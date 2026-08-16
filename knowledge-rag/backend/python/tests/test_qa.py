"""Automated QA suite — maps 1:1 to QA_TEST_PLAN.md scenarios S1-S13.

Run from backend/python:  .venv/bin/python -m pytest tests/ -v
Hermetic: stub embedder (no model loads), reranker disabled, temp persistence
and log dirs. Never touches the network or your .env credentials.
"""

import json
import os
from pathlib import Path

import pytest

from app.llm import verify_citations
from app.retrieval import reciprocal_rank_fusion
from app.utils import extract_csv_chunks, extract_blocks_from_markdown

SAMPLE_DIR = Path(__file__).resolve().parents[3] / "sample-docs"

TXT_SAMPLE = "Aurora Labs is a software company founded in 2019. " \
             "Atlas costs $49 per user per month. Beacon integrates with Slack."
MD_SAMPLE = "# Aurora Labs FAQ\n\n## Billing\n\nAtlas costs $49 per user per month.\n\n## Security\n\nData is encrypted with AES-256."
CSV_SAMPLE = "Product,Category,Price\nAtlas,Analytics,49\nBeacon,Alerting,19\nNimbus,Pipeline,0\n"
DOCX_HEADINGS = ["Getting started", "Billing", "Security", "Integrations"]


# ---------- helpers ----------

def _ingest(client, session_id: str, filename: str, content: bytes, **params):
    mime = "application/octet-stream"
    return client.post(
        f"/ingest/{session_id}",
        files={"file": (filename, content, mime)},
        params=params,
    )


@pytest.fixture()
def session_id():
    import uuid

    return f"qa-{uuid.uuid4().hex[:10]}"


@pytest.fixture()
def ready_session(client, session_id):
    """A session with the TXT sample ingested (BM25 initialized)."""
    r = _ingest(client, session_id, "sample.txt", TXT_SAMPLE.encode())
    assert r.status_code == 200, r.text
    return session_id


# ---------- S1: extension whitelist ----------

def test_s1_unsupported_extension_rejected(client, session_id):
    r = _ingest(client, session_id, "malware.exe", b"MZ...")
    assert r.status_code == 400
    assert "Unsupported file type" in r.json()["detail"]
    assert ".exe" in r.json()["detail"]


def test_s1_png_rejected(client, session_id):
    r = _ingest(client, session_id, "image.png", b"\x89PNG")
    assert r.status_code == 400


# ---------- S2: size guardrail ----------

def test_s2_oversize_rejected(client, session_id, monkeypatch):
    import app.routes as routes

    monkeypatch.setattr(routes, "MAX_UPLOAD_BYTES", 100)
    r = _ingest(client, session_id, "big.txt", b"x" * 5000)
    assert r.status_code == 413
    assert "upload limit" in r.json()["detail"]


def test_s2_within_limit_ok(client, session_id):
    r = _ingest(client, session_id, "small.txt", b"hello world")
    assert r.status_code == 200


# ---------- S3: CSV row limit ----------

def test_s3_csv_row_limit(client, session_id, monkeypatch):
    import app.utils as utils

    monkeypatch.setattr(utils, "MAX_CSV_ROWS", 3)
    rows = "\n".join([f"r{i}" for i in range(10)])
    r = _ingest(client, session_id, "too_many.csv", f"h\n{rows}".encode())
    assert r.status_code == 400
    assert "row limit" in r.json()["detail"]


# ---------- S4: multi-format ingestion ----------

@pytest.mark.parametrize(
    "filename,content",
    [
        ("doc.txt", TXT_SAMPLE.encode()),
        ("doc.md", MD_SAMPLE.encode()),
        ("doc.csv", CSV_SAMPLE.encode()),
    ],
)
def test_s4_text_formats_ingest(client, session_id, filename, content):
    r = _ingest(client, session_id, filename, content)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["chunk_count"] >= 1
    assert body["chunk_strategy"] == "fixed"


def test_s4_docx_ingests(client, session_id, tmp_path):
    from docx import Document

    doc_path = tmp_path / "doc.docx"
    doc = Document()
    doc.add_heading("Guide", level=1)
    doc.add_paragraph("This is the body of the guide document.")
    doc.save(doc_path)
    r = _ingest(client, session_id, "doc.docx", doc_path.read_bytes())
    assert r.status_code == 200, r.text
    assert r.json()["chunk_count"] >= 1


def test_s4_pdf_ingests(client, session_id):
    pdf = SAMPLE_DIR / "aurora-labs.pdf"
    if not pdf.exists():
        pytest.skip("sample PDF not present")
    r = _ingest(client, session_id, "aurora-labs.pdf", pdf.read_bytes())
    assert r.status_code == 200, r.text
    assert r.json()["page_count"] >= 1


# ---------- S5: chunking strategy + settings validation ----------

def test_s5_structure_aware_uses_headings(client, session_id):
    r = _ingest(
        client, session_id, "faq.md", MD_SAMPLE.encode(), strategy="structure_aware"
    )
    assert r.status_code == 200, r.text
    # Each chunk should carry its heading line (verified via the document endpoint)
    dr = client.get(f"/documents/{session_id}/faq.md")
    assert dr.status_code == 200
    chunk_texts = [c["text"] for c in dr.json()["chunks"]]
    joined = "\n".join(chunk_texts)
    assert "Billing" in joined and "Security" in joined
    assert "Atlas costs $49" in joined


def test_s5_invalid_chunk_size_rejected(client, session_id):
    r = _ingest(client, session_id, "doc.txt", TXT_SAMPLE.encode(), chunk_size=10)
    assert r.status_code == 400


def test_s5_invalid_overlap_rejected(client, session_id):
    r = _ingest(client, session_id, "doc.txt", TXT_SAMPLE.encode(), overlap=500, chunk_size=200)
    assert r.status_code == 400


def test_s5_unknown_strategy_rejected(client, session_id):
    r = _ingest(client, session_id, "doc.txt", TXT_SAMPLE.encode(), strategy="magic")
    assert r.status_code == 400


def test_s5_markdown_block_extraction(tmp_path):
    md_file = tmp_path / "sample.md"
    md_file.write_text(MD_SAMPLE, encoding="utf-8")
    blocks = extract_blocks_from_markdown(str(md_file))
    headings = [b["heading"] for b in blocks if b.get("heading")]
    assert "Billing" in headings and "Security" in headings


# ---------- S6: CSV coherence ----------

def test_s6_csv_stays_tabular(client, session_id):
    r = _ingest(client, session_id, "products.csv", CSV_SAMPLE.encode())
    assert r.status_code == 200, r.text
    dr = client.get(f"/documents/{session_id}/products.csv")
    assert dr.status_code == 200
    chunks = dr.json()["chunks"]
    assert len(chunks) >= 1
    first = chunks[0]
    # Header row preserved and row range recorded
    assert "Product" in first["text"] and "Price" in first["text"]
    assert first["row_start"] == 2
    assert first["row_end"] >= 2


def test_s6_csv_chunker_units(tmp_path):
    csv_file = tmp_path / "p.csv"
    csv_file.write_text(CSV_SAMPLE, encoding="utf-8")
    chunks, data_rows = extract_csv_chunks(str(csv_file), max_words=500)
    assert data_rows == 3
    assert len(chunks) == 1
    text, row_start, row_end = chunks[0]
    assert "Product" in text and "Atlas" in text
    assert (row_start, row_end) == (2, 4)


# ---------- S7: hybrid scores labeled ----------

def test_s7_search_returns_labeled_scores(client, ready_session):
    r = client.post(f"/search/{ready_session}", json={"query": "Atlas price"})
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    assert results, "expected at least one retrieved chunk"
    for chunk in results:
        scores = chunk["retrieval_scores"]
        # All four stage keys present; never blended into one number
        assert set(scores.keys()) == {"dense_similarity", "bm25", "rrf", "rerank"}
        assert scores["rrf"] is not None
        assert scores["rerank"] is None  # reranker disabled in tests


# ---------- S8: RRF fusion math ----------

def test_s8_rrf_symmetric_ranks():
    lists = [["a", "b", "c"], ["b", "a", "d"]]
    fused = reciprocal_rank_fusion(lists, k=60)
    # a: rank 1 + rank 2 -> 1/61 + 1/62 ; b: rank 2 + rank 1 -> same
    assert abs(fused["a"] - fused["b"]) < 1e-12
    assert abs(fused["a"] - (1 / 61 + 1 / 62)) < 1e-12


def test_s8_rrf_k_constant():
    lists = [["a", "b"], ["b", "a"]]
    assert reciprocal_rank_fusion(lists, k=60)["a"] > reciprocal_rank_fusion(lists, k=1000)["a"]


# ---------- S9: retrieval funnel ----------

def test_s9_funnel_counts(client, ready_session):
    r = client.post(f"/search/{ready_session}", json={"query": "Atlas price"})
    assert r.status_code == 200
    body = r.json()
    assert body["candidates_retrieved"] >= body["candidates_sent_to_llm"]
    assert 1 <= body["candidates_sent_to_llm"] <= 5  # RERANK_TOP_K default


# ---------- S10: context isolation ----------

def test_s10_sessions_isolated(client, session_id):
    # Two sessions, different documents
    r_a = _ingest(client, session_id, "faq.md", MD_SAMPLE.encode())
    assert r_a.status_code == 200
    r_b = _ingest(client, f"{session_id}-b", "products.csv", CSV_SAMPLE.encode())
    assert r_b.status_code == 200

    # Searching session A must only surface faq.md chunks
    ra = client.post(f"/search/{session_id}", json={"query": "Atlas"})
    assert ra.status_code == 200
    assert all(c["filename"] == "faq.md" for c in ra.json()["results"])

    # And session B only products.csv chunks
    rb = client.post(f"/search/{session_id}-b", json={"query": "Beacon"})
    assert rb.status_code == 200
    assert all(c["filename"] == "products.csv" for c in rb.json()["results"])


# ---------- S11: citation verification ----------

def test_s11_strips_fabricated_markers():
    context = [
        {"id": "c1", "filename": "a.md", "page_number": 1, "text": "Atlas costs $49."},
        {"id": "c2", "filename": "a.md", "page_number": 1, "text": "Beacon integrates with Slack."},
    ]
    answer, citations = verify_citations("Atlas is $49 [1]. Beacon uses Slack [2]. Also [9] and [2] again.", context)
    assert "[1]" in answer and "[2]" in answer
    assert "[9]" not in answer
    assert len(citations) == 2
    assert [c["marker"] for c in citations] == [1, 2]
    assert citations[0]["id"] == "c1" and citations[1]["id"] == "c2"


def test_s11_no_citations_when_none_valid():
    answer, citations = verify_citations("No sources here [3] [42].", [{"id": "c1", "text": "x"}])
    assert answer == "No sources here  ."
    assert citations == []


# ---------- S12: graceful degradation ----------

def test_s12_chat_graceful_fallback_without_key(client, ready_session, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    r = client.post(f"/chat/{ready_session}", json={"query": "Atlas price"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data and len(data["answer"]) > 0
    assert "citations" in data


def test_s12_chat_graceful_fallback_on_generation_failure(client, ready_session, monkeypatch):
    import app.routes as routes

    monkeypatch.setattr(routes.llm_client, "llm_available", lambda: True)
    monkeypatch.setattr(
        routes.llm_client, "generate_answer", lambda q, c: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    r = client.post(f"/chat/{ready_session}", json={"query": "Atlas price"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data and len(data["answer"]) > 0
    assert "citations" in data


# ---------- S13: observability / JSONL logging ----------

def test_s13_search_writes_jsonl(client, ready_session):
    r = client.post(f"/search/{ready_session}", json={"query": "Atlas price"})
    assert r.status_code == 200

    log_dir = os.getenv("QUERY_LOG_DIR")
    log_path = Path(log_dir) / "queries.jsonl"
    assert log_path.exists(), "query log file not written"

    records = [json.loads(line) for line in log_path.read_text().splitlines() if line.strip()]
    last = records[-1]
    assert last["session_id"] == ready_session
    assert last["query"] == "Atlas price"
    assert "latency_ms" in last
    assert {"dense", "bm25", "fusion", "rerank", "total"} <= set(last["latency_ms"].keys())
    assert last["retrieved"]  # fused pool with stage scores
    assert last["final_answer"] is None  # search has no generation stage
