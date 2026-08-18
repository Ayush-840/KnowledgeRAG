"""LLM-as-judge helpers for the eval harness.

Qualitative RAGAS-style metrics (faithfulness, answer relevance) are computed
with an LLM judge. The provider is selected by LLM_PROVIDER (mirrors
app/llm.py):

  - "nvidia" (default when NVIDIA_API_KEY is set) — NVIDIA NIM hosted models
  - "openrouter" — OpenRouter

The harness runs without qualitative metrics if no API key is present.

Generation reuses the app's structured synthesis prompt (app.llm), and
check_structure() is a cheap, no-LLM pre-check of the response contract
(three sections present, body [n] markers resolve to the citation section).
"""

import json
import os
import re
import ssl
import urllib.request

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
NVIDIA_URL     = "https://integrate.api.nvidia.com/v1/chat/completions"

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
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set")
    return OPENROUTER_URL, key


_DEFAULT_MODEL = "meta/llama-3.3-70b-instruct" if LLM_PROVIDER == "nvidia" else "openai/gpt-4o"
GENERATION_MODEL = os.getenv("EVAL_GENERATION_MODEL", _DEFAULT_MODEL)
JUDGE_MODEL = os.getenv("EVAL_JUDGE_MODEL", _DEFAULT_MODEL)


def llm_available() -> bool:
    """True when the key for the configured provider is present.
    (openrouter -> OPENROUTER_API_KEY, nvidia -> NVIDIA_API_KEY)
    """
    if LLM_PROVIDER == "nvidia":
        return bool(os.getenv("NVIDIA_API_KEY"))
    return bool(os.getenv("OPENROUTER_API_KEY"))


def _post_chat(messages: list, model: str, temperature: float = 0.0, max_tokens: int = 512) -> str:
    url, api_key = _provider_config()
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
    data = _urlopen_with_retry(req)
    return data["choices"][0]["message"]["content"].strip()


def _urlopen_with_retry(req, attempts: int = 4, base_delay: float = 2.0):
    """POST with retry/backoff on transient HTTP errors (429 rate limit, 5xx)."""
    import time
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


def _parse_score(text: str) -> float:
    """Extract a 0..1 score from a judge response (handles '0.85', 'Score: 0.85/1.0', ...)."""
    match = re.search(r"0(?:[.][0-9]+)?|1(?:[.]0+)?", text)
    if not match:
        return None
    score = float(match.group(0))
    return max(0.0, min(1.0, score))


CITE_RE = re.compile(r"\[(\d+)\]")


def _as_chunk(c):
    """Accept either a plain text string or a chunk dict (as produced by the
    retrieval layer), so callers can pass richer chunks for source labeling."""
    if isinstance(c, dict):
        return c
    return {"text": c}


def generate_answer(question: str, context_chunks: list) -> str:
    """Generate a document-grounded answer with the same defensive, structured
    synthesis prompt the app uses (imported from app.llm), so eval answers obey
    the same response contract that check_structure() validates."""
    from app.llm import GENERATION_SYSTEM_PROMPT, _format_context_chunk

    chunks = [_as_chunk(c) for c in context_chunks]
    context = "\n\n".join(
        _format_context_chunk(i + 1, c) for i, c in enumerate(chunks)
    )
    user = (
        f"CONTEXT:\n{context}\n\nQUESTION: {question}\n\n"
        "Answer using only the CONTEXT above, following the RESPONSE FORMAT."
    )
    return _post_chat(
        [{"role": "system", "content": GENERATION_SYSTEM_PROMPT}, {"role": "user", "content": user}],
        GENERATION_MODEL,
        temperature=0.2,
    )


def check_structure(answer: str, n_chunks: int):
    """Fast, no-LLM pre-check of the response contract.

    Verifies (1) all three response sections are present — Executive Summary /
    Core Answer, Key Takeaways & Concepts, Citation References — and (2) every
    [n] marker used in the body resolves to an entry in the Citation References
    section and stays within the retrieved context size.

    Returns (ok: bool, issues: list[str]).
    """
    issues = []
    if not answer or not answer.strip():
        return False, ["answer is empty"]

    lines = answer.splitlines()
    header_re = re.compile(
        r"^\s*(?:#+\s*)?(?:\*\*)?"
        r"(executive summary|core answer|key takeaways|key points|"
        r"citation references|citations|references)"
        r"(?:\*\*)?:?(\s|$)",
        re.IGNORECASE,
    )

    def find_header(*patterns):
        for i, line in enumerate(lines):
            t = line.strip()
            if header_re.match(t) and any(p.search(t) for p in patterns):
                return i
        return None

    sum_idx = find_header(re.compile(r"executive summary|core answer", re.IGNORECASE))
    take_idx = find_header(re.compile(r"key takeaways|key points", re.IGNORECASE))
    cite_idx = find_header(re.compile(r"citation references|citations|references", re.IGNORECASE))

    if sum_idx is None:
        issues.append("missing Executive Summary / Core Answer section")
    if take_idx is None:
        issues.append("missing Key Takeaways & Concepts section")
    if cite_idx is None:
        issues.append("missing Citation References section")

    cite_start = cite_idx if cite_idx is not None else len(lines)
    body = "\n".join(lines[:cite_start])
    cite_section = "\n".join(lines[cite_start:]) if cite_idx is not None else ""

    body_markers = sorted({int(m) for m in CITE_RE.findall(body)})
    cite_markers = {int(m) for m in CITE_RE.findall(cite_section)}

    for n in body_markers:
        if n < 1 or n > n_chunks:
            issues.append(f"marker [{n}] exceeds context size ({n_chunks} chunks)")
        elif n not in cite_markers:
            issues.append(f"marker [{n}] used in body but missing from Citation References")

    return not issues, issues


def judge_faithfulness(question: str, answer: str, context_chunks: list) -> float:
    """Score how well the answer's claims are grounded in the retrieved context (0..1)."""
    context = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(context_chunks))
    prompt = (
        "You are evaluating whether an answer is grounded in its context.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        f"ANSWER:\n{answer}\n\n"
        "Check every factual claim in the ANSWER: is it supported by the CONTEXT, or does "
        "the answer add unsupported/contradictory claims? Ignore style. "
        "Return ONLY a single number between 0.0 and 1.0, where 1.0 means every claim is "
        "fully supported by the context and 0.0 means none are."
    )
    return _parse_score(
        _post_chat([{"role": "user", "content": prompt}], JUDGE_MODEL, temperature=0.0)
    )


def judge_answer_relevance(question: str, answer: str) -> float:
    """Score how directly the answer addresses the question (0..1)."""
    prompt = (
        "You are evaluating how relevant an answer is to its question.\n\n"
        f"QUESTION: {question}\n\n"
        f"ANSWER:\n{answer}\n\n"
        "Does the ANSWER directly and completely address the QUESTION? Penalize answers "
        "that are off-topic or dodge the question. Return ONLY a single number between "
        "0.0 and 1.0, where 1.0 means perfectly relevant and 0.0 means completely "
        "irrelevant."
    )
    return _parse_score(
        _post_chat([{"role": "user", "content": prompt}], JUDGE_MODEL, temperature=0.0)
    )


# ---- Unanswerable query handling ----

# Phrases that indicate the system correctly declined to answer
_DECLINE_PATTERNS = re.compile(
    r"couldn't find|cannot find|not found|not in the|not available|"
    r"no relevant|no information|don't have|does(?:n't| not) contain|"
    r"unable to answer|not present in|no data|no mention|"
    r"i don't have enough|insufficient information|"
    r"the uploaded documents don't|the context (?:does|doesn't)(?: not)? contain",
    re.IGNORECASE,
)


def check_decline(answer: str) -> bool:
    """Cheap, no-LLM regex check for whether an answer correctly declines.
    Returns True if the answer contains phrases indicating the system couldn't
    find the information in the uploaded documents."""
    if not answer or not answer.strip():
        return False
    return bool(_DECLINE_PATTERNS.search(answer))


def judge_declined_correctly(question: str, answer: str) -> float:
    """For unanswerable queries: score whether the system correctly declined
    to answer rather than fabricating a response.

    Returns 1.0 if the answer correctly declines, 0.0 if it fabricates.
    Uses a cheap regex pre-check first; falls back to LLM judge for ambiguous cases.
    """
    # Fast path: regex detects clear decline phrases
    if check_decline(answer):
        return 1.0
    # Fast path: empty or very short answer that doesn't fabricate
    if not answer or len(answer.strip()) < 20:
        return 0.5  # uncertain — too short to tell
    # LLM judge for ambiguous cases
    prompt = (
        "You are evaluating whether an answer correctly declines to answer a question "
        "when the information is not available.\n\n"
        f"QUESTION: {question}\n\n"
        f"ANSWER:\n{answer}\n\n"
        "The QUESTION asks about information that is NOT in the provided documents. "
        "The correct behavior is to DECLINE to answer (e.g., 'I couldn\'t find that in "
        "the uploaded documents' or 'The context doesn\'t contain this information').\n\n"
        "Does the ANSWER correctly decline, or does it fabricate/hallucinate an answer?\n"
        "Return ONLY a single number: 1.0 if it correctly declines, 0.0 if it fabricates."
    )
    return _parse_score(
        _post_chat([{"role": "user", "content": prompt}], JUDGE_MODEL, temperature=0.0)
    )
