"""LLM-as-judge helpers for the eval harness.

Qualitative RAGAS-style metrics (faithfulness, answer relevance) are computed
with an LLM judge. The provider is selected by LLM_PROVIDER (mirrors
app/llm.py):

  - "nvidia" (default when NVIDIA_API_KEY is set) — NVIDIA NIM hosted models
  - "openrouter" — OpenRouter

The harness runs without qualitative metrics if no API key is present.
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


def generate_answer(question: str, context_chunks: list) -> str:
    """Generate a document-grounded answer with defensive, citation-enforcing prompting."""
    context = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(context_chunks))
    system = (
        "You are a document-grounded Q&A assistant. Answer ONLY from the provided "
        "context. If the context does not contain the answer, say so explicitly. "
        "Cite sources inline with [n] markers matching the context list."
    )
    user = f"CONTEXT:\n{context}\n\nQUESTION: {question}\n\nAnswer concisely with [n] citations."
    return _post_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        GENERATION_MODEL,
        temperature=0.2,
    )


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
