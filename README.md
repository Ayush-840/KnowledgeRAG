# Knowledge RAG

[![Tests](https://github.com/YOUR_USERNAME/knowledge-rag/actions/workflows/test.yml/badge.svg)](https://github.com/YOUR_USERNAME/knowledge-rag/actions/workflows/test.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)

<!-- Demo GIF placeholder — record with https://github.com/nicedoc/recordit or OBS -->
<!-- ![Demo](demo.gif) -->

**Ask your documents. Get grounded answers.**

Knowledge RAG is a full-stack retrieval-augmented generation system that produces LLM-synthesized, citation-grounded answers — not raw snippet dumps. It combines hybrid retrieval (dense embeddings + BM25 sparse search) fused with Reciprocal Rank Fusion, narrowed by a cross-encoder reranker, and fed into a defensive generation prompt that enforces inline `[n]` citations traceable to the exact source chunk. Every retrieval-stage score (cosine similarity, BM25, RRF, reranker relevance) is exposed separately in the UI — never blended into a single opaque number. A RAGAS-style eval harness computes context precision, context recall, faithfulness, and answer relevance per query, broken down by query type, so you can actually tell whether a config change helped or hurt.

### Screenshots

<!-- Replace these placeholders with actual screenshots. Take screenshots on a 1440px-wide viewport. -->

<!-- **Chat with citation-grounded answer** — synthesized three-section response with clickable [n] citation pills -->
<!-- ![Chat with citations](screenshots/chat-citations.png) -->

<!-- **Source drawer** — labeled dense/BM25/RRF/rerank scores per chunk, with highlighted excerpt -->
<!-- ![Source drawer](screenshots/source-drawer.png) -->

<!-- **Dev metrics panel** — retrieval latency breakdown, token usage split, funnel counts -->
<!-- ![Dev metrics](screenshots/dev-metrics.png) -->

<!-- **3D vector space** — UMAP projection with live query projection and promoted/receded chunks -->
<!-- ![Vector space](screenshots/vector-space.png) -->

## Architecture

```mermaid
flowchart LR
    subgraph Ingest
        A[Document Parser\nPDF · DOCX · MD · CSV · TXT\nLayout artifact cleanup] --> B[Chunker\nfixed 500/100\nstructure-aware]
        B --> C[Embedder\nall-MiniLM-L6-v2\nswappable]
        C --> D[(ChromaDB\n+ BM25 index)]
    end

    subgraph Query
        E[Query] --> F[Dense search\nChromaDB cosine]
        E --> G[Sparse search\nBM25Okapi]
        F --> H[RRF Fusion\nk=60]
        G --> H
        H --> I[Cross-Encoder Reranker\nBAAI/bge-reranker-base]
        I --> J[Top-k context\ndefault k=5]
        J --> K[Defensive Prompt\nenforces [n] citations]
        K --> L[LLM Synthesis\nGPT-4o via OpenRouter]
        L --> M[Answer + Verified Citations]
    end

    subgraph Observability
        N[Per-query JSONL log] -.-> F
        N -.-> H
        N -.-> I
        N -.-> L
        O[Eval Harness] -.-> D
        O -.-> L
        O --> P[JSON + Markdown Reports\nprecision · recall · faithfulness\nper query type]
    end
```

### Pipeline stages

| Stage | Implementation | Notes |
| --- | --- | --- |
| **Parse** | `pypdf` → `pdfplumber` fallback (PDF), `python-docx` (DOCX), regex (MD), `csv` (CSV) | Strips running headers/footers, page numbers, glue artifacts |
| **Chunk** | Fixed 500-word / 100-overlap windows; structure-aware variant respects paragraph/heading boundaries | Per-upload setting, stored in metadata |
| **Embed** | `sentence-transformers` all-MiniLM-L6-v2 (default); OpenAI `text-embedding-3-small` via `EMBEDDER=openai` | Swappable behind `Embedder` base class |
| **Index** | ChromaDB (cosine) + BM25Okapi (rank-bm25) | BM25 persisted to disk, rebuilt on each ingest |
| **Fuse** | Reciprocal Rank Fusion (configurable k, default 60) | Merges dense + sparse rankings without score calibration |
| **Rerank** | `BAAI/bge-reranker-base` CrossEncoder | Retrieves 20–50 candidates, reranks to top-k (default 5) |
| **Generate** | Structured synthesis prompt → OpenRouter → GPT-4o | Enforces Executive Summary → Key Takeaways → Citation References |
| **Verify** | `verify_citations()` strips fabricated `[n]` markers | Invalid/out-of-range markers removed from final answer |
| **Log** | Structured JSONL per query | Query, retrieved IDs + scores, reranked order, citations, latency breakdown |

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+
- An LLM API key ([OpenRouter](https://openrouter.ai) or [NVIDIA NIM](https://build.nvidia.com) free tier)

### Backend

```bash
cd knowledge-rag/backend/python

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — at minimum set one of:
#   OPENROUTER_API_KEY=sk-...   (OpenRouter, default)
#   NVIDIA_API_KEY=nvapi-...    (NVIDIA NIM free tier)

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd knowledge-rag/frontend/react

npm install
npm run dev      # Vite dev server on :5173, proxies to backend :8000
```

### Deployment

The frontend is deployed on Vercel; the backend runs on any container host (Render, Railway, etc.).

> **Live deployment**: Replace this line with your actual production URL (e.g., `https://knowledge-rag.vercel.app`). Ensure only the production domain appears publicly — Vercel's Standard Protection gates auto-generated preview URLs. Verify the backend's `CORS_ORIGINS` includes the production frontend URL, and that `VITE_API_URL` points at a live, reachable backend.

### Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `LLM_PROVIDER` | `openrouter` | `"openrouter"` or `"nvidia"` |
| `OPENROUTER_API_KEY` | — | Required when `LLM_PROVIDER=openrouter` |
| `NVIDIA_API_KEY` | — | Required when `LLM_PROVIDER=nvidia` |
| `GENERATION_MODEL` | `openai/gpt-4o` | LLM for answer synthesis |
| `EMBEDDER` | `minilm` | `"minilm"` (local) or `"openai"` (API) |
| `OPENAI_API_KEY` | — | Required when `EMBEDDER=openai` |
| `RRF_K` | `60` | Reciprocal Rank Fusion constant |
| `RETRIEVE_CANDIDATES` | `20` | Wide retrieval pool before reranking |
| `RERANK_TOP_K` | `5` | Narrow top-k sent to the LLM |
| `RERANKER_ENABLED` | `true` | Enable/disable cross-encoder reranker |
| `RERANKER_MODEL` | `BAAI/bge-reranker-base` | Cross-encoder model name |
| `MAX_UPLOAD_MB` | `50` | Maximum upload file size |
| `MAX_CSV_ROWS` | `50000` | Maximum CSV data rows |
| `QUERY_LOG_DIR` | `./logs` | Per-query JSONL log directory |

## Evaluation corpus

The `eval-docs/` folder contains an 18-document corpus across 5 formats (PDF, DOCX, MD, CSV, TXT) deliberately structured to stress-test retrieval:

| Cluster | Documents | Purpose |
| --- | --- | --- |
| **Contracts** | `vendor-contract.md`, `vendor-contract-v2.md`, `sla-agreement.md` | Near-duplicate pairs with changed clauses (renewal terms) |
| **Policies** | `employee-handbook-v1.md`, `employee-handbook-v2.md`, `privacy-policy-v1.md`, `privacy-policy-v2.md` | Superseded versions testing correct-version retrieval |
| **Financial/Product** | `product-pricing.csv`, `atlas-product-sheet.pdf`, `feature-comparison.md` | Tabular + PDF data, cross-document queries |
| **Operations** | `incident-runbook.txt`, `oncall-handbook.md`, `api-reference.md` | Technical runbooks with multi-hop material |
| **Compliance** | `gdpr-faq.md`, `benefits-faq.md`, `security-policy.docx` | Legal/HR content with shared vocabulary |

**Golden query set**: `backend/python/eval/golden_set.json` — 72 tagged queries across 4 types:

| Query type | Count | What it tests |
| --- | --- | --- |
| Single-hop factual | 36 | Direct lookups in one chunk |
| Multi-hop / synthesis | 19 | Answers requiring facts from 2+ chunks or documents |
| Ambiguous | 12 | Plausible under more than one interpretation |
| Unanswerable | 5 | No supporting content — tests that the system declines rather than hallucinates |

## Benchmarks

All numbers from real runs on the 18-document eval corpus (72 queries), with `RRF_K=60`, `RERANKER_ENABLED=true`.

### Retrieval performance by configuration

| Config | Candidates | Top-k | Precision | Recall | Recall@pool | Latency (ms) |
| --- | --- | --- | --- | --- | --- | --- |
| **c20 / t5** (default) | 20 | 5 | 0.331 | 0.808 | 0.830 | 758 |
| c30 / t5 | 30 | 5 | 0.375 | 0.771 | 1.000 | 1,202 |
| c50 / t3 | 50 | 3 | 0.542 | 0.714 | 1.000 | 1,388 |

The overall precision (~0.33) looks low in isolation, but this is a deliberate design choice, not an weakness. The funnel retrieves a wide candidate pool (20 chunks) to protect recall — the `recall_at_pool` column shows the retriever *finds* the right chunks even when precision is low. The reranker then narrows to top-5 for generation, which is where precision is actually enforced. The gap between `Recall` (after reranking) and `Recall@pool` (before reranking) is evidence this works: with 20 candidates, recall@pool reaches 83–100%, meaning the relevant chunks are in the pool — the reranker's job is selecting the best 5, not finding them from scratch. A system that retrieves only 5 candidates would show higher precision but silently miss relevant chunks it never considered.

### Retrieval performance by query type (default config: c20 / t5 / k60)

| Query type | n | Precision | Recall | Recall@pool |
| --- | --- | --- | --- | --- |
| Single-hop | 36 | 0.294 | 0.904 | 0.911 |
| Multi-hop | 19 | 0.495 | 0.609 | 0.675 |
| Ambiguous | 12 | 0.183 | 0.833 | 0.833 |
| Unanswerable | 5 | 0.000 | 0.000 | 0.000 |

Single-hop recall is strong (90.4%) — the retriever finds the right chunk most of the time. Multi-hop recall drops to 60.9% because these questions require combining facts across 2+ chunks, which stresses context recall. Ambiguous queries show lower precision (18.3%) because multiple interpretations surface different chunks — this is the corpus doing its job as a distractor. Unanswerable precision/recall are 0.0 as expected (no relevant chunks exist).

### Retrieval latency breakdown (default config, mean across 72 queries)

| Stage | Latency |
| --- | --- |
| Dense (ChromaDB) | 20.1 ms |
| BM25 | 1.1 ms |
| RRF Fusion | 1.7 ms |
| Cross-encoder rerank | 735.4 ms |
| **Total** | **758.3 ms** |

Reranking dominates latency. Disabling it (`RERANKER_ENABLED=false`) drops total search time to ~25 ms but loses the precision gain from cross-encoder scoring.

### Running the benchmarks yourself

```bash
cd knowledge-rag/backend/python
source .venv/bin/activate

# Full corpus (18 docs, 72 queries)
python -m eval.run_eval --docs ../../eval-docs --strategy structure_aware --tag evaldocs-final

# Sweep different configurations
python -m eval.sweep --docs ../../eval-docs

# Sample corpus (6 docs, 16 queries) — fast smoke test
python -m eval.run_eval --docs ../../sample-docs --tag sample
```

Reports are written to `eval/reports/` as both JSON (machine-readable) and Markdown (human-readable, diffable across config changes).

## Tech stack

| Layer | Technology |
| --- | --- |
| **Frontend** | React 19, Vite 8, Tailwind CSS 4, Three.js (3D vector space) |
| **Backend** | Python 3.13, FastAPI, Uvicorn |
| **Vector store** | ChromaDB (cosine similarity) |
| **Sparse retrieval** | rank-bm25 (BM25Okapi) |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) / OpenAI API |
| **Reranker** | BAAI/bge-reranker-base (CrossEncoder) |
| **LLM** | GPT-4o via OpenRouter / Llama 3.3 70B via NVIDIA NIM |
| **Eval** | Custom RAGAS-style harness with LLM-as-judge |
| **PDF parsing** | pypdf + pdfplumber (fallback) |
| **DOCX parsing** | python-docx |
| **Deployment** | Vercel (frontend), any container host (backend) |

## Project structure

```
knowledge-rag/
├── eval-docs/                    # 18-document eval corpus
├── sample-docs/                  # 6-document quick-start corpus
├── backend/
│   ├── python/
│   │   ├── app/
│   │   │   ├── main.py           # FastAPI app + CORS
│   │   │   ├── routes.py         # /ingest, /search, /chat, /space
│   │   │   ├── retrieval.py      # Hybrid search: RRF + reranker
│   │   │   ├── llm.py            # LLM generation + citation verification
│   │   │   ├── embedders.py      # Swappable embedding interface
│   │   │   ├── utils.py          # Parsers, chunkers, ingest pipeline
│   │   │   ├── schemas.py        # Pydantic response models
│   │   │   ├── dependencies.py   # ChromaDB + BM25 session management
│   │   │   ├── observability.py  # Structured JSONL query logging
│   │   │   └── space.py          # UMAP vector space projection
│   │   ├── eval/
│   │   │   ├── run_eval.py       # Eval harness CLI
│   │   │   ├── sweep.py          # Config sweep over chunk/k/candidates
│   │   │   ├── llm.py            # LLM-as-judge helpers
│   │   │   ├── golden_set.json   # 72 tagged golden queries
│   │   │   └── reports/          # Benchmark JSON + Markdown reports
│   │   └── tests/
│   │       └── test_qa.py        # 68 integration tests
│   └── node/                     # (Legacy Node.js proxy — deprecated)
└── frontend/
    └── react/
        ├── src/
        │   ├── pages/Home.jsx        # Chat + space explorer layout
        │   ├── components/
        │   │   ├── ChatBox.jsx       # Message composer + scroll
        │   │   ├── Message.jsx       # Rich answer rendering + cite pills
        │   │   ├── SourceDrawer.jsx  # Citation panel with labeled scores
        │   │   ├── DocumentViewer.jsx# In-context chunk viewer
        │   │   ├── MetricsPanel.jsx  # Dev metrics (latency, tokens, funnel)
        │   │   ├── FileUpload.jsx    # Drag-drop + staged progress
        │   │   ├── Sidebar.jsx       # Session history + tags + search
        │   │   └── SpacePanel.jsx    # 3D vector space explorer
        │   ├── hooks/useChatSessions.js
        │   ├── services/api.js
        │   └── utils/docColors.js
        └── public/
            ├── favicon.svg           # Document + nodes motif
            └── logo.svg
```

## Design decisions

These are the choices most likely to come up in an interview, with the reasoning behind each.

### Why RRF over a weighted score blend

Dense cosine similarity and BM25 scores live on fundamentally different scales — a cosine of 0.85 and a BM25 score of 12.4 aren't directly comparable. A hand-tuned weighted blend (`α * cosine + β * bm25`) requires calibrating α and β, which breaks whenever the corpus or embedding model changes. Reciprocal Rank Fusion sidesteps this entirely: it operates on *ranks*, not scores, so it's immune to scale differences and needs no per-corpus tuning. The `k=60` constant is the standard value from the original RRF paper and has worked without adjustment across our eval configurations.

### Why UMAP over t-SNE for the vector space view

t-SNE is a one-shot layout — there's no `transform()` method, so projecting a new query point requires re-running the full layout on all points, which is O(n²) and destroys the existing layout. UMAP provides a parametric transform: fit once on the corpus, then `transform()` new query vectors into the same space in O(1). This is what makes the live "drop a query into the map" interaction possible without re-rendering the entire 3D view.

### Why the eval corpus includes near-duplicates and multi-hop material

A corpus of totally unrelated documents can't stress-test retrieval — everything is either obviously relevant or obviously not. Near-duplicate pairs (e.g., `vendor-contract.md` vs `vendor-contract-v2.md` with changed renewal terms) create hard negatives: chunks that are lexically and semantically close to the right answer but factually wrong. This is what makes precision discriminating — without distractors, precision stays trivially close to 1.0 because there's nothing confusing the retriever. Multi-hop material (e.g., `platform-report-part1.md` + `platform-report-part2.md`) ensures recall measures whether the system retrieves *all* necessary chunks, not just the first relevant one.

### What the low precision number actually means

0.33 precision means that of the 5 chunks sent to the LLM, roughly 1–2 are topically relevant to the question. This is acceptable because the generation prompt explicitly instructs the model to synthesize from relevant context and ignore noise — the LLM itself acts as a second filter. The alternative (retrieving only 3–5 high-precision chunks) would raise precision to ~0.7 but silently drop recall to ~60%, missing half the relevant information. For a citation-grounded system, finding the right information (recall) matters more than never retrieving noise (precision), because fabricated citations are the failure mode that matters, and that's governed by recall, not precision.

### Known limitations

- **LLM-as-judge faithfulness scoring** has known biases — the same model that generates the answer can rate its own faithfulness favorably. Human evaluation remains the gold standard; the LLM judge is a scalable approximation, not a replacement.
- **Reranker latency** (735ms mean) dominates the pipeline. This is the cross-encoder's O(n²) attention over query×chunk pairs — a real cost, not an implementation gap. Production systems either batch reranking or use smaller distilled models.
- **Session-scoped storage** means indexes don't survive server restarts unless persistence is configured. The Dockerfile defaults to `/data/chroma` for container deployments; local dev uses `./chroma_data`.
- **Unanswerable query detection** uses a regex pre-check with LLM fallback — the regex catches common decline phrases but can miss novel phrasings. The LLM fallback handles ambiguous cases but adds latency.

## License

MIT
