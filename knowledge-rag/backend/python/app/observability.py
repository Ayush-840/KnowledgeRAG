"""Structured per-query logging (JSONL).

Every search writes one JSON line capturing: query, retrieved chunk ids +
stage-wise scores, reranked order, citations, and latency breakdown. Both the
eval harness and the future metrics dashboard read from these logs.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

QUERY_LOG_DIR = Path(os.getenv("QUERY_LOG_DIR", "./logs"))
QUERY_LOG_PATH = QUERY_LOG_DIR / "queries.jsonl"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_query(record: dict) -> None:
    """Append a structured per-query record as one JSON line."""
    try:
        QUERY_LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(QUERY_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=str) + "\n")
    except OSError as e:  # logging must never break the request
        print(f"⚠️  Could not write query log: {e}")
