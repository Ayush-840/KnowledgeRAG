# Knowledge RAG — Eval Dataset Specification

This document defines the requirements for the evaluation corpus (`eval-docs/`)
and golden query set (`backend/python/eval/golden_set.json`) used by the eval
harness (`python -m eval.run_eval`).

> **Status:** complete. The `eval-docs/` corpus (18 documents, 6 topical
> clusters, 3 near-duplicate pairs, all 5 formats) and the 72-query golden set
> (`eval/golden_set.json`, tagged `single_hop` / `multi_hop` / `ambiguous` /
> `unanswerable`) are committed, and the README Benchmarks table contains
> measured numbers from real runs.

---

## Why this matters

A large pile of *unrelated* documents gives the retriever nothing to confuse it
with, which makes precision look artificially good while telling you nothing.
An aggregate score over a handful of flat questions hides exactly the
failure-mode breakdown (e.g., strong single-hop, weak multi-hop) that makes an
eval worth running. This spec addresses both problems.

---

## 1. Corpus design (`eval-docs/`)

### Size

**15–25 documents total** — enough to create genuine retrieval competition,
small enough to keep golden-set authoring tractable.

### Topical clusters

Documents must be grouped into **3–5 topical clusters** that share vocabulary.
The retriever must rank within a cluster, not just pick from unrelated topics.

| Cluster | Example content | Shared vocabulary pool |
| --- | --- | --- |
| Data privacy | Privacy policy v1, Privacy policy v2 (amended), GDPR FAQ | "data subject", "controller", "retention", "consent" |
| Product catalogue | Product sheet PDF, pricing CSV, feature comparison MD | SKU names, model numbers, specs |
| Engineering ops | Incident runbook TXT, on-call handbook DOCX, SLA document | "escalation", "SLO", "MTTR", "oncall" |
| HR / people | Employee handbook v1, Employee handbook v2 (one clause changed), benefits FAQ | "PTO", "probation", "equity", "handbook" |
| Research / analysis | Two-part technical report (split across two files) | domain-specific terms unique to the report |

Adjust cluster topics to match your actual documents. The constraint is that
**every cluster must contain ≥ 2 documents with overlapping vocabulary**.

### Format coverage

At least one document per supported ingest format:

| Format | Min count |
| --- | --- |
| `.pdf` | 1 |
| `.txt` | 1 |
| `.docx` | 1 |
| `.md` | 1 |
| `.csv` | 1 |

Include ≥ 1 **cross-format cluster pair** (e.g., a policy PDF and a CSV that
references its section numbers) to test multi-format multi-hop retrieval.

### Near-duplicate pairs

Include **2–3 near-duplicate / superseded pairs**. Each pair consists of:

- **Document A**: the original version.
- **Document B**: a revised version differing in ≥ 1 clause, figure, or
  row, while sharing most vocabulary and structure with A.

The golden query for this pair asks about the *changed* clause, expecting
Document B as the ground-truth chunk and Document A as the distractor. This
directly tests whether the reranker picks the *correct* version, not just *a
similar* one.

**Example pair (data-privacy cluster):**

```
data-privacy-v1.md  — "Retention period: 36 months"
data-privacy-v2.md  — "Retention period: 24 months (updated 2025-01)"
```

Golden query: `"What is the current data retention period?"`  
Expected chunk: from `data-privacy-v2.md`  
Common distractor: from `data-privacy-v1.md`

### Multi-hop material

Include **3–5 multi-hop document pairs or triples** where answering a query
requires joining evidence from ≥ 2 documents/chunks:

- **Pointer–content pattern:** Document A names an entity (e.g., a product
  model number); Document B contains the specs for that model.
- **Claim–evidence pattern:** Document A makes a claim; Document C provides the
  underlying data that supports or refutes it.
- **Sequential pattern:** Part 1 and Part 2 of a report where the conclusion
  draws from both sections.

Each multi-hop pair/triple must have a corresponding `multi_hop` golden query.

---

## 2. Golden query set (`eval/golden_set.json`)

### Size

**50–100 queries total**. The distribution should be approximately:

| Type | Recommended share | Rationale |
| --- | --- | --- |
| `single_hop` | ~40% | Establishes the baseline; must pass before multi-hop is meaningful |
| `multi_hop` | ~30% | Core discriminator for context recall |
| `ambiguous` | ~20% | Tests reranker score separation and confidence calibration |
| `unanswerable` | ~10% | Tests faithfulness — the system must decline, not hallucinate |

Under ~30 queries, precision/recall numbers are statistical noise. More
importantly, an aggregate score hides the failure-mode breakdown that makes the
eval useful.

### Schema

Each entry in `golden_set.json` follows this schema:

```jsonc
{
  "id": "q001",
  "query": "What is the current data retention period?",
  "query_type": "single_hop",          // single_hop | multi_hop | ambiguous | unanswerable
  "golden_chunks": [                    // list of chunk identifiers (filename + approximate content anchor)
    {
      "filename": "data-privacy-v2.md",
      "content_anchor": "Retention period: 24 months"   // substring that must appear in the chunk
    }
  ],
  "distractor_chunks": [               // optional — files the retriever must NOT rank above golden
    { "filename": "data-privacy-v1.md", "content_anchor": "Retention period: 36 months" }
  ],
  "notes": "Near-duplicate pair test — v2 supersedes v1."
}
```

For `unanswerable` queries, `golden_chunks` is empty (`[]`) and the expected
behaviour is that the generated answer declines to answer rather than fabricating
a response (faithfulness score = 1.0, answer relevance ≈ 0).

### Query authoring rules by type

#### `single_hop`

- The answer must be fully contained in a **single chunk**.
- Use direct, unambiguous phrasing — these are your baseline; if single-hop
  fails, multi-hop results are meaningless.
- Cover every document in the corpus with ≥ 1 query so that ingest bugs are
  caught.

#### `multi_hop`

- The answer **cannot** be inferred from any single chunk in isolation.
- Explicitly identify which chunks must be retrieved together and record them in
  `golden_chunks`.
- Prefer bridge-entity phrasing: "What is the SLO for the service described in
  the incident runbook?" (runbook names the service; SLA doc defines the SLO).

#### `ambiguous`

- The query lexically matches ≥ 2 chunks, but only one is the intended answer.
- The ambiguity must arise from shared vocabulary, not a typo or bad phrasing.
- Record the intended chunk as `golden_chunks[0]` and the plausible distractor
  in `distractor_chunks`.
- Example: "What changed in the last policy update?" when both v1→v2 and a
  separate amendment exist.

#### `unanswerable`

- The query is **entirely absent from the corpus** — not just hard to find.
- Good sources: ask about a product that is not in the catalogue, a date that
  is not mentioned, or a person not referenced anywhere.
- Avoid trick questions where the answer is technically present but obscure —
  those belong in `ambiguous`.
- The eval harness checks that the generated answer does not assert a fact
  (faithfulness judge prompt: "Does the answer claim to answer the question
  using information not present in the context?").

---

## 3. Authoring checklist

Before committing the corpus and golden set, verify:

- [ ] 15–25 documents in `eval-docs/`
- [ ] ≥ 3 topical clusters, each with ≥ 2 vocabulary-overlapping docs
- [ ] ≥ 1 file per supported format (.pdf, .txt, .docx, .md, .csv)
- [ ] 2–3 near-duplicate/superseded pairs with `distractor_chunks` in the golden set
- [ ] 3–5 multi-hop pairs/triples with `multi_hop` queries covering each
- [ ] 50–100 total queries meeting the type distribution above
- [ ] Every document covered by ≥ 1 `single_hop` query
- [ ] `golden_chunks[].content_anchor` verified against the actual ingest output
- [ ] `unanswerable` queries confirmed absent from the corpus

---

## 4. Running the eval against this corpus

```bash
cd backend/python
source .venv/bin/activate

# All query types, default config
python -m eval.run_eval --docs ../../eval-docs

# Single query type
python -m eval.run_eval --docs ../../eval-docs --query-type multi_hop

# Ablation: no reranker
RERANKER_ENABLED=false python -m eval.run_eval --docs ../../eval-docs

# With LLM judge (faithfulness + answer relevance; needed for unanswerable)
export NVIDIA_API_KEY=nvapi-...   # or OPENROUTER_API_KEY=sk-...
python -m eval.run_eval --docs ../../eval-docs --chunk-size 500 --overlap 100 --strategy structure_aware

# Named benchmark report (writes bench-<tag>.json/.md)
python -m eval.run_eval --docs ../../eval-docs --tag fixed-500-100-rerank
```

Reports land in `eval/reports/eval_report.json` and `eval/reports/eval_report.md`
(or `bench-<tag>.json/.md` with `--tag`), broken out globally and per
`query_type` in the `by_query_type` summary. The committed benchmark runs live
in `eval/reports/bench-*-evaldocs.*`. The old sample-docs golden set (16
untagged queries) is preserved at `eval/golden_set_sample.json` for
reproducing the README's earlier baseline.

---

*Last updated: 2026-08-16*
