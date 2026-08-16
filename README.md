<p align="center">
  <img src="knowledge-rag/frontend/react/public/logo.svg" alt="Knowledge RAG logo" width="96" />
</p>

# Knowledge RAG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react&logoColor=white)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FC60A8)](https://www.trychroma.com)
[![sentence-transformers](https://img.shields.io/badge/sentence--transformers-1b6ec2)](https://www.sbert.net)

**Ask your documents. Get grounded answers.**

Knowledge RAG is a hybrid retrieval-augmented generation app for document
Q&A. It retrieves over your PDFs and text files with **dense + sparse hybrid
search fused via Reciprocal Rank Fusion (RRF)**, narrows the result set with a
**cross-encoder reranker**, and keeps every score in the pipeline **separate
and labeled** — dense similarity, BM25, RRF, and reranker — so answers can be
checked against the sources instead of trusted on faith.

What makes it distinctive:

- **Principled fusion, not score blending.** Dense (ChromaDB) and sparse (BM25)
  rankings are merged with RRF — no hand-tuned 0.6/0.4 weight soup.
- **Retrieve wide, rerank narrow.** A fused pool of candidates (default 20) is
  re-scored by a `BAAI/bge-reranker-base` cross-encoder, and only the top-k
  (default 5) move on — the API reports both numbers per query.
- **Component-wise evaluation, not vibes.** Retrieval quality (context
  precision/recall) and generation quality (faithfulness, answer relevance)
  are measured separately by a reproducible harness — a high faithfulness
  score with low context recall is a classic false-positive pattern that a
  single end-to-end score would hide.
- **Retrieval transparency.** Every returned chunk carries its stage-wise
  scores separately (dense / BM25 / RRF / rerank), the chunking strategy that
  produced it, and inline `[n]` citations verified against the actual
  retrieved chunks.
- **Clean extraction.** PDF text is scrubbed at the source — standalone page
  numbers, running headers/footers (detected across pages), and glued numeric
  prefixes (`04Build`) are removed before chunking, so embeddings and BM25 are
  never poisoned by layout noise. A stored extraction baseline makes parser
  regressions fail CI instead of surfacing later.
- **Per-upload chunking controls.** Chunk size, overlap, and strategy
  (`fixed` | `structure_aware`) are set per upload and recorded in the index
  metadata.

## Demo

> 🎬 **Demo video coming soon** — a short walkthrough (upload → ask →
> citations → source inspection) will be embedded here once recorded.

## Architecture

```mermaid
flowchart LR
    subgraph Ingest
        A[PDF / TXT / DOCX / MD / CSV] --> B[Parser<br/>pypdf · pdfplumber · python-docx · csv]
        B --> B2[Artifact scrubber<br/>page numbers · headers/footers · glued prefixes]
        B2 --> C[Chunker<br/>fixed | structure-aware]
        C --> D[Embedder<br/>MiniLM · swappable via EMBEDDER]
        D --> E[(ChromaDB<br/>per-session)]
        C --> F[BM25 index<br/>rank-bm25]
    end

    subgraph Query
        Q[Query] --> G[Dense top-N]
        Q --> H[BM25 top-N]
        G --> I[RRF fusion · top-20 pool]
        H --> I
        I --> J[Cross-encoder reranker<br/>bge-reranker-base · top-5]
        J --> K[Defensive prompt<br/>+ strict citation rules]
        K --> L[LLM<br/>GPT-4o via OpenRouter]
        L --> M[Answer + verified citations]
    end

    subgraph Observe
        E --> N[JSONL query log<br/>scores · order · latency · tokens]
        F --> N
        M --> N
        N --> O[Eval harness<br/>precision · recall · faithfulness · relevance]
        E --> P[Vector space explorer<br/>UMAP 3D projection · optional/advanced]
        P --> N
    end
```

The Vector Space Explorer is an **optional, advanced** feature: it renders the
session's chunk embeddings as a navigable 3D point cloud (see below) and is
shown as an observer of the indexed embeddings, never in the critical
retrieval/generation path.

Sessions are fully isolated: each session gets its own persistent Chroma
collection and BM25 index under `CHROMA_PERSISTENCE_DIR`, so documents never
leak across sessions.

## Repository layout

```
knowledge-rag/
├── backend/
│   ├── python/          # FastAPI retrieval + generation service
│   │   ├── app/
│   │   │   ├── main.py          # FastAPI app entrypoint
│   │   │   ├── routes.py        # /ingest, /search, /chat, /documents endpoints
│   │   │   ├── retrieval.py     # RRF fusion + cross-encoder reranking
│   │   │   ├── utils.py         # extraction, chunking, embedding, ingestion
│   │   │   ├── embedders.py     # swappable embedding models (MiniLM, OpenAI)
│   │   │   ├── llm.py           # OpenRouter generation + citation verification
│   │   │   ├── observability.py # per-query JSONL logging
│   │   │   ├── dependencies.py  # per-session Chroma + BM25 state
│   │   │   └── schemas.py       # response models
│   │   └── eval/                # RAGAS-style eval harness (golden set, LLM judge)
│   └── node/            # Express gateway proxying /ingest, /search, /chat
└── frontend/
    └── react/           # React 19 + Vite UI: landing page + chat app
        ├── src/pages/Home.jsx           # App shell (sidebar + chat + drawer)
        ├── src/components/              # ChatBox, Message, FileUpload, Sidebar, SourceDrawer, MetricsPanel
        ├── src/hooks/useChatSessions.js # Multi-session manager (localStorage, greeting interceptor)
        └── src/services/api.js          # Fetch wrapper with AbortController timeouts
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm

## Getting started

### 1. Python retrieval service

```bash
cd backend/python
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # optional; defaults work out of the box
uvicorn app.main:app --reload --port 8001
```

The service is now at `http://localhost:8001` (`/health` for a status check).
On the first search, the reranker model (`BAAI/bge-reranker-base`, ~1.1 GB) is
downloaded on demand; set `RERANKER_ENABLED=false` to skip it and rely on RRF
ordering.

### 2. Node gateway (optional proxy)

```bash
cd backend/node
npm install
cp .env.example .env                # optional
npm start                           # http://localhost:8000
```

The gateway proxies `/ingest`, `/search`, `/chat`, `/documents`, and `/title`
to the Python service (`PYTHON_URL`, default `http://localhost:8001`).
Streaming responses (the `?stream=1` ingest stages) pass through untouched.

### 3. Frontend

```bash
cd frontend/react
npm install
npm run dev                         # http://localhost:5173
```

## Environment variables

**Python service** (`backend/python/.env`):

| Variable               | Default                    | Description                                      |
| ---------------------- | -------------------------- | ------------------------------------------------ |
| `CHROMA_PERSISTENCE_DIR` | `./chroma_data`          | Where per-session Chroma + BM25 indexes live     |
| `RRF_K`                | `60`                       | Reciprocal Rank Fusion constant                  |
| `RETRIEVE_CANDIDATES`  | `20`                       | Wide retrieval pool before reranking             |
| `RERANK_TOP_K`         | `5`                        | Top-k chunks sent to generation after reranking  |
| `RERANKER_MODEL`       | `BAAI/bge-reranker-base`   | Cross-encoder reranker model                     |
| `RERANKER_ENABLED`     | `true`                     | Set `false` to skip reranking (RRF order only)   |
| `QUERY_LOG_DIR`        | `./logs`                   | Where per-query JSONL logs are written           |
| `EMBEDDER`             | `minilm`                   | Embedding model: `minilm` (local) or `openai`    |
| `OPENAI_API_KEY`       | —                          | Required when `EMBEDDER=openai`                  |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model                           |
| `MAX_UPLOAD_MB`        | `50`                       | Upload size limit per file                       |
| `MAX_CSV_ROWS`         | `50000`                    | Max data rows accepted for CSVs                  |
| `LLM_PROVIDER`         | `openrouter`               | `openrouter` (needs `OPENROUTER_API_KEY`) or `nvidia` (needs `NVIDIA_API_KEY`) |
| `OPENROUTER_API_KEY`   | —                          | Required for `/chat` answers when `LLM_PROVIDER=openrouter` |
| `NVIDIA_API_KEY`       | —                          | Required for `/chat` answers when `LLM_PROVIDER=nvidia` (free key at build.nvidia.com) |
| `GENERATION_MODEL`     | `openai/gpt-4o`            | LLM used for chat answers (`meta/llama-3.3-70b-instruct` on NVIDIA) |
| `GENERATION_MAX_TOKENS`| `600`                      | Max completion tokens per chat answer            |
| `UMAP_CLUSTER_THRESHOLD` | `4000`                  | Above this chunk count the 3D view clusters points into representative markers |
| `EVAL_GENERATION_MODEL`| `openai/gpt-4o`            | Model used to generate eval answers (uses same `LLM_PROVIDER`) |
| `EVAL_JUDGE_MODEL`     | `openai/gpt-4o`            | Model used to judge faithfulness + relevance     |

**Node gateway** (`backend/node/.env`):

| Variable    | Default                | Description                          |
| ----------- | ---------------------- | ------------------------------------ |
| `PORT`      | `8000`                 | Gateway listen port                  |
| `PYTHON_URL`| `http://localhost:8001`| Python retrieval service base URL    |

## API

### `POST /ingest/{session_id}`

Upload a document. Supported formats: **.pdf, .txt, .docx, .md, .csv** (max
`MAX_UPLOAD_MB`, default 50 MB). Accepts optional per-upload chunking settings.
With `?stream=1` the response is `text/event-stream` of **real pipeline
stages** — `parsing` → `chunking` → `embedding` → `indexing` → `done` — so the
UI progress bar reflects what the backend is actually doing, not a timed
animation. The non-streaming response stays backward compatible.

| Query param | Default | Description                          |
| ----------- | ------- | ------------------------------------ |
| `chunk_size`| `500`   | Max words per chunk (50–2000)        |
| `overlap`   | `100`   | Word overlap between chunks (0 ≤ overlap < chunk_size) |
| `strategy`  | `fixed` | `fixed` or `structure_aware`         |

Format-specific behavior:

- **.pdf / .txt** — page-based extraction; `structure_aware` respects paragraph
  boundaries within pages.
- **.docx** — headings are preserved; `structure_aware` splits along heading
  boundaries.
- **.md** — chunked along heading boundaries by default.
- **.csv** — chunked row-wise (header + row groups), so chunks stay tabular
  and coherent. Each chunk's metadata records `row_start`/`row_end`, and the
  ingest response's `page_count` carries the data-row count.

```bash
curl -F "file=@report.pdf" \
  "http://localhost:8001/ingest/my-session?strategy=structure_aware"
```

### `POST /search/{session_id}`

```bash
curl -X POST "http://localhost:8001/search/my-session" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key findings?"}'
```

Returns the top-k chunks after reranking, with `candidates_retrieved` vs
`candidates_sent_to_llm`, and per-chunk labeled scores:

```json
{
  "session_id": "my-session",
  "query": "What are the key findings?",
  "results": [
    {
      "text": "…",
      "filename": "report.pdf",
      "page_number": 3,
      "chunk_strategy": "structure_aware",
      "retrieval_scores": {
        "dense_similarity": 0.61,
        "bm25": 8.42,
        "rrf": 0.052,
        "rerank": 0.987
      },
      "confidence": 0.987
    }
  ],
  "candidates_retrieved": 20,
  "candidates_sent_to_llm": 5
}
```

Scores are never blended into one unlabeled number: `dense_similarity` and
`bm25` are raw retrieval-stage scores, `rrf` is the fusion score, and `rerank`
is the cross-encoder relevance score.

### `POST /chat/{session_id}`

Full RAG chat: hybrid retrieval → rerank → LLM generation with citation
verification. Requires an LLM API key — `NVIDIA_API_KEY` with
`LLM_PROVIDER=nvidia` (NVIDIA NIM hosted models) or `OPENROUTER_API_KEY`
(default).

```bash
curl -X POST "http://localhost:8001/chat/my-session" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key findings?"}'
```

Returns the generated `answer` with `[n]` citation markers, the verified
`citations` (chunk id, filename, page, text quote, labeled scores, confidence),
and a `metrics` breakdown (retrieval/rerank/generation/total latency + token
usage). Invalid/out-of-range citation markers from the model are stripped —
fabricated references never reach the UI. Every `/chat` call is also logged to
the JSONL query log with the final answer, citations, and tokens.

### `POST /title`

Short chat title for a query — the sidebar names chats with a meaningful
summary instead of "New chat". Uses an LLM summary (max 16 tokens) when a key
is configured, else a deterministic first-8-words heuristic:

```bash
curl -X POST "http://localhost:8001/title" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key findings?"}'
# {"title": "What are the key findings"}
```

### `GET /documents/{session_id}` and `GET /documents/{session_id}/{filename}`

Back the in-context document viewer: list a session's documents (filename,
title, chunk count, page/row numbers, embedder), and fetch one document's
chunks in document order with page/row labels.

### Document titles

Every ingest response (and each search result / citation) carries a best-effort
`title` for display: PDF `/Title` metadata, DOCX core properties, a Markdown
H1, or a short first line of a `.txt`. The UI prefers it over the raw upload
filename — the storage identifier stays the internal key. `title` is `null`
for CSVs and generic/empty titles, in which case the filename is shown.

### `GET /health`

Returns `{"status": "ok"}`.

## Chat UI

The React app (`frontend/react`) ships a chat interface at `/#/chat`:

- **Multi-session sidebar** — Pinned / Today / Previous 7 days / Previous 30
  days / Older groups, search-by-title-and-content, per-tag colors with
  filtering, and a per-chat quick-action menu (rename, pin, add/remove tag,
  export as JSON, delete). Persisted to localStorage (`knowledge-rag:sessions`).
- **Upload workspace** — glassmorphism dropzone with drag-over micro-animation,
  format + size validation, staged progress driven by the **real backend
  stages** (`?stream=1`): Extracting text… → Chunking document… → Generating
  embeddings… → Indexing… → Ready, plus a metadata preview card (title or
  filename, size, page/row count, chunk count, strategy), and per-upload
  advanced chunk settings.
- **Answers with citations** — inline `[n]` pills open a source drawer showing
  per-chunk filename, page, labeled stage scores (dense/BM25/RRF/rerank),
  confidence %, and the most query-relevant sentence highlighted. Each source
  card's **View in document** action opens a split-screen document viewer that
  renders the full document from its chunks (in order, with page/row labels)
  and scrolls to highlight the cited chunk and its sentence.
- **Dev metrics panel** — collapsible per-answer breakdown of retrieval,
  rerank, generation, and total latency plus token usage.
- **Auto-generated chat titles** — the sidebar names each chat from its first
  uploaded document (title or filename) immediately, then refines it with an
  LLM summary of the first real query. Empty drafts that never receive a
  message or upload are dropped instead of lingering as "New chat" entries.
- **Greeting interceptor** — "hi"/"hello" are answered locally in ~400 ms,
  never hitting the RAG pipeline. All requests use `AbortController` timeouts.

The dev server proxies `/ingest`, `/search`, `/chat`, `/documents`, `/title`,
`/space` to the Python service on `localhost:8001` (set `VITE_API_URL` to
point elsewhere).

**Storage compatibility:** sessions live in localStorage under
`knowledge-rag:sessions`. Newer fields (`pinned`, `tags`) have safe defaults,
so sessions saved by older versions keep working with no migration. On load,
empty drafts (no messages, no files, default title) are filtered out.

## Vector Space Explorer (optional, advanced)

A toggleable **3D view of the session's actual chunk embeddings** — the one
place depth is not decoration: it renders literally what retrieval did with
your query. Click **Vector space** in the header (or open it after asking a
question).

- **Projection — UMAP, not t-SNE.** The backend (`app/space.py`) reduces the
  chunk embeddings (384-dim MiniLM, or whatever `EMBEDDER` produces) to 3D.
  UMAP is deliberate: its fitted model can `.transform()` a **new query
  embedding into the existing map in real time** (t-SNE is non-parametric and
  cannot), and it preserves global cluster structure better — so "which
  document is this cluster" is visible, not just local neighborhoods.
- **Recompute discipline.** The full projection is fitted once per document
  set and cached (recomputed only when chunks are added/removed) — it is
  *never* re-run per query, so points don't jitter between questions. The
  query transform is the only per-query computation (~ms).
- **What's plotted.** Every chunk is a point colored by source document. On a
  chat query, the query embedding drops in as a distinct cyan **tetrahedron**
  (shape, not just color — colorblind-safe); reranked chunks are enlarged and
  linked to it by thin lines, retrieved chunks hold full color, and everything
  else recedes. Clicking any point opens the same citation panel as the chat
  answers (one source of truth, no second chunk UI).
- **Scaling.** Above `UMAP_CLUSTER_THRESHOLD` (default 4000) chunks, points
  are grid-clustered into representative markers sized by cluster count.
  Low-end devices (`hardwareConcurrency <= 4`) automatically get a static 2D
  SVG scatter of the same coordinates instead of a forced 3D experience.
  `prefers-reduced-motion` disables idle auto-rotation. The panel is
  keyboard-navigable (arrow keys select a point, Enter opens it).
- **Bundle discipline.** The three.js / React Three Fiber stack is
  lazy-loaded — it ships as a separate chunk fetched only when the panel
  opens, so it never taxes the main chat bundle.

### `GET /space/{session_id}` and `POST /space/{session_id}/query`

```bash
curl "http://localhost:8001/space/my-session"
# { method: "umap", point_count: 342, clustered: false,
#   points: [{ id, x, y, z, filename }] }

curl -X POST "http://localhost:8001/space/my-session/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the key findings?"}'
# { point: { x, y, z }, promoted_ids: [...], retrieved_ids: [...] }
```

The query endpoint reuses the same `hybrid_search` funnel as `/chat`, so the
promoted/receded styling is driven by the exact scores the LLM saw — no
separate scoring logic. `method` is `umap`, or `pca` when UMAP is unavailable
or the corpus is too small for it.

## Evaluation harness

Every search writes a structured JSONL record (query, retrieved chunk ids +
stage scores, reranked order, citations, latency breakdown) to
`QUERY_LOG_DIR/queries.jsonl`. The eval harness reuses that same pipeline and
scores the retrieval quality on a golden set:

```bash
cd backend/python
source .venv/bin/activate

# Retrieval metrics only (no API key needed)
python -m eval.run_eval --docs ../../eval-docs

# With LLM-as-judge for faithfulness + answer relevance
# export NVIDIA_API_KEY=nvapi-...   # or OPENROUTER_API_KEY=sk-...
python -m eval.run_eval --docs ../../eval-docs --chunk-size 500 --overlap 100 --strategy structure_aware

# Compare without reranking
RERANKER_ENABLED=false python -m eval.run_eval --docs ../../eval-docs

# Filter by query type
python -m eval.run_eval --docs ../../eval-docs --query-type multi_hop
```

Each run ingests the eval corpus into a settings-specific session
(`eval-<chunk_size>-<overlap>-<strategy>`), computes **context precision**,
**context recall** and **recall@pool** from the golden evidence, and — when an
API key is present — **faithfulness** and **answer relevance** via an
LLM-as-judge call. Reports land in `eval/reports/` as `eval_report.json` and
a diffable `eval_report.md`, so chunking/retrieval changes can be compared.
Metrics are computed globally **and** broken out per query type (in the
`by_query_type` summary and a per-query-type table) so that a strong
single-hop score cannot mask weak multi-hop or ambiguous-query behaviour.

### Eval dataset design

The golden set is designed to make retrieval genuinely hard — a large pile of
unrelated documents gives the retriever nothing to confuse it with, which makes
precision look artificially good while telling you nothing.

**Corpus (`eval-docs/`):** 18 documents (~71 chunks at the default 500/100
setting) organised in 6 topical clusters that share vocabulary (data privacy,
product catalogue, engineering ops, HR, contracts, and a two-part platform
report), so the retriever faces real distractors when ranking. The set includes:

- **3 near-duplicate / superseded pairs** (privacy policy v1/v2 with a changed
  retention clause, employee handbook v1/v2 with changed PTO, vendor contract
  v1/v2 with a changed renewal term) to stress-test the reranker — the question
  is whether it picks the *correct* version, not just *a similar* one.
- **Multi-hop material** (a two-part platform report, runbook↔SLA pairs,
  product sheet↔pricing CSV) where the answer requires joining evidence from
  two or more documents, making context recall discriminating rather than
  trivially easy.
- **At least one document per supported format** (.pdf, .txt, .docx, .md, .csv)
  and cross-format clusters (e.g. the Atlas product-sheet PDF references the
  same SKUs as the pricing CSV).

**Golden queries (`eval/golden_set.json`):** 72 queries, each tagged with
a `query_type` label:

| Type | Description | Distinguishing challenge |
| --- | --- | --- |
| `single_hop` | Answer lives in one chunk | Baseline precision/recall |
| `multi_hop` | Answer requires joining ≥ 2 chunks / docs | Context recall, ordering |
| `ambiguous` | Query matches multiple plausible chunks | Reranker + score separation |
| `unanswerable` | Answer is not in the corpus | Faithfulness — must not hallucinate |

> **Why 50–100?** Under ~30 queries, precision/recall numbers are statistical
> noise. More importantly, an aggregate score hides exactly the failure-mode
> breakdown (e.g., strong single-hop, weak multi-hop) that makes the eval worth
> running.

The golden set lives in `backend/python/eval/golden_set.json`; the full
dataset spec — document list, cluster rationale, near-duplicate pairs, and
query authoring guidelines — is in [`EVAL_DATASET.md`](EVAL_DATASET.md).

## QA test plan

[`QA_TEST_PLAN.md`](QA_TEST_PLAN.md) mirrors the original VectorMind 14-scenario
QA matrix, adapted to the current architecture. The automatable scenarios
(ingestion boundaries, multi-format ingestion, chunking, hybrid retrieval,
RRF, session isolation, citation verification, graceful degradation,
observability) are an executable pytest suite:

```bash
cd backend/python
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v
```

The suite is hermetic — stub embedder, reranker disabled, temp Chroma/log
dirs, no network or API keys required. Frontend scenarios (greeting
interceptor, localStorage recovery, network degradation, document viewer)
have step-by-step manual procedures in the plan.

## Benchmarks

Measured with the eval harness on the `eval-docs/` corpus (18 topically
clustered documents across 5 formats — including 3 near-duplicate/superseded
pairs and multi-hop material — expanded to ~71 chunks at the default chunk
size so the retriever faces real distractors) with a 72-query golden set.
Results are broken out by query type so that a strong single-hop score cannot
mask weak multi-hop or ambiguous-query behaviour. **Retrieval latency** is the
full stage breakdown (dense + BM25 + fusion + rerank) on a single CPU machine.
Generation latency and the qualitative metrics require a valid LLM API key
(`OPENROUTER_API_KEY` or `NVIDIA_API_KEY`).

### Representative config — structure_aware · 500/100 · reranker on · pool 20

Measured on the `eval-docs/` corpus (18 documents, 6 topical clusters, 3
near-duplicate pairs, multi-hop material, ~71 chunks) with the 72-query
golden set, `BAAI/bge-reranker-base` reranker, `all-MiniLM-L6-v2` embedder.

| Query type | n | Precision | Recall | Recall@pool | Faithfulness | Ans. relevance |
| --- | --- | --- | --- | --- | --- | --- |
| `single_hop` | 36 | 0.294 | 0.904 | 0.911 | — | — |
| `multi_hop` | 19 | 0.495 | 0.609 | 0.675 | — | — |
| `ambiguous` | 12 | 0.183 | 0.833 | 0.833 | — | — |
| `unanswerable` | 5 | 0.000 | 0.000 | 0.000 | — | — |
| **overall** | 72 | 0.308 | 0.752 | 0.773 | — | — |

> The `unanswerable` row scoring 0/0 is correct: the golden set tags questions
> whose answer is absent from the corpus, so retrieval must surface nothing.
> Faithfulness and answer relevance require an LLM API key and are populated
> when `OPENROUTER_API_KEY`/`NVIDIA_API_KEY` is valid.

### Config comparison (retrieval metrics, no LLM needed)

| Config | Chunking | Reranker | Pool | Precision | Recall | Recall@pool | Latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| fixed · 500/100 | fixed | off | 20 | 0.281 | 0.661 | 0.853 | 26 ms |
| fixed · 500/100 | fixed | on | 20 | 0.286 | 0.694 | 0.853 | ~910 ms |
| structure_aware · 500/100 | structure_aware | on | 20 | 0.308 | 0.752 | 0.773 | ~713 ms |

> Reproduce with: `cd backend/python && python -m eval.run_eval --docs ../../eval-docs`
> (add `--strategy structure_aware`, or `RERANKER_ENABLED=false`, to vary the
> config). Per-config reports land in `eval/reports/` as `eval_report.json`
> (or `bench-<tag>.json` with `--tag <tag>`). Reranker latency is
> steady-state (first-query warmup and the one-time model download excluded).

### Earlier baseline (sample-docs · 16 flat questions)

These numbers were produced on the small bundled sample corpus (aurora-labs.txt,
faq.md, products.csv, data-privacy.md — 9 chunks fixed / 32 structure-aware,
16 golden questions with no query-type tagging). They are kept here as a
regression baseline only — **do not treat them as performance claims**. Re-run
with `python -m eval.run_eval --docs ../../sample-docs` (the harness auto-uses
the archived 16-query golden set for `sample-docs`); values below were
re-measured on the current code (cosine space, whitespace-insensitive matching).

| Config | Chunking | Reranker | Pool | Precision | Recall | Recall@pool | Latency |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | fixed · 500/100 | off | 20 | 0.325 | 0.693 | 1.000 | 19 ms |
| B | structure_aware · 500/100 | off | 20 | 0.213 | 0.432 | 0.984 | 19 ms |
| C | structure_aware · 500/100 | on | 20 | 0.375 | 0.771 | 0.984 | ~1265 ms* |
| D | fixed · 500/100 | on | 20 | 0.425 | 0.859 | 1.000 | ~1054 ms* |
| E | fixed · 250/50 | off | 20 | 0.288 | 0.553 | 1.000 | 18 ms |
| F | fixed · 1000/200 | off | 20 | 0.350 | 0.750 | 1.000 | 17 ms |
| G | structure_aware · 250/50 | off | 20 | 0.250 | 0.516 | 0.974 | 20 ms |
| H | fixed · 500/100 | off | 50 | 0.325 | 0.693 | 1.000 | 23 ms |

*Reranker latencies are steady-state means (first-query warmup ≈7 s, plus the
one-time ≈70 s bge-reranker download, excluded).

**What the baseline shows:**

- **Reranker measurably helps**: lifts recall (fixed 0.693→0.859,
  structure-aware 0.432→0.771) and precision (0.325→0.425,
  0.213→0.375) — invisible on the tiny original corpus where recall was
  already 1.0. Cost: ~1.0–1.3 s/query.
- **`recall@pool` ≥ `recall`**: the wide fused pool catches the evidence; the
  top-5 cut drops it — the funnel is doing its job.
- Fixed edges structure-aware *without* reranking (0.693 vs 0.432 recall);
  reranking closes the gap. Larger chunks (1000/200) give best no-rerank recall
  (0.750). Pool width 20 vs 50 changes nothing here.
- **Why these numbers understate the problem**: 16 untagged questions on four
  unrelated documents gives the retriever no real distractors, so precision
  looks artificially good. The new corpus addresses this.

## Roadmap

- [x] PDF extraction hygiene (page numbers, running headers/footers, glued prefixes) + regression baseline

- [x] Hybrid retrieval with RRF fusion + cross-encoder reranking
- [x] Structure-aware chunking + per-upload chunk settings
- [x] Labeled stage-wise scores in the API
- [x] Per-query JSONL logging (query, candidates, scores, reranked order, latency)
- [x] Evaluation harness (context precision/recall, recall@pool, faithfulness, answer relevance)
- [x] Multi-format ingestion (.pdf, .txt, .docx, .md, .csv)
- [x] Swappable embedding models (MiniLM local, OpenAI via `EMBEDDER`)
- [x] Upload guardrails (size limit, CSV row limit, extension whitelist)
- [x] Chat UI with inline `[n]` citations + source drawer (labeled scores, confidence, highlighted sentences)
- [x] LLM generation stage with citation verification (`/chat`)
- [x] Dev metrics panel (retrieval/rerank/generation latency + token usage)
- [x] Document viewer (click a citation to see the excerpt in-context)
- [x] 3D vector space explorer (UMAP projection, live query drop-in, promoted/receded chunks, 2D fallback)

## License

[MIT](LICENSE)
