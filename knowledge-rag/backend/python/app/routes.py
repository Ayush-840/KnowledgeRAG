from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
import os
import re
import time

from .schemas import ChatResponse, IngestResponse, SearchResponse
from .utils import ingest_document, CHUNKERS, SUPPORTED_EXTENSIONS
from .dependencies import get_session_vectors
from .retrieval import hybrid_search, RETRIEVE_CANDIDATES, RERANK_TOP_K
from .observability import log_query, utc_now_iso
from . import llm as llm_client

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024

router = APIRouter()

@router.get("/documents/{session_id}")
async def list_documents(session_id: str):
    """List documents in a session (filename, chunk count, page/row numbers, embedder)."""
    session = get_session_vectors(session_id)
    collection = session["collection"]
    got = collection.get(include=["metadatas"])
    counts = {}
    for m in got["metadatas"]:
        filename = m.get("filename", "unknown")
        entry = counts.setdefault(
            filename, {"chunk_count": 0, "pages": set(), "embedder": m.get("embedder", "unknown")}
        )
        entry["chunk_count"] += 1
        if m.get("page_number") is not None:
            entry["pages"].add(m["page_number"])
    documents = [
        {
            "filename": f,
            "chunk_count": c["chunk_count"],
            "pages": sorted(c["pages"]),
            "embedder": c["embedder"],
        }
        for f, c in sorted(counts.items())
    ]
    return {"session_id": session_id, "documents": documents}


@router.get("/documents/{session_id}/{filename}")
async def get_document(session_id: str, filename: str):
    """Fetch one document's chunks in document order for in-context viewing."""
    session = get_session_vectors(session_id)
    collection = session["collection"]
    got = collection.get(where={"filename": filename}, include=["documents", "metadatas"])
    chunks = []
    for cid, text, m in zip(got["ids"], got["documents"], got["metadatas"]):
        chunks.append(
            {
                "id": cid,
                "page_number": m.get("page_number", 0),
                "text": text,
                "chunk_strategy": m.get("chunk_strategy", "fixed"),
                "row_start": m.get("row_start"),
                "row_end": m.get("row_end"),
            }
        )
    chunks.sort(key=lambda c: _chunk_order(c["id"]))
    return {"filename": filename, "chunk_count": len(chunks), "chunks": chunks}


def _chunk_order(doc_id: str) -> int:
    """Chunk ids end in _c<N> where N is the global chunk index (document order)."""
    m = re.search(r"_c(\d+)$", doc_id)
    return int(m.group(1)) if m else 0


@router.post("/ingest/{session_id}", response_model=IngestResponse)
async def ingest_file(
    session_id: str,
    file: UploadFile = File(...),
    chunk_size: int = 500,
    overlap: int = 100,
    strategy: str = "fixed",
):
    # Validate session exists
    session = get_session_vectors(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate per-upload chunking settings
    if strategy not in CHUNKERS:
        raise HTTPException(status_code=400, detail=f"Unknown chunking strategy: {strategy}")
    if chunk_size < 50 or chunk_size > 2000:
        raise HTTPException(status_code=400, detail="chunk_size must be between 50 and 2000")
    if overlap < 0 or overlap >= chunk_size:
        raise HTTPException(status_code=400, detail="overlap must be >= 0 and < chunk_size")

    # Validate extension + size before touching anything
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB upload limit",
        )

    # Save uploaded file temporarily
    upload_dir = Path("/tmp/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(content)

    # Process ingestion
    try:
        page_count, chunk_count = ingest_document(
            session_id, file.filename, str(file_path),
            chunk_size=chunk_size, overlap=overlap, strategy=strategy,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return IngestResponse(
        session_id=session_id,
        filename=file.filename,
        page_count=page_count,
        chunk_count=chunk_count,
        chunk_size=chunk_size,
        overlap=overlap,
        chunk_strategy=strategy,
    )

@router.post("/search/{session_id}", response_model=SearchResponse)
async def search(session_id: str, query: dict):
    # query expects {"query": "..."}
    q = query.get("query")
    if not q:
        raise HTTPException(status_code=400, detail="Query string required")

    session = get_session_vectors(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    collection = session["collection"]
    bm25 = session.get("bm25")
    if bm25 is None:
        raise HTTPException(status_code=500, detail="BM25 index not initialized")

    # Hybrid retrieval: dense + BM25 -> RRF fusion -> cross-encoder rerank
    out = hybrid_search(
        collection,
        bm25,
        q,
        bm25_ids=session.get("bm25_ids"),
        candidates=RETRIEVE_CANDIDATES,
        top_k=RERANK_TOP_K,
    )
    results = out["results"]

    result_chunks = []
    for r in results:
        # confidence = reranker score when available, else RRF score (both labeled separately)
        scores = r["retrieval_scores"]
        confidence = scores["rerank"] if scores["rerank"] is not None else scores["rrf"]
        result_chunks.append({
            "id": r["id"],
            "text": r["text"],
            "filename": r["filename"],
            "page_number": r["page_number"],
            "chunk_strategy": r["chunk_strategy"],
            "retrieval_scores": scores,
            "confidence": round(confidence, 4) if confidence is not None else None,
        })

    # Structured per-query log (JSONL) — read by the eval harness and metrics dashboard
    log_query({
        "ts": utc_now_iso(),
        "session_id": session_id,
        "query": q,
        "retrieved": out["fused_pool"],
        "reranked_ids": out["reranked_ids"],
        "candidates_retrieved": out["candidates_retrieved"],
        "candidates_sent_to_llm": out["candidates_sent_to_llm"],
        "final_answer": None,  # generation stage arrives in a later phase
        "citations": [
            {"id": r["id"], "filename": r["filename"], "page_number": r["page_number"]}
            for r in results
        ],
        "latency_ms": out["latency_ms"],
    })

    return SearchResponse(
        session_id=session_id,
        query=q,
        results=result_chunks,
        candidates_retrieved=out["candidates_retrieved"],
        candidates_sent_to_llm=out["candidates_sent_to_llm"],
    )

@router.post("/chat/{session_id}", response_model=ChatResponse)
async def chat(session_id: str, body: dict):
    """Full RAG chat: hybrid retrieval -> cross-encoder rerank -> LLM generation
    with citation verification. Requires an LLM API key (NVIDIA_API_KEY or
    OPENROUTER_API_KEY, selected via LLM_PROVIDER).
    """
    q = (body.get("query") or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query string required")

    session = get_session_vectors(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    collection = session["collection"]
    bm25 = session.get("bm25")
    if bm25 is None:
        raise HTTPException(status_code=500, detail="BM25 index not initialized — upload a document first")

    t0 = time.perf_counter()
    out = hybrid_search(
        collection, bm25, q,
        bm25_ids=session.get("bm25_ids"),
        candidates=RETRIEVE_CANDIDATES,
        top_k=RERANK_TOP_K,
    )

    # Build context chunks with everything the citation panel + logs need
    context = []
    for r in out["results"]:
        scores = r["retrieval_scores"]
        confidence = scores["rerank"] if scores["rerank"] is not None else scores["rrf"]
        context.append({
            "id": r["id"],
            "text": r["text"],
            "filename": r["filename"],
            "page_number": r["page_number"],
            "scores": scores,
            "confidence": round(confidence, 4) if confidence is not None else None,
        })

    if not llm_client.llm_available():
        raw_answer, usage, gen_ms = llm_client._generate_extractive_fallback(q, context, "API key not configured")
    else:
        try:
            raw_answer, usage, gen_ms = llm_client.generate_answer(q, context)
        except Exception as e:
            raw_answer, usage, gen_ms = llm_client._generate_extractive_fallback(q, context, str(e))

    answer, citations = llm_client.verify_citations(raw_answer, context)
    total_ms = round((time.perf_counter() - t0) * 1000, 2)

    metrics = {
        "retrieval_ms": out["latency_ms"],
        "generation_ms": gen_ms,
        "total_ms": total_ms,
        "tokens": {
            "prompt": usage.get("prompt_tokens"),
            "completion": usage.get("completion_tokens"),
            "total": usage.get("total_tokens"),
        },
        "model": llm_client.GENERATION_MODEL,
    }

    log_query({
        "ts": utc_now_iso(),
        "session_id": session_id,
        "query": q,
        "retrieved": out["fused_pool"],
        "reranked_ids": out["reranked_ids"],
        "candidates_retrieved": out["candidates_retrieved"],
        "candidates_sent_to_llm": out["candidates_sent_to_llm"],
        "final_answer": answer,
        "citations": [
            {"id": c["id"], "filename": c["filename"], "page_number": c["page_number"]}
            for c in citations
        ],
        "latency_ms": {**out["latency_ms"], "generation": gen_ms, "total": total_ms},
        "tokens": metrics["tokens"],
        "model": llm_client.GENERATION_MODEL,
    })

    return ChatResponse(
        session_id=session_id,
        query=q,
        answer=answer,
        citations=citations,
        metrics=metrics,
        candidates_retrieved=out["candidates_retrieved"],
        candidates_sent_to_llm=out["candidates_sent_to_llm"],
    )
