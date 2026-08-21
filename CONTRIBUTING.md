# Contributing to Knowledge RAG

Thanks for your interest in contributing. Here's how to get started.

## Development setup

### Backend

```bash
cd backend/python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Edit .env — set at least one LLM API key (OPENROUTER_API_KEY or NVIDIA_API_KEY)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend/react
npm install
npm run dev    # Vite dev server on :5173, proxies to backend :8000
```

## Running tests

```bash
cd backend/python
python -m pytest tests/ -v
```

Tests are hermetic — they don't require an LLM key or network access. They validate parsing, chunking, retrieval, and API contract correctness against synthetic documents.

## Running the eval harness

```bash
cd backend/python
source .venv/bin/activate

# Quick smoke test (6 docs, 16 queries)
python -m eval.run_eval --docs ../../sample-docs --tag sample

# Full eval (18 docs, 72 queries) — requires an LLM key for judge
python -m eval.run_eval --docs ../../eval-docs --strategy structure_aware --tag evaldocs-final

# Config sweep
python -m eval.sweep --docs ../../eval-docs
```

Reports land in `eval/reports/` as JSON and Markdown.

## Project conventions

- **One feature or fix per commit.** Keep commits small and descriptive.
- **Don't touch the retrieval architecture** (RRF fusion, reranker, chunking strategies) or eval harness design unless the change is explicitly about improving them. These are the strongest parts of the project.
- **Python:** 3.13+, type hints, `ruff`-style formatting.
- **React:** Functional components, hooks, Tailwind CSS.

## Adding screenshots

See [screenshots/README.md](screenshots/README.md) for how to record and save demo screenshots.

## Submitting changes

1. Fork the repo and create a feature branch.
2. Make your changes with descriptive commits.
3. Run the test suite: `python -m pytest tests/ -v`
4. Open a PR against `main` with a clear description of what changed and why.
