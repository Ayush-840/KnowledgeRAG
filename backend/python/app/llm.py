"""LLM generation client with defensive, citation-enforcing prompting.

Supports multiple providers via LLM_PROVIDER env var:
  - "openrouter" (default) — uses OPENROUTER_API_KEY
  - "nvidia"               — uses NVIDIA_API_KEY + NVIDIA NIM endpoint (free tier)

Both providers support multiple comma-separated API keys with automatic
rotation on 401/403/429 failures.  Rotation events are logged to
key-rotations.jsonl in QUERY_LOG_DIR.

generate_answer() returns (answer, usage, latency_ms). The system prompt
constrains the model to the provided context, requires [n] citation markers and
a structured synthesized answer (summary -> takeaways -> citations), which the
caller then verifies against the actually-retrieved chunks (verify_citations)
so fabricated references never reach the UI.
"""

import json
import os
import re
import ssl
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
NVIDIA_URL     = "https://integrate.api.nvidia.com/v1/chat/completions"

# Provider routing
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()

# --- Key rotation log ----------------------------------------------------
_KEY_LOG_DIR = Path(os.getenv("QUERY_LOG_DIR", "./logs"))
_KEY_LOG_PATH = _KEY_LOG_DIR / "key-rotations.jsonl"

def _log_key_event(provider: str, event: str, key_idx: int,
                   total: int, key_hint: str | None,
                   error_code: int | None = None) -> None:
    """Append a structured key rotation event to key-rotations.jsonl."""
    try:
        _KEY_LOG_DIR.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "event": event,
            "key_index": key_idx,
            "total_keys": total,
        }
        if key_hint:
            record["key_hint"] = key_hint
        if error_code is not None:
            record["http_status"] = error_code
        with open(_KEY_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        pass  # logging must never break the request


# --- Generic key rotator --------------------------------------------------

class _KeyRotator:
    """Round-robin rotator for a comma-separated list of API keys.

    Reads from *env_var* at import time.  ``current()`` returns the active
    key; ``rotate()`` advances to the next one (with optional error logging).
    """

    def __init__(self, provider: str, env_var: str, hint: str = ""):
        self.provider = provider
        self.env_var = env_var
        self._hint = hint  # shown in error messages when no keys are set
        raw = os.getenv(env_var, "")
        self.keys: list[str] = [k.strip() for k in raw.split(",") if k.strip()]
        self._idx = 0
        if self.keys:
            _log_key_event(provider, "startup", self._idx, len(self.keys),
                           self._hint_fn(self._idx))

    def _hint_fn(self, idx: int) -> str:
        return self.keys[idx][:15] + "…" if self.keys else None

    @property
    def available(self) -> bool:
        return bool(self.keys)

    def current(self) -> str:
        if not self.keys:
            raise RuntimeError(f"{self.env_var} not set{self._hint}")
        return self.keys[self._idx % len(self.keys)]

    def rotate(self, error_code: int | None = None) -> None:
        if not self.keys:
            return
        self._idx = (self._idx + 1) % len(self.keys)
        _log_key_event(self.provider, "rotate", self._idx, len(self.keys),
                       self._hint_fn(self._idx), error_code)

_nvidia_rotator = _KeyRotator("nvidia", "NVIDIA_API_KEY",
                               " — get a free key at https://build.nvidia.com")
_openrouter_rotator = _KeyRotator("openrouter", "OPENROUTER_API_KEY",
                                   " — get a key at https://openrouter.ai/keys")
# ------------------------------------------------------------------------


def _ssl_context():
    """HTTPS context using certifi's CA bundle when available (macOS python.org
    builds often ship without a default CA store, which breaks urllib calls)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001 - fall back to the interpreter default
        return ssl.create_default_context()


def _active_rotator() -> _KeyRotator:
    return _nvidia_rotator if LLM_PROVIDER == "nvidia" else _openrouter_rotator


def _provider_config():
    """Return (url, api_key) for the active provider."""
    rotator = _active_rotator()
    if LLM_PROVIDER == "nvidia":
        return NVIDIA_URL, rotator.current()
    return OPENROUTER_URL, rotator.current()


GENERATION_MODEL = os.getenv(
    "GENERATION_MODEL",
    "meta/llama-3.3-70b-instruct" if LLM_PROVIDER == "nvidia" else "openai/gpt-4o"
)
GENERATION_MAX_TOKENS = int(os.getenv("GENERATION_MAX_TOKENS", "600"))

CITE_RE = re.compile(r"\[(\d+)\]")


def llm_available() -> bool:
    """True when the key for the configured provider is present."""
    return _active_rotator().available


def _build_request(url: str, api_key: str, payload: dict) -> urllib.request.Request:
    """Build an authenticated POST request for the chat endpoint."""
    return urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )


def _chat(messages: list, temperature: float = 0.2, max_tokens: int = GENERATION_MAX_TOKENS):
    url, api_key = _provider_config()
    model = GENERATION_MODEL
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # Rotate through all keys on auth / rate-limit failures.
    rotator = _active_rotator()
    max_key_attempts = len(rotator.keys) if rotator.keys else 1

    last_exc: Exception | None = None
    for _key_attempt in range(max_key_attempts):
        req = _build_request(url, api_key, payload)
        try:
            t0 = time.perf_counter()
            data = _urlopen_with_retry(req)
            latency_ms = (time.perf_counter() - t0) * 1000
            answer = data["choices"][0]["message"]["content"].strip()
            usage = data.get("usage", {}) or {}
            return answer, usage, round(latency_ms, 2)
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code in (401, 403, 429):
                rotator.rotate(error_code=exc.code)
                url, api_key = _provider_config()
                continue
            raise
    raise last_exc  # type: ignore[misc]


def _urlopen_with_retry(req, attempts: int = 4, base_delay: float = 2.0):
    """POST with retry/backoff on transient HTTP errors (429 rate limit, 5xx)."""
    import urllib.error

    last = None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=120, context=_ssl_context()) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429 or e.code >= 500:
                if i < attempts - 1:
                    time.sleep(base_delay * (2 ** i))
                    continue
            raise
    raise last


def _generate_extractive_fallback(query: str, context_chunks: list, error_detail: str):
    """Fallback generator when external LLM API fails (e.g. HTTP 403/402/429).
    Creates a clean, grounded synthesis from top retrieved chunks with working [n] citations.
    """
    if not context_chunks:
        return "I couldn't find relevant information in the uploaded documents.", {}, 0.0

    lines = ["Here is what I found in your uploaded document(s):\n"]
    for i, chunk in enumerate(context_chunks[:3]):
        text = chunk.get("text", "").strip()
        if len(text) > 400:
            text = text[:400].rsplit(" ", 1)[0] + "..."
        label = chunk.get("title") or chunk.get("filename") or "document"
        page = chunk.get("page_number")
        page_str = f" (Page {page})" if page else ""
        lines.append(f"• From **{label}**{page_str} [{i + 1}]:\n  \"{text}\"")

    answer = "\n\n".join(lines)
    return answer, {"fallback": True, "error": error_detail}, 10.0


# Defensive, citation-enforcing generation prompt. Requires a synthesized answer
# (never raw quote dumps), human-readable document titles, inline [n] citations,
# and an explicit "what's missing" statement for low-coverage questions — the
# eval harness's faithfulness / unanswerable-query slices depend on it.
GENERATION_SYSTEM_PROMPT = (
    "You are Knowledge RAG, an intelligent document analysis assistant. "
    "Your role is to read the retrieved context chunks and synthesize a clear, "
    "comprehensive, and cohesive answer to the user's query.\n\n"
    "CRITICAL INSTRUCTIONS:\n"
    "1. Synthesize, Do Not Quote Dump:\n"
    "   - Provide a well-structured summary of the core topic.\n"
    "   - Do NOT output raw chunk listings, unformatted extracts, or isolated "
    "quotes unless the user specifically requests them.\n"
    "   - Group related concepts under clear bold headings and bullet points.\n"
    "2. Document & Metadata Formatting:\n"
    "   - Always reference documents using their original human-readable title "
    "(given as Source in the CONTEXT block), never raw filenames, hashes, or "
    "storage keys.\n"
    "   - Place numerical citations inline (e.g., [1], [2]) directly after the "
    "facts they support, matching the CONTEXT numbering.\n"
    "3. Handling Low-Relevance Chunks:\n"
    "   - Ignore irrelevant noise or out-of-context text retrieved from the "
    "documents.\n"
    "   - If the CONTEXT lacks enough information to answer fully, state "
    "clearly what information is available and what is missing. Never invent "
    "facts or references. If nothing relevant was retrieved, reply exactly: "
    "\"I couldn't find that in the uploaded documents.\"\n\n"
    "RESPONSE FORMAT:\n"
    "- Executive Summary / Core Answer: 2-3 sentences with the primary takeaway.\n"
    "- Key Takeaways & Concepts: a bulleted breakdown of the key points.\n"
    "- Citation References: mapped directly to the original document titles and "
    "pages."
)


def _format_context_chunk(index: int, chunk: dict) -> str:
    """Render one context chunk with its resolved human-readable source label,
    so the model can cite real document titles instead of storage keys."""
    title = chunk.get("title") or chunk.get("filename") or "Document"
    header = f'Source: "{title}"'
    page = chunk.get("page_number")
    if page:
        header += f", page {page}"
    return f"[{index}] ({header})\n{chunk.get('text', '')}"


def generate_answer(query: str, context_chunks: list):
    """Generate a grounded answer with [n] citations.

    context_chunks: list of dicts with at least {"text": ...}, plus optional
    {"title", "filename", "page_number"} used to label sources for the model.
    Returns (answer, usage, latency_ms).
    """
    context = "\n\n".join(
        _format_context_chunk(i + 1, c) for i, c in enumerate(context_chunks)
    )
    user = (
        f"CONTEXT:\n{context}\n\nQUESTION: {query}\n\n"
        "Answer using only the CONTEXT above, following the RESPONSE FORMAT."
    )
    try:
        return _chat(
            [
                {"role": "system", "content": GENERATION_SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
    except Exception as e:
        return _generate_extractive_fallback(query, context_chunks, str(e))


def summarize_title(query: str) -> str:
    """Short chat title from a query: an LLM summary when a key is configured,
    else a deterministic heuristic. The LLM call is tiny (max 16 tokens) and
    failures degrade silently to the heuristic."""
    if llm_available():
        try:
            answer, _usage, _ms = _chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "You generate short chat titles. Reply with a title of "
                            "6 words or fewer capturing the topic of the user's "
                            "question. No quotes, no markdown, no explanation."
                        ),
                    },
                    {"role": "user", "content": query},
                ],
                temperature=0.0,
                max_tokens=16,
            )
            title = answer.strip().strip('"').strip()
            if 2 <= len(title) <= 60 and "\n" not in title:
                return title
        except Exception:  # noqa: BLE001 - fall back to the heuristic
            pass
    return _heuristic_title(query)


def _heuristic_title(query: str) -> str:
    """Deterministic fallback: first ~8 words, punctuation cleaned, capped at 48 chars."""
    t = re.sub(r"\s+", " ", query).strip()
    t = re.sub(r"^[^a-zA-Z0-9]+|[?!.]+$", "", t).strip()
    title = " ".join(t.split()[:8]).strip()
    if len(title) > 48:
        title = title[:48].rsplit(" ", 1)[0] + "…"
    return title or "Untitled chat"


def verify_citations(answer: str, context_chunks: list):
    """Cross-check [n] markers in the answer against the retrieved chunks.

    Invalid/out-of-range markers are removed. Returns
    (clean_answer, citations) where citations is a deduplicated, marker-sorted
    list of {"marker", "id", "filename", "page_number", "text", "scores",
    "confidence"}.
    """
    citations = []
    seen = set()

    def repl(m):
        n = int(m.group(1))
        if 1 <= n <= len(context_chunks):
            c = context_chunks[n - 1]
            if n not in seen:
                seen.add(n)
                citations.append(
                    {
                        "marker": n,
                        "id": c["id"],
                        "filename": c["filename"],
                        "title": c.get("title"),
                        "page_number": c.get("page_number", 0),
                        "text": c["text"],
                        "scores": c.get("scores"),
                        "confidence": c.get("confidence"),
                    }
                )
            return f"[{n}]"
        return ""

    clean = CITE_RE.sub(repl, answer)
    citations.sort(key=lambda c: c["marker"])
    return clean, citations
