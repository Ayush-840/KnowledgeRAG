"""LLM generation client with defensive, citation-enforcing prompting.

Supports multiple providers via LLM_PROVIDER env var:
  - "openrouter" (default) — uses OPENROUTER_API_KEY
  - "nvidia"               — uses NVIDIA_API_KEY + NVIDIA NIM endpoint (free tier)

generate_answer() returns (answer, usage, latency_ms). The system prompt
constrains the model to the provided context and requires [n] citation markers,
which the caller then verifies against the actually-retrieved chunks
(verify_citations) so fabricated references never reach the UI.
"""

import json
import os
import re
import ssl
import time
import urllib.request

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
NVIDIA_URL     = "https://integrate.api.nvidia.com/v1/chat/completions"

# Provider routing
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").lower()


def _ssl_context():
    """HTTPS context using certifi's CA bundle when available (macOS python.org
    builds often ship without a default CA store, which breaks urllib calls)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001 - fall back to the interpreter default
        return ssl.create_default_context()


def _provider_config():
    """Return (url, api_key) for the active provider."""
    if LLM_PROVIDER == "nvidia":
        key = os.getenv("NVIDIA_API_KEY", "")
        if not key:
            raise RuntimeError("NVIDIA_API_KEY not set — get a free key at https://build.nvidia.com")
        return NVIDIA_URL, key
    # default: openrouter
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    return OPENROUTER_URL, key


GENERATION_MODEL = os.getenv(
    "GENERATION_MODEL",
    "nvidia/llama-3.1-nemotron-70b-instruct" if LLM_PROVIDER == "nvidia" else "openai/gpt-4o"
)
GENERATION_MAX_TOKENS = int(os.getenv("GENERATION_MAX_TOKENS", "600"))

CITE_RE = re.compile(r"\[(\d+)\]")


def llm_available() -> bool:
    provider = os.getenv("LLM_PROVIDER", "openrouter").lower()
    if provider == "nvidia":
        return bool(os.getenv("NVIDIA_API_KEY"))
    return bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("NVIDIA_API_KEY"))


def _chat(messages: list, temperature: float = 0.2, max_tokens: int = GENERATION_MAX_TOKENS):
    url, api_key = _provider_config()
    model = os.getenv(
        "GENERATION_MODEL",
        "meta/llama-3.3-70b-instruct" if LLM_PROVIDER == "nvidia" else "openai/gpt-4o"
    )
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    t0 = time.perf_counter()
    data = _urlopen_with_retry(req)
    latency_ms = (time.perf_counter() - t0) * 1000
    answer = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {}) or {}
    return answer, usage, round(latency_ms, 2)


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
        filename = chunk.get("filename", "document")
        page = chunk.get("page_number")
        page_str = f" (Page {page})" if page else ""
        lines.append(f"• From **{filename}**{page_str} [{i + 1}]:\n  \"{text}\"")

    answer = "\n\n".join(lines)
    return answer, {"fallback": True, "error": error_detail}, 10.0


def generate_answer(query: str, context_chunks: list):
    """Generate a grounded answer with [n] citations.

    context_chunks: list of dicts with at least {"text": ...}. Returns
    (answer, usage, latency_ms).
    """
    context = "\n\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(context_chunks))
    system = (
        "You are a document-grounded Q&A assistant for Knowledge RAG. "
        "Answer ONLY from the provided CONTEXT. Cite the source of each claim "
        "inline with [n] markers matching the context list. Do not invent "
        "references or facts. If the CONTEXT does not contain the answer, reply "
        "exactly: \"I couldn't find that in the uploaded documents.\""
    )
    user = (
        f"CONTEXT:\n{context}\n\nQUESTION: {query}\n\n"
        "Answer concisely with [n] citations."
    )
    try:
        return _chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
        )
    except Exception as e:
        return _generate_extractive_fallback(query, context_chunks, str(e))


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
