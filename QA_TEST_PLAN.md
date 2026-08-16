# Knowledge RAG — QA Test Plan

Automated + manual validation matrix for the Knowledge RAG hybrid RAG app, mirroring
the original VectorMind 14-scenario QA suite and adapted to the current architecture
(5 formats, RRF fusion, cross-encoder reranking, `/chat` with citation verification,
JSONL observability, document viewer).

- **Automated suite**: `backend/python/tests/test_qa.py` (pytest) — run with
  `cd backend/python && .venv/bin/python -m pytest tests/ -v`
- **Manual checks**: browser-level scenarios (greeting interceptor, localStorage
  recovery, network degradation, document viewer) documented in detail below.
- **Status legend**: `PASS` (verified by the automated suite), `MANUAL` (requires
  browser interaction — procedure provided, not yet executed).

---

## 1. Scenario Matrix

| # | Category | Validation Behavior | Automation | Status |
|---|----------|---------------------|------------|--------|
| 0 | PDF Extraction Hygiene | Page-number lines, running headers/footers, and glued numeric prefixes (the `04Build` artifact) are stripped at extraction; legitimate in-body numbers (`2024`, `$49`) are preserved | pytest | `PASS` |
| 0b | PDF Extraction Regression | Re-extracting the sample corpus matches the stored baseline (regenerate with `UPDATE_BASELINES=1`) | pytest | `PASS` |
| 1 | Ingestion Boundaries | Rejects unsupported extensions (`.exe`, `.png`) with a clear 400 error before any parsing | pytest | `PASS` |
| 2 | Ingestion Boundaries | Rejects files over the size limit (default 50 MB) with 413 — no partial indexing | pytest | `PASS` |
| 3 | Ingestion Boundaries | Rejects CSVs over `MAX_CSV_ROWS` with 400 | pytest | `PASS` |
| 4 | Multi-Format Ingestion | All 5 supported formats (`.pdf`, `.txt`, `.docx`, `.md`, `.csv`) ingest and are searchable | pytest | `PASS` |
| 5 | Chunking Strategy | `structure_aware` splits along headings (md/docx); `fixed` uses size+overlap windows; per-upload settings validated (bad `chunk_size`/`overlap` → 400) | pytest | `PASS` |
| 6 | CSV Coherence | CSV chunks stay tabular — each chunk keeps the header row and records `row_start`/`row_end` | pytest | `PASS` |
| 7 | Hybrid Retrieval | Dense (Chroma), sparse (BM25), RRF, and rerank scores returned **separately and labeled** (never blended) | pytest | `PASS` |
| 8 | RRF Fusion | Reciprocal Rank Fusion math correct (k-configurable, rank-based, no score calibration) | pytest | `PASS` |
| 9 | Retrieval Funnel | Widen-then-rerank: `candidates_retrieved` ≥ `candidates_sent_to_llm` (20 → 5 by default) | pytest | `PASS` |
| 10 | Context Isolation | Queries in session A never surface chunks from session B's documents | pytest | `PASS` |
| 11 | Citation Verification | Fabricated/out-of-range `[n]` markers stripped from generated answers; valid markers map to actually-retrieved chunks | pytest | `PASS` |
| 12 | Graceful Degradation | `/chat` with no LLM key or a failing generation returns `200` with a grounded extractive fallback answer (never hangs, never fabricates) | pytest | `PASS` |
| 13 | Observability | Every search/chat writes one structured JSONL record (query, retrieved ids + scores, latency breakdown, answer, tokens) | pytest | `PASS` |
| 14 | Greeting Handling | Local interceptor answers "hi"/"hello" in < 400 ms with zero backend calls | manual | `MANUAL` |

> **Adapted from the original matrix**: the original's *Auto-Summarization* scenario is
> out of scope — Knowledge RAG has no auto-summary stage; its closest equivalent
> (the post-upload metadata preview card) is covered in the manual frontend checks
> below. *Local Storage Recovery*, *Network Degradation*, and *Document Viewer* are
> also frontend scenarios and are listed under §3 Manual Frontend Checks.

---

## 2. Detailed Scenario Specs (automated)

### 2.0 PDF Extraction Hygiene (S0, S0b)
- **S0 — Artifact stripping.** `clean_page_text` removes standalone page-number
  lines (`3`, `Page 4`, `— 7 —`), running headers/footers detected across pages
  (normalized digit/punctuation-stripped key, >50% recurrence at page top/bottom),
  and the glue pattern (`04Build` → `Build`) at the first content line only.
  Legitimate numbers (`2024 revenue`, `$49`) are never touched.
- **S0b — Regression baseline.** `tests/baselines/pdf_extraction.json` stores the
  cleaned extraction of the sample corpus; `test_pdf_extraction_baseline`
  re-extracts and diffs, so a future parser change that reintroduces
  contamination fails CI. Regenerate with `UPDATE_BASELINES=1`.

### 2.1 Ingestion Boundaries
- **S1 — Extension whitelist.** POST `/ingest/{session}` with a `.exe` file →
  `400` with message listing supported extensions. No chunk is stored.
- **S2 — Size guardrail.** Upload a file larger than `MAX_UPLOAD_MB` (default 50) →
  `413`. The check runs before parsing or embedding, so no partial index exists.
- **S3 — CSV row limit.** A CSV with more than `MAX_CSV_ROWS` data rows →
  `400` "CSV exceeds row limit".

### 2.2 Multi-Format Ingestion (S4)

Each of `.txt`, `.md`, `.csv`, `.docx`, and `.pdf` ingests with `chunk_count ≥ 1`
and returns page/row counts (`page_count` carries the data-row count for CSVs).
Chunk metadata records `filename`, `chunk_strategy`, `chunk_size`, `overlap`, and
`embedder` — retrieval results stay explainable.

### 2.3 Chunking (S5, S6)
- `structure_aware` on a multi-heading markdown file produces chunks whose text
  contains the heading lines (verified against `sample-docs/faq.md`'s 12 sections).
- CSV chunks retain the header row, and metadata carries the exact `row_start`/
  `row_end` file-row range.
- Invalid settings: `chunk_size < 50`, `chunk_size > 2000`, `overlap < 0`, or
  `overlap ≥ chunk_size` → `400`.

### 2.4 Hybrid Retrieval & RRF (S7, S8, S9)
- `hybrid_search` returns per-chunk `retrieval_scores` with all four keys
  (`dense_similarity`, `bm25`, `rrf`, `rerank`) — each present and labeled, with
  `rerank` `null` when the reranker is disabled.
- RRF unit check: with k=60, doc ranked 1st by dense and 2nd by sparse scores
  `1/(60+1) + 1/(60+2)`, equal to the symmetric case — no score blending.
- The response exposes `candidates_retrieved` (wide fused pool) and
  `candidates_sent_to_llm` (narrow top-k) with `candidates_retrieved ≥
  candidates_sent_to_llm`.

### 2.5 Context Isolation (S10)
Two sessions ingest different documents. Searching session A returns only
chunks whose `filename` belongs to session A; session B likewise. No
cross-document or cross-session leakage (Chroma collection + BM25 index are
both per-session).

### 2.6 Generation & Citation Verification (S11, S12)
- `verify_citations`: an answer referencing `[1]`, `[2]`, and a fabricated `[9]`
  keeps the valid markers, strips `[9]`, dedupes repeated markers, and returns
  citations mapped to the actual retrieved chunks (id, filename, page).
- `/chat` degrades gracefully instead of hanging: with no LLM key configured or
  a failing generation call, it returns `200` with a grounded extractive
  fallback answer (top chunks quoted verbatim with working `[n]` citations).

### 2.7 Observability (S13)
A search writes exactly one JSONL line to `QUERY_LOG_DIR/queries.jsonl`
containing `query`, `session_id`, `retrieved` (ids + stage scores),
`reranked_ids`, candidate counts, `latency_ms` breakdown (dense/bm25/fusion/
rerank/total), and `final_answer` (null for search, populated for chat).

### 2.8 Real ingestion stages + titles (S14)
- **Streaming ingest.** `POST /ingest/{session}?stream=1` returns
  `text/event-stream` with real pipeline stages in order — `parsing` →
  `chunking` → `embedding` → `indexing` → `done` — then the final result
  (chunk count, title). Mid-stream failures (e.g. an empty CSV) surface as a
  `stage: error` event, not a broken stream or a 500.
- **Document titles.** Ingest responses, `/documents`, search results, and
  citations carry a best-effort `title` (PDF `/Title`, DOCX core properties,
  Markdown H1, short first line of a `.txt`). CSVs and generic/empty titles
  return `null` so the UI falls back to the upload filename.
- **`POST /title`.** Returns a short chat title for a query — LLM summary when
  a key is configured, else a deterministic first-8-words heuristic; empty
  queries are rejected with `400`.
- **Cosine space.** Sessions are indexed with `hnsw:space=cosine` so the
  `dense_similarity` score reported in search results is an actual cosine
  similarity, not `1 - L2`.

---

## 3. Manual Frontend Checks

### 3.1 Greeting Interceptor (S14)
1. Open `/#/chat`, type `hi` and send.
2. Expect an instant local reply ("Hello! How can I assist you with your
   document?") in well under 400 ms, with **no** backend request (check the
   uvicorn access log — no `/search` or `/chat` line).
3. Repeat with `hello` and `hey`.

### 3.2 Local Storage Recovery
1. Create a session, upload a document, send a query with sources.
2. Rename the session, pin it, and add a tag.
3. Hard-reload the page. Expect: session list, active tab, messages, pin, and
   tag all restored from `localStorage` (new `pinned`/`tags` fields default
   safely for sessions saved before the feature).

### 3.3 Network Degradation
1. Stop the backend (`Ctrl-C` on uvicorn).
2. Send a query. Expect a graceful error bubble ("Backend unreachable…") within
   the 120 s `AbortController` window — no frozen spinner.
3. Restart the backend; the app recovers without a reload.

### 3.4 Ingestion Stage Feedback
1. Upload a large document and watch the progress bar.
2. Expect human-readable stage labels that match the real backend stages
   (`Extracting text…` → `Chunking document…` → `Generating embeddings…` →
   `Indexing…` → `Ready`) — driven by `?stream=1` events, not a timed
   animation, so the label cannot drift from what the backend is doing.

### 3.5 Auto Chat Titles
1. Create a chat and upload a document. Expect the sidebar to name the chat
   after the document's title (or filename) immediately.
2. Ask a real question. Expect the title to be replaced with a short summary
   of the query (LLM when a key is set, heuristic otherwise).
3. Create a new chat and immediately reload the page without uploading or
   sending anything. Expect the empty "New chat" draft to be gone — it never
   lingers in the sidebar.

### 3.6 Document Viewer
1. Ask a question that produces citations, open the Sources panel, click
   **View in document →** on a citation.
2. Expect the split-screen viewer to open that document, auto-scroll to the
   cited chunk, and highlight the chunk plus the query-relevant sentence.
3. Test with a CSV citation (chunk shows its row range) and a markdown citation.

### 3.7 Upload Workspace
1. Drag a file over the dropzone — expect the glow/pulse micro-animation and
   the metadata preview card (type badge, size, staged progress, then page/row
   + chunk counts and strategy).
2. Try uploading `.png`/`.exe` — expect an instant client-side error.
3. Try a file > 50 MB — expect a size error before upload.

---

## 4. Traceability to the Original VectorMind Matrix

| Original scenario | Knowledge RAG equivalent |
|---|---|
| Ingestion Boundaries (non-PDFs, > 50 MB) | S1–S3 (extended: 5 formats, 50 MB default, CSV row limit) |
| Auto-Summarization | Out of scope — replaced by metadata preview card (§3.5) |
| Context Isolation | S10 (per-session Chroma collection + BM25 index) |
| Greeting Handling | S14 (§3.1) |
| Local Storage Recovery | §3.2 |
| Network Degradation | S12 backend + §3.3 frontend |
| *(new)* RRF fusion correctness | S8 |
| *(new)* Widen-then-rerank funnel | S9 |
| *(new)* Citation verification / anti-hallucination | S11 |

---

## 5. Running the Automated Suite

```bash
cd backend/python
source .venv/bin/activate        # or: .venv/bin/python
pip install -r requirements-dev.txt   # pytest, httpx
python -m pytest tests/ -v
```

The suite is hermetic: it stubs the embedder and sets the reranker disabled
(`RERANKER_ENABLED=false`), uses a temp Chroma persistence dir and temp query
log dir, and never touches the network or your `.env` credentials. Reranker
behavior is covered separately by the eval-harness ablation runs
(`RERANKER_ENABLED=false` vs default) in the README benchmarks.

Last updated: 2026-08-16
