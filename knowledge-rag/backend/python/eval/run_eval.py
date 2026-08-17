"""Standalone RAGAS-style evaluation harness.

Usage (from backend/python, in the venv):
    python -m eval.run_eval --docs ../../sample-docs
    python -m eval.run_eval --docs ../../sample-docs --chunk-size 500 --overlap 100 --strategy structure_aware

Metrics per golden question:
  - context precision: relevant chunks in the top-k context / chunks retrieved
  - context recall:    relevant chunks retrieved / all relevant chunks in the corpus
  - recall @ pool:     recall over the wider fused pool (before reranking)
  - structure:         fast no-LLM pre-check — all three response sections present
                       and body [n] citations resolve to the Citation References section
  - faithfulness:      LLM judge — is the generated answer grounded in the context?
  - answer relevance:  LLM judge — does the answer address the question?

Qualitative metrics need an LLM API key (NVIDIA_API_KEY or OPENROUTER_API_KEY,
selected via LLM_PROVIDER). Retrieval metrics always run. Outputs:
eval_report.json + eval_report.md (diffable across chunking/retrieval settings).

Reranking is controlled by the usual env vars (RERANKER_ENABLED, RERANK_TOP_K,
RETRIEVE_CANDIDATES). Set RERANKER_ENABLED=false to compare without reranking.
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load .env before any module reads configuration (LLM_PROVIDER, NVIDIA_API_KEY, ...)
load_dotenv()

from app.dependencies import get_session_vectors, reset_session
from app.observability import log_query, utc_now_iso
from app.retrieval import RETRIEVE_CANDIDATES, RERANK_TOP_K, RERANKER_ENABLED, hybrid_search
from app.utils import ingest_document
from eval import llm as llm_client

DEFAULT_GOLDEN = Path(__file__).parent / "golden_set.json"


def _relevant(text: str, evidence: list) -> bool:
    """Substring match, insensitive to line wrapping: both sides are
    whitespace-normalized so an evidence phrase split across lines in the
    corpus ("must remain\nbelow 30 minutes") still matches."""
    low = re.sub(r"\s+", " ", text.lower())
    return any(re.sub(r"\s+", " ", ev.lower()) in low for ev in evidence)


def _mean(values) -> float:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def resolve_golden(docs_dir: Path, golden_path: Path) -> Path:
    """Auto-fallback: the bundled sample-docs corpus is tiny and pairs with the
    archived 16-question golden set; the eval-docs corpus (with its 72 tagged
    queries) is meaningless against it. Only triggers when the caller did not
    explicitly pass --golden (the default resolves to eval/golden_set.json)."""
    if golden_path == DEFAULT_GOLDEN and docs_dir.resolve().name == "sample-docs":
        sample_golden = Path(__file__).parent / "golden_set_sample.json"
        if sample_golden.exists():
            print(f"  ℹ️  sample-docs detected — using archived {sample_golden.name} (16 flat queries)")
            return sample_golden
    return golden_path


def run_eval(docs_dir: Path, chunk_size: int, overlap: int, strategy: str, out_dir: Path, golden_path: Path, query_type: str = None, tag: str = None):
    golden_path = resolve_golden(docs_dir, golden_path)
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    if query_type:
        tagged = [g for g in golden if g.get("query_type") == query_type]
        if not tagged and not any("query_type" in g for g in golden):
            print(f"  ⚠️  --query-type {query_type} requested but golden set has no query_type tags — "
                  "running the full set instead.")
        else:
            golden = tagged
            if not golden:
                sys.exit(f"No golden queries of type '{query_type}' found")
        print(f"  filtering to query_type={query_type}: {len(golden)} queries")
    # Ingest all 5 supported formats. (The old sample corpus excluded PDFs because
    # the sample PDF duplicated the TXT content, which would double-count relevant
    # chunks in the recall denominator — the eval-docs corpus has unique content
    # per file, so all formats participate.)
    docs = sorted(
        list(docs_dir.glob("*.txt"))
        + list(docs_dir.glob("*.md"))
        + list(docs_dir.glob("*.csv"))
        + list(docs_dir.glob("*.pdf"))
        + list(docs_dir.glob("*.docx"))
    )
    if not docs:
        sys.exit(f"No sample documents (.txt/.md/.csv) found in {docs_dir}")

    # Dedicated session per settings combo so configs can be diffed without cross-contamination
    session_id = f"eval-{chunk_size}-{overlap}-{strategy}"
    reset_session(session_id)  # a re-run of the same combo starts clean — without
    # this, the persistent collection accumulates duplicate chunks and the
    # reported metrics silently drift from the README baselines.

    for doc in docs:
        print(f"  ingesting {doc.name} (chunk_size={chunk_size}, overlap={overlap}, strategy={strategy})")
        ingest_document(
            session_id, doc.name, str(doc),
            chunk_size=chunk_size, overlap=overlap, strategy=strategy,
        )

    session = get_session_vectors(session_id)
    collection = session["collection"]
    bm25 = session.get("bm25")
    if bm25 is None:
        sys.exit("BM25 index not initialized after ingestion")

    # Corpus scan for total relevant chunks per question
    corpus = collection.get(include=["documents"])
    corpus_texts = corpus["documents"]

    has_llm = llm_client.llm_available()
    print(f"  LLM-as-judge: {'enabled (' + llm_client.JUDGE_MODEL + ')' if has_llm else 'SKIPPED (set NVIDIA_API_KEY or OPENROUTER_API_KEY)'}")
    print(f"  reranker: {'enabled' if RERANKER_ENABLED else 'disabled'}")

    rows = []
    for g in golden:
        q = g["question"]
        out = hybrid_search(
            collection, bm25, q,
            bm25_ids=session.get("bm25_ids"),
            candidates=RETRIEVE_CANDIDATES,
            top_k=RERANK_TOP_K,
        )
        results = out["results"]
        topk_texts = [r["text"] for r in results]
        chunks = [
            {
                "text": r["text"],
                "title": r.get("title"),
                "filename": r["filename"],
                "page_number": r["page_number"],
            }
            for r in results
        ]

        relevant_topk = [r for r in results if _relevant(r["text"], g["evidence"])]
        total_relevant = sum(1 for t in corpus_texts if _relevant(t, g["evidence"]))
        precision = round(len(relevant_topk) / len(results), 4) if results else 0.0
        recall = round(len(relevant_topk) / total_relevant, 4) if total_relevant else 0.0

        # Recall over the wider fused pool (pre-rerank)
        pool_ids = [c["id"] for c in out["fused_pool"]]
        pool_docs = collection.get(ids=pool_ids, include=["documents"])
        pool_relevant = sum(1 for t in pool_docs["documents"] if _relevant(t, g["evidence"]))
        recall_at_pool = round(pool_relevant / total_relevant, 4) if total_relevant else 0.0

        answer = None
        faithfulness = None
        answer_relevance = None
        structure_ok = None
        structure_issues = []
        llm_error = None
        generation_ms = None
        if has_llm:
            try:
                t_gen = time.perf_counter()
                answer = llm_client.generate_answer(q, chunks)
                generation_ms = round((time.perf_counter() - t_gen) * 1000, 2)
                # Cheap structural pre-check before the expensive LLM judges
                structure_ok, structure_issues = llm_client.check_structure(answer, len(chunks))
                faithfulness = llm_client.judge_faithfulness(q, answer, topk_texts)
                answer_relevance = llm_client.judge_answer_relevance(q, answer)
            except Exception as e:  # noqa: BLE001 - keep the rest of the run going
                llm_error = str(e)

        row = {
            "id": g["id"],
            "query_type": g.get("query_type"),
            "question": q,
            "expected_source": g.get("expected_source"),
            "retrieved_count": len(results),
            "relevant_retrieved": len(relevant_topk),
            "total_relevant": total_relevant,
            "context_precision": precision,
            "context_recall": recall,
            "recall_at_pool": recall_at_pool,
            "answer": answer,
            "faithfulness": faithfulness,
            "answer_relevance": answer_relevance,
            "structure_ok": structure_ok,
            "structure_issues": structure_issues,
            "generation_ms": generation_ms,
            "llm_error": llm_error,
            "latency_ms": out["latency_ms"],
        }
        rows.append(row)

        log_query({
            "ts": utc_now_iso(),
            "eval": True,
            "golden_id": g["id"],
            "session_id": session_id,
            "query": q,
            "retrieved": out["fused_pool"],
            "reranked_ids": out["reranked_ids"],
            "candidates_retrieved": out["candidates_retrieved"],
            "candidates_sent_to_llm": out["candidates_sent_to_llm"],
            "final_answer": answer,
            "citations": [{"id": r["id"], "filename": r["filename"], "page_number": r["page_number"]} for r in results],
            "latency_ms": out["latency_ms"],
            "metrics": {
                "context_precision": precision,
                "context_recall": recall,
                "recall_at_pool": recall_at_pool,
                "structure_ok": structure_ok,
                "structure_issues": structure_issues,
                "faithfulness": faithfulness,
                "answer_relevance": answer_relevance,
            },
        })

    summary = {
        "context_precision": _mean([r["context_precision"] for r in rows]),
        "context_recall": _mean([r["context_recall"] for r in rows]),
        "recall_at_pool": _mean([r["recall_at_pool"] for r in rows]),
        "structure_pass_rate": _mean([r["structure_ok"] for r in rows]),
        "faithfulness": _mean([r["faithfulness"] for r in rows]),
        "answer_relevance": _mean([r["answer_relevance"] for r in rows]),
        "mean_generation_ms": _mean([r["generation_ms"] for r in rows]),
        "mean_total_latency_ms": _mean([r["latency_ms"]["total"] for r in rows]),
        # Per-query-type breakdown so a strong single-hop score cannot mask weak
        # multi-hop / ambiguous behaviour (only present when the golden set tags types)
        "by_query_type": _per_query_type_summary(rows),
    }

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "settings": {
            "chunk_size": chunk_size,
            "overlap": overlap,
            "strategy": strategy,
            "retrieve_candidates": RETRIEVE_CANDIDATES,
            "rerank_top_k": RERANK_TOP_K,
            "reranker_enabled": RERANKER_ENABLED,
            "judge_model": llm_client.JUDGE_MODEL,
            "generation_model": llm_client.GENERATION_MODEL,
            "llm_enabled": has_llm,
        },
        "documents": [d.name for d in docs],
        "summary": summary,
        "queries": rows,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"bench-{tag}" if tag else "eval_report"
    json_path = out_dir / f"{stem}.json"
    md_path = out_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    print(f"\nReport written to {json_path} and {md_path}")
    print(json.dumps({"summary": summary}, indent=2))


def _per_query_type_summary(rows: list) -> dict:
    """Mean metrics grouped by g["query_type"] (omits None/untagged rows)."""
    groups = {}
    for r in rows:
        qt = r.get("query_type")
        if not qt:
            continue
        groups.setdefault(qt, []).append(r)
    out = {}
    for qt, g in sorted(groups.items()):
        out[qt] = {
            "n": len(g),
            "context_precision": _mean([r["context_precision"] for r in g]),
            "context_recall": _mean([r["context_recall"] for r in g]),
            "recall_at_pool": _mean([r["recall_at_pool"] for r in g]),
            "structure_pass_rate": _mean([r["structure_ok"] for r in g]),
            "faithfulness": _mean([r["faithfulness"] for r in g]),
            "answer_relevance": _mean([r["answer_relevance"] for r in g]),
        }
    return out


def _render_markdown(report: dict) -> str:
    s = report["settings"]
    lines = [
        "# Knowledge RAG — Evaluation Report",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Documents: {', '.join(report['documents'])}",
        f"- Settings: chunk_size={s['chunk_size']}, overlap={s['overlap']}, strategy={s['strategy']}, "
        f"candidates={s['retrieve_candidates']}, top_k={s['rerank_top_k']}, reranker={s['reranker_enabled']}",
        f"- LLM judge: {s['judge_model']} (enabled={s['llm_enabled']})",
        "",
        "## Summary",
        "",
        "| Metric | Mean |",
        "| --- | --- |",
    ]
    for k, v in report["summary"].items():
        if k == "by_query_type":
            continue
        lines.append(f"| {k} | {v if v is not None else 'n/a'} |")

    by_type = report["summary"].get("by_query_type") or {}
    if by_type:
        lines += ["", "### By query type", "", "| Type | n | Precision | Recall | Recall@pool | Structure | Faithfulness | Ans. rel. |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for qt, m in sorted(by_type.items()):
            lines.append(
                f"| {qt} | {m['n']} | {m['context_precision']} | {m['context_recall']} | {m['recall_at_pool']} | "
                f"{m['structure_pass_rate'] if m['structure_pass_rate'] is not None else 'n/a'} | "
                f"{m['faithfulness'] if m['faithfulness'] is not None else 'n/a'} | "
                f"{m['answer_relevance'] if m['answer_relevance'] is not None else 'n/a'} |"
            )

    lines += ["", "### Generation (LLM-as-judge)", "", "| Metric | Mean |", "| --- | --- |"]
    for k in ("faithfulness", "answer_relevance", "mean_generation_ms"):
        v = report["summary"].get(k)
        lines.append(f"| {k} | {v if v is not None else 'n/a'} |")

    lines += ["", "## Per query", "", "| ID | Type | Question | Retrieved | Relevant | Precision | Recall | Recall@pool | Structure | Faithfulness | Answer rel. | Latency (ms) |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in report["queries"]:
        struct = {True: "✓", False: "✗"}.get(r["structure_ok"], "—")
        lines.append(
            f"| {r['id']} | {r.get('query_type') or '—'} | {r['question']} | {r['retrieved_count']} | {r['relevant_retrieved']} | "
            f"{r['context_precision']} | {r['context_recall']} | {r['recall_at_pool']} | "
            f"{struct} | "
            f"{r['faithfulness'] if r['faithfulness'] is not None else 'n/a'} | "
            f"{r['answer_relevance'] if r['answer_relevance'] is not None else 'n/a'} | "
            f"{r['latency_ms']['total']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Knowledge RAG evaluation harness")
    parser.add_argument("--docs", type=Path, default=Path("../../sample-docs"), help="Directory of sample documents")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN, help="Path to golden_set.json")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "reports", help="Report output directory")
    parser.add_argument("--chunk-size", type=int, default=500, help="Chunk size (words)")
    parser.add_argument("--overlap", type=int, default=100, help="Chunk overlap (words)")
    parser.add_argument("--strategy", type=str, default="fixed", choices=["fixed", "structure_aware"], help="Chunking strategy")
    parser.add_argument("--query-type", type=str, default=None, choices=["single_hop", "multi_hop", "ambiguous", "unanswerable"], help="Only evaluate golden queries of this type")
    parser.add_argument("--tag", type=str, default=None, help="Report filename tag (writes bench-<tag>.json/.md instead of eval_report.*)")
    args = parser.parse_args()

    docs_dir = args.docs.resolve()
    print(f"Knowledge RAG eval — docs: {docs_dir}")
    run_eval(docs_dir, args.chunk_size, args.overlap, args.strategy, args.out, args.golden, query_type=args.query_type, tag=args.tag)


if __name__ == "__main__":
    main()
