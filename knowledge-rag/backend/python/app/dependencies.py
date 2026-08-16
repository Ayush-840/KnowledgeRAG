import os
import json
from pathlib import Path
from typing import Dict, Any
from chromadb.config import Settings
import chromadb
from rank_bm25 import BM25Okapi

# Directory to store persistent index data per session
BASE_PERSISTENCE_DIR = Path(os.getenv("CHROMA_PERSISTENCE_DIR", "./chroma_data"))
BASE_PERSISTENCE_DIR.mkdir(parents=True, exist_ok=True)

# In‑memory registry for active session indexes
SESSION_REGISTRY: Dict[str, Dict[str, Any]] = {}

def get_session_vectors(session_id: str):
    """Return the Chroma collection for a session, creating it if necessary."""
    if session_id not in SESSION_REGISTRY:
        # Load or create persistent collection
        client = chromadb.PersistentClient(path=str(BASE_PERSISTENCE_DIR / session_id))
        # hnsw:space=cosine makes Chroma return cosine distances, so the
        # dense_similarity = 1 - distance reported by retrieval.py is an actual
        # cosine similarity (Chroma's default space is L2, which would make the
        # label a lie). Only affects collections created from here on; existing
        # persisted collections keep their original space.
        collection = client.get_or_create_collection(
            name=session_id,
            metadata={"session_id": session_id, "hnsw:space": "cosine"},
        )
        # Load BM25 index from disk if exists
        bm25_path = BASE_PERSISTENCE_DIR / session_id / "bm25.json"
        bm25 = None
        bm25_ids = None
        if bm25_path.exists():
            with open(bm25_path, "r", encoding="utf-8") as f:
                bm25_data = json.load(f)
            bm25 = BM25Okapi(bm25_data["corpus"])
            bm25_ids = bm25_data.get("ids")
        SESSION_REGISTRY[session_id] = {
            "client": client,
            "collection": collection,
            "bm25": bm25,
            "bm25_ids": bm25_ids,
        }
    return SESSION_REGISTRY[session_id]

def persist_bm25(session_id: str, tokenized_corpus: list, ids: list = None):
    """Persist BM25 tokenized corpus (and matching Chroma ids) to disk for later reload."""
    bm25_dir = BASE_PERSISTENCE_DIR / session_id
    bm25_dir.mkdir(parents=True, exist_ok=True)
    bm25_path = bm25_dir / "bm25.json"
    payload = {"corpus": tokenized_corpus}
    if ids is not None:
        payload["ids"] = ids
    with open(bm25_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
