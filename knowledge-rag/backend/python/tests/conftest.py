"""Pytest configuration for the Knowledge RAG QA suite.

The suite must be hermetic: it never touches the network, never loads the
MiniLM embedder or the ~1.1 GB reranker, and uses temp dirs for Chroma
persistence and query logs. Env vars are set HERE (module import time) because
app modules read them at import (CHROMA_PERSISTENCE_DIR, QUERY_LOG_DIR,
RERANKER_ENABLED, retrieval knobs).
"""

import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="kr-qa-")

os.environ["CHROMA_PERSISTENCE_DIR"] = os.path.join(_TMP, "chroma")
os.environ["QUERY_LOG_DIR"] = os.path.join(_TMP, "logs")
os.environ["RERANKER_ENABLED"] = "false"          # never download bge-reranker in tests
os.environ["RRF_K"] = "60"
os.environ["RETRIEVE_CANDIDATES"] = "20"
os.environ["RERANK_TOP_K"] = "5"
os.environ["EMBEDDER"] = "minilm"                 # value irrelevant; embedder is stubbed below

import hashlib  # noqa: E402

import numpy as np  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class StubEmbedder:
    """Deterministic fake embedder (384-dim, seeded per text) so no model loads."""

    name = "stub-embedder"

    def embed(self, texts):
        vectors = []
        for t in texts:
            seed = int(hashlib.md5(t.encode("utf-8")).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)
            v = rng.normal(size=384).astype("float32")
            v /= float(np.linalg.norm(v) + 1e-9)
            vectors.append(v)
        return np.array(vectors, dtype="float32")


@pytest.fixture(autouse=True)
def _stub_embedder(monkeypatch):
    """Replace the real embedder factory in app.utils (ingest path)."""
    from app import utils

    monkeypatch.setattr(utils, "get_embedder", lambda: StubEmbedder())


@pytest.fixture()
def client():
    from app.main import app

    return TestClient(app)
