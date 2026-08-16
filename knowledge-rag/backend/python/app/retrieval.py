"""Hybrid retrieval pipeline: dense (Chroma) + sparse (BM25) -> RRF fusion -> cross-encoder rerank.

Scores from each stage are kept separate and labeled, per the Phase 1 spec:
retrieval-stage scores (dense cosine similarity, raw BM25, RRF fusion score) and
the reranker's cross-encoder relevance score are never blended into one number.

Each call returns a dict with results, candidate counts, a per-stage latency
breakdown (ms), the fused candidate pool with stage scores, and the final
reranked id order — everything the observability layer logs per query.
"""

import os
import time
from typing import Dict, List, Optional

# ---- Tunable knobs (env-configurable) ----
RRF_K = int(os.getenv("RRF_K", "60"))                      # RRF constant
RETRIEVE_CANDIDATES = int(os.getenv("RETRIEVE_CANDIDATES", "20"))  # wide retrieval pool
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "5"))         # narrow top-k for generation
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
RERANKER_ENABLED = os.getenv("RERANKER_ENABLED", "true").lower() in ("1", "true", "yes")

_reranker = None
_reranker_error: Optional[Exception] = None


def get_reranker():
    """Lazily load the cross-encoder reranker once. Returns None if disabled or unavailable."""
    global _reranker, _reranker_error
    if not RERANKER_ENABLED:
        return None
    if _reranker is None and _reranker_error is None:
        try:
            from sentence_transformers import CrossEncoder

            _reranker = CrossEncoder(RERANKER_MODEL)
        except Exception as e:  # noqa: BLE001 - any failure degrades gracefully
            _reranker_error = e
            print(
                f"⚠️  Reranker unavailable ({RERANKER_MODEL}): {e} — "
                "falling back to RRF ordering."
            )
    return _reranker


def reciprocal_rank_fusion(ranked_lists: List[List[str]], k: int = RRF_K) -> Dict[str, float]:
    """Reciprocal Rank Fusion over ranked lists of doc ids.

    RRF score = sum over lists of 1 / (k + rank), with rank 1-indexed.
    This merges dense and sparse rankings without needing calibrated scores.
    """
    fused: Dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked, start=1):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (k + rank)
    return fused


def hybrid_search(
    collection,
    bm25,
    query: str,
    bm25_ids: Optional[List[str]] = None,
    candidates: Optional[int] = None,
    top_k: Optional[int] = None,
) -> dict:
    """Run hybrid retrieval for a query.

    Returns a dict:
      - results: top-k chunks after reranking, each with id, text, filename,
        page_number, chunk_strategy and labeled retrieval_scores
      - candidates_retrieved: size of the fused pool handed to the reranker
      - candidates_sent_to_llm: top-k after reranking (what generation would see)
      - latency_ms: {dense, bm25, fusion, rerank, total} in milliseconds
      - fused_pool: [{id, dense_similarity, bm25, rrf}] for the wide pool
      - reranked_ids: final ordered chunk ids
    """
    t0 = time.perf_counter()
    candidates = candidates or RETRIEVE_CANDIDATES
    top_k = top_k or RERANK_TOP_K

    # ---- Wide dense retrieval ----
    t_dense = time.perf_counter()
    dense = collection.query(
        query_texts=[query],
        n_results=candidates,
        include=["documents", "metadatas", "distances"],  # ids are always returned by Chroma
    )
    dense_ids: List[str] = list(dense["ids"][0])
    dense_docs: List[str] = list(dense["documents"][0])
    dense_metas: List[dict] = list(dense["metadatas"][0])
    dense_dists: List[float] = list(dense["distances"][0])
    dense_ms = (time.perf_counter() - t_dense) * 1000

    # ---- Wide sparse retrieval ----
    t_bm25 = time.perf_counter()
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)
    top_bm25_idx = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )[:candidates]
    bm25_ms = (time.perf_counter() - t_bm25) * 1000

    # Align BM25 corpus positions with Chroma doc ids.
    # Prefer the ids persisted alongside the BM25 corpus; fall back to collection order.
    if bm25_ids is None:
        bm25_ids = collection.get(include=[])["ids"]
    id_to_pos: Dict[str, int] = {doc_id: i for i, doc_id in enumerate(bm25_ids)}

    # ---- RRF fusion ----
    t_fuse = time.perf_counter()
    bm25_ranked = [bm25_ids[i] for i in top_bm25_idx]
    rrf_scores = reciprocal_rank_fusion([dense_ids, bm25_ranked])

    # Union of candidate ids from both retrievers
    candidate_ids: List[str] = list(dict.fromkeys([*dense_ids, *bm25_ranked]))

    # Fetch text/metadata for any doc that only one retriever surfaced
    fetched = collection.get(ids=candidate_ids, include=["documents", "metadatas"])
    id_to_doc = {
        doc_id: (text, meta)
        for doc_id, text, meta in zip(
            fetched["ids"], fetched["documents"], fetched["metadatas"]
        )
    }

    # Raw per-source scores (kept separate and labeled, never blended)
    dense_by_id = {doc_id: 1.0 - dist for doc_id, dist in zip(dense_ids, dense_dists)}
    bm25_by_id = {
        bm25_ids[i]: float(bm25_scores[i]) for i in top_bm25_idx if i < len(bm25_ids)
    }

    # Fused pool (wide), ordered by RRF
    fused_ranked = sorted(candidate_ids, key=lambda i: rrf_scores[i], reverse=True)[:candidates]
    fused_ms = (time.perf_counter() - t_fuse) * 1000

    # ---- Narrow reranking (cross-encoder) ----
    t_rerank = time.perf_counter()
    rerank_scores: Dict[str, float] = {}
    reranker = get_reranker()
    if reranker is not None and fused_ranked:
        pairs = [[query, id_to_doc[i][0]] for i in fused_ranked]
        try:
            scores = reranker.predict(pairs)
            rerank_scores = {i: float(s) for i, s in zip(fused_ranked, scores)}
            final_ranked = sorted(fused_ranked, key=lambda i: rerank_scores[i], reverse=True)[:top_k]
        except Exception as e:  # noqa: BLE001 - degrade to RRF order
            print(f"⚠️  Rerank failed: {e} — using RRF order")
            final_ranked = fused_ranked[:top_k]
    else:
        final_ranked = fused_ranked[:top_k]
    rerank_ms = (time.perf_counter() - t_rerank) * 1000

    # ---- Build response records ----
    results = []
    for doc_id in final_ranked:
        text, meta = id_to_doc[doc_id]
        results.append(
            {
                "id": doc_id,
                "text": text,
                "filename": meta.get("filename", ""),
                "page_number": meta.get("page_number", 0),
                "chunk_strategy": meta.get("chunk_strategy", "fixed"),
                "retrieval_scores": {
                    "dense_similarity": round(dense_by_id[doc_id], 4) if doc_id in dense_by_id else None,
                    "bm25": round(bm25_by_id[doc_id], 4) if doc_id in bm25_by_id else None,
                    "rrf": round(rrf_scores[doc_id], 4),
                    "rerank": round(rerank_scores[doc_id], 4) if doc_id in rerank_scores else None,
                },
            }
        )

    # Fused pool with stage scores (what the reranker saw)
    fused_pool = []
    for doc_id in fused_ranked:
        fused_pool.append(
            {
                "id": doc_id,
                "dense_similarity": round(dense_by_id[doc_id], 4) if doc_id in dense_by_id else None,
                "bm25": round(bm25_by_id[doc_id], 4) if doc_id in bm25_by_id else None,
                "rrf": round(rrf_scores[doc_id], 4),
            }
        )

    return {
        "results": results,
        "candidates_retrieved": len(fused_ranked),
        "candidates_sent_to_llm": len(final_ranked),
        "latency_ms": {
            "dense": round(dense_ms, 2),
            "bm25": round(bm25_ms, 2),
            "fusion": round(fused_ms, 2),
            "rerank": round(rerank_ms, 2),
            "total": round((time.perf_counter() - t0) * 1000, 2),
        },
        "fused_pool": fused_pool,
        "reranked_ids": [r["id"] for r in results],
    }
