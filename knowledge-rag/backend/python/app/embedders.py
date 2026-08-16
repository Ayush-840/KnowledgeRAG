"""Embedding model interface.

Call sites use get_embedder().embed(texts) and never touch the concrete
implementation, so the model can be swapped via env without rippling through
retrieval/ingestion code:

  EMBEDDER=minilm   (default) all-MiniLM-L6-v2, local via sentence-transformers
  EMBEDDER=openai   text-embedding-3-small (or OPENAI_EMBEDDING_MODEL) via API

Note: sessions are indexed with whatever embedder is configured at ingest time;
mixing embedders within one session's collection would corrupt the vector space.
"""

import json
import os
import ssl
import urllib.request

import numpy as np


def _ssl_context():
    """HTTPS context using certifi's CA bundle when available (macOS python.org
    builds often ship without a default CA store, which breaks urllib calls)."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001 - fall back to the interpreter default
        return ssl.create_default_context()

EMBEDDER_NAME = os.getenv("EMBEDDER", "minilm").lower()
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_EMBEDDINGS_URL = os.getenv("OPENAI_EMBEDDINGS_URL", "https://api.openai.com/v1/embeddings")


class Embedder:
    name = "base"

    def embed(self, texts):
        raise NotImplementedError


class MiniLMEmbedder(Embedder):
    name = "all-MiniLM-L6-v2"

    def __init__(self):
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(self.name)

    def embed(self, texts):
        return self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True)


class OpenAIEmbedder(Embedder):
    def __init__(self):
        self.name = OPENAI_EMBEDDING_MODEL
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY not set — required for EMBEDDER=openai")

    def embed(self, texts, batch_size=64):
        vectors = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            payload = {"model": self.name, "input": batch}
            req = urllib.request.Request(
                OPENAI_EMBEDDINGS_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=120, context=_ssl_context()) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # OpenAI returns embeddings in request order
            vectors.extend(item["embedding"] for item in data["data"])
        return np.array(vectors, dtype="float32")


_embedder = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        if EMBEDDER_NAME == "minilm":
            _embedder = MiniLMEmbedder()
        elif EMBEDDER_NAME == "openai":
            _embedder = OpenAIEmbedder()
        else:
            raise ValueError(f"Unknown EMBEDDER: {EMBEDDER_NAME} (expected 'minilm' or 'openai')")
    return _embedder
