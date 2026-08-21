from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pathlib import Path
import json
import os
import queue
import re
import threading
import time

from .schemas import ChatResponse, IngestResponse, SearchResponse, GraphResponse, EntityResponse
from .utils import ingest_document, CHUNKERS, SUPPORTED_EXTENSIONS
from .dependencies import get_session_vectors, get_or_build_graph, invalidate_graph
from .retrieval import hybrid_search, RETRIEVE_CANDIDATES, RERANK_TOP_K
from .observability import log_query, utc_now_iso
from .space import get_space, transform_query
from .entities import extract_entities
from .knowledge_graph import query_graph, get_full_graph
from . import llm as llm_client

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "50")) * 1024 * 1024

# Chroma collection names allow [a-zA-Z0-9._-], 3-512 chars, alphanumeric
# start/end. Validate at the API boundary so a bad session id returns a clean
# 400 instead of an unhandled Chroma crash (500).
_SESSION_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{1,510}[a-zA-Z0-9]$")


def _validate_session_id(session_id: str) -> None:
    if not (3 <= len(session_id) <= 512 and _SESSION_ID_RE.fullmatch(session_id)):
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id: use 3-512 characters from [a-zA-Z0-9._-], "
            "starting and ending with an alphanumeric character",
        )


router = APIRouter()

@router.get("/documents/{session_id}")
async def list_documents(session_id: str):
    """List documents in a session (filename, chunk count, page/row numbers, embedder)."""
    _validate_session_id(session_id)
    session = get_session_vectors(session_id)
    collection = session["collection"]
    got = collection.get(include=["metadatas"])
    counts = {}
    for m in got["metadatas"]:
        filename = m.get("filename", "unknown")
        entry = counts.setdefault(
            filename, {"chunk_count": 0, "pages": set(), "embedder": m.get("embedder", "unknown"), "title": None}
        )
        entry["chunk_count"] += 1
        if m.get("title"):
            entry["title"] = m["title"]
        if m.get("page_number") is not None:
            entry["pages"].add(m["page_number"])
    documents = [
        {
            "filename": f,
            "title": c.get("title"),
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
    _validate_session_id(session_id)
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
    title = next((m.get("title") for m in got["metadatas"] if m.get("title")), None)
    return {"filename": filename, "title": title, "chunk_count": len(chunks), "chunks": chunks}


def _chunk_order(doc_id: str) -> int:
    """Chunk ids end in _c<N> where N is the global chunk index (document order)."""
    m = re.search(r"_c(\d+)$", doc_id)
    return int(m.group(1)) if m else 0


@router.post("/ingest/{session_id}")
async def ingest_file(
    session_id: str,
    file: UploadFile = File(...),
    chunk_size: int = 500,
    overlap: int = 100,
    strategy: str = "fixed",
    stream: bool = False,
):
    """Upload a document. With ?stream=1 the response is text/event-stream of
    real pipeline stages (parsing -> chunking -> embedding -> indexing -> done),
    so UIs can show honest progress instead of a timed animation. Without it,
    the response is the final IngestResponse JSON (backward compatible).
    """
    # Validate session id format (sessions are auto-created on first use)
    _validate_session_id(session_id)
    session = get_session_vectors(session_id)

    # Validate per-upload chunking settings
    if strategy not in CHUNKERS:
        raise HTTPException(status_code=400, detail=f"Unknown chunking strategy: {strategy}")
    if chunk_size < 50 or chunk_size > 2000:
        raise HTTPException(status_code=400, detail="chunk_size must be between 50 and 2000")
    if overlap < 0 or overlap >= chunk_size:
        raise HTTPException(status_code=400, detail="overlap must be >= 0 and < chunk_size")

    # Validate extension + size before touching anything.
    # Never trust client-supplied paths: strip any directory components
    # (both / and \ separators) and use the bare basename everywhere.
    filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    ext = os.path.splitext(filename)[1].lower()
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

    # Save uploaded file temporarily (basename only — never trust client paths)
    upload_dir = Path("/tmp/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / filename
    with open(file_path, "wb") as f:
        f.write(content)

    def ingest_and_report():
        """Run ingestion in a worker thread, streaming real stage events."""
        events: "queue.Queue" = queue.Queue()

        def report(stage: str):
            events.put({"stage": stage})

        def work():
            try:
                page_count, chunk_count, title = ingest_document(
                    session_id, filename, str(file_path),
                    chunk_size=chunk_size, overlap=overlap, strategy=strategy,
                    progress_cb=report,
                )
                events.put({
                    "stage": "done",
                    "result": IngestResponse(
                        session_id=session_id,
                        filename=filename,
                        title=title,
                        page_count=page_count,
                        chunk_count=chunk_count,
                        chunk_size=chunk_size,
                        overlap=overlap,
                        chunk_strategy=strategy,
                    ).model_dump(mode="json"),
                })
            except Exception as e:  # noqa: BLE001 - report mid-stream failures as events
                events.put({"stage": "error", "error": str(e)})

        t = threading.Thread(target=work, daemon=True)
        t.start()
        while True:
            evt = events.get()
            yield f"data: {json.dumps(evt)}\n\n"
            if evt["stage"] in ("done", "error"):
                break

    if stream:
        return StreamingResponse(ingest_and_report(), media_type="text/event-stream")

    # Non-streaming path (backward compatible)
    try:
        page_count, chunk_count, title = ingest_document(
            session_id, filename, str(file_path),
            chunk_size=chunk_size, overlap=overlap, strategy=strategy,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Invalidate cached knowledge graph since new chunks were added
    invalidate_graph(session_id)

    return IngestResponse(
        session_id=session_id,
        filename=filename,
        title=title,
        page_count=page_count,
        chunk_count=chunk_count,
        chunk_size=chunk_size,
        overlap=overlap,
        chunk_strategy=strategy,
    )

@router.get("/space/{session_id}")
async def vector_space(session_id: str, force: bool = False):
    """3D projection of every chunk in the session (UMAP, cached per document
    set). Returns compact {id, x, y, z, filename} points — full chunk text is
    fetched on demand, not shipped up front. ?force=1 recomputes the fit.
    """
    _validate_session_id(session_id)
    try:
        space = get_space(session_id, force=force)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "session_id": session_id,
        "method": space["method"],
        "embedder": space["embedder"],
        "point_count": space["point_count"],
        "clustered": space["clustered"],
        "threshold": space["threshold"],
        "points": space["points"],
    }


@router.post("/space/{session_id}/query")
async def vector_space_query(session_id: str, body: dict):
    """Drop a query into the existing map (UMAP .transform() — no re-layout)
    and report which chunks the retrieval funnel promoted vs. receded.
    """
    _validate_session_id(session_id)
    q = (body.get("query") or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query string required")

    session = get_session_vectors(session_id)
    bm25 = session.get("bm25")
    if bm25 is None:
        raise HTTPException(status_code=500, detail="BM25 index not initialized — upload a document first")

    out = hybrid_search(
        session["collection"], bm25, q,
        bm25_ids=session.get("bm25_ids"),
        candidates=RETRIEVE_CANDIDATES,
        top_k=RERANK_TOP_K,
    )
    point = transform_query(session_id, q)
    return {
        "session_id": session_id,
        "query": q,
        **point,
        "promoted_ids": out["reranked_ids"],
        "retrieved_ids": [c["id"] for c in out["fused_pool"]],
        "candidates_retrieved": out["candidates_retrieved"],
        "candidates_sent_to_llm": out["candidates_sent_to_llm"],
    }


@router.get("/entities/{session_id}/{chunk_id}")
async def get_chunk_entities(session_id: str, chunk_id: str):
    """Extract entities from a specific chunk's text."""
    _validate_session_id(session_id)
    session = get_session_vectors(session_id)
    collection = session["collection"]
    try:
        data = collection.get(ids=[chunk_id], include=["documents"])
    except Exception:
        raise HTTPException(status_code=404, detail=f"Chunk {chunk_id} not found")
    if not data.get("documents"):
        raise HTTPException(status_code=404, detail=f"Chunk {chunk_id} not found")

    text = data["documents"][0]
    entities = extract_entities(text)
    return EntityResponse(
        session_id=session_id,
        chunk_id=chunk_id,
        entities=[e.to_dict() for e in entities],
    )


@router.get("/graph/{session_id}")
async def get_graph(session_id: str, force: bool = False):
    """Get the knowledge graph for a session.

    Returns typed nodes (entities) and weighted edges (co-occurrence).
    Use ?force=1 to rebuild from chunks.
    """
    _validate_session_id(session_id)
    if force:
        invalidate_graph(session_id)
    G = get_or_build_graph(session_id)
    if G is None:
        raise HTTPException(status_code=404, detail="No documents ingested — upload files first")

    result = get_full_graph(G)
    return GraphResponse(
        session_id=session_id,
        nodes=result.nodes,
        edges=result.edges,
        stats=result.stats,
    )


@router.post("/graph/{session_id}/query")
async def graph_query(session_id: str, body: dict):
    """Query the knowledge graph with entities extracted from a query string.

    Finds matching nodes and expands to 1-hop neighbors.
    """
    _validate_session_id(session_id)
    q = (body.get("query") or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query string required")

    G = get_or_build_graph(session_id)
    if G is None:
        raise HTTPException(status_code=404, detail="No documents ingested — upload files first")

    # Extract entities from the query
    query_entities = [e.text for e in extract_entities(q)]
    result = query_graph(G, query_entities)

    return GraphResponse(
        session_id=session_id,
        nodes=result.nodes,
        edges=result.edges,
        stats=result.stats,
        query_entities=result.query_entities,
    )


@router.post("/title")
async def chat_title(body: dict):
    """Short chat title for a query: LLM summary when a key is configured,
    else a deterministic heuristic. Called once after the first exchange so the
    sidebar shows a meaningful title instead of 'New chat'.
    """
    q = (body.get("query") or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query string required")
    return {"title": llm_client.summarize_title(q)}

@router.post("/search/{session_id}", response_model=SearchResponse)
async def search(session_id: str, query: dict):
    # query expects {"query": "..."}
    _validate_session_id(session_id)
    q = query.get("query")
    if not q:
        raise HTTPException(status_code=400, detail="Query string required")

    session = get_session_vectors(session_id)

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
            "title": r.get("title"),
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
    _validate_session_id(session_id)
    q = (body.get("query") or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query string required")

    session = get_session_vectors(session_id)
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
            "title": r.get("title"),
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

    # Answer-level confidence: mean of cited chunk confidences
    cited_confidences = [c.get("confidence") for c in citations if c.get("confidence") is not None]
    answer_confidence = round(sum(cited_confidences) / len(cited_confidences), 4) if cited_confidences else None

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
        "answer_confidence": answer_confidence,
    })

    return ChatResponse(
        session_id=session_id,
        query=q,
        answer=answer,
        citations=citations,
        metrics=metrics,
        candidates_retrieved=out["candidates_retrieved"],
        candidates_sent_to_llm=out["candidates_sent_to_llm"],
        answer_confidence=answer_confidence,
    )
