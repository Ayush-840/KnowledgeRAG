"""Standalone RAGAS-style evaluation harness.

Usage (from backend/python, in the venv):
    python -m eval.run_eval --docs ../../sample-docs
    python -m eval.run_eval --docs ../../sample-docs --chunk-size 500 --overlap 100 --strategy structure_aware

Metrics per golden question:
  - context precision: relevant chunks in the top-k context / chunks retrieved
  - context recall:    relevant chunks retrieved / all relevant chunks in the corpus
  - recall @ pool:     recall over the wider fused pool (before reranking)
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
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Load .env before any module reads configuration (LLM_PROVIDER, NVIDIA_API_KEY, ...)
load_dotenv()

from app.dependencies import get_session_vectors
from app.observability import log_query, utc_now_iso
from app.retrieval import RETRIEVE_CANDIDATES, RERANK_TOP_K, RERANKER_ENABLED, hybrid_search
from app.utils import ingest_document
from eval import llm as llm_client

DEFAULT_GOLDEN = Path(__file__).parent / "golden_set.json"


def _relevant(text: str, evidence: list) -> bool:
    low = text.lower()
    return any(ev.lower() in low for ev in evidence)


def _mean(values) -> float:
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals), 4) if vals else None


def run_eval(docs_dir: Path, chunk_size: int, overlap: int, strategy: str, out_dir: Path, golden_path: Path):
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    # Ingest txt/md/csv samples (PDFs are excluded here: the sample PDF duplicates the
    # TXT content, which would double-count relevant chunks in the recall denominator).
    docs = sorted(
        list(docs_dir.glob("*.txt"))
        + list(docs_dir.glob("*.md"))
        + list(docs_dir.glob("*.csv"))
    )
    if not docs:
        sys.exit(f"No sample documents (.txt/.md/.csv) found in {docs_dir}")

    # Dedicated session per settings combo so configs can be diffed without cross-contamination
    session_id = f"eval-{chunk_size}-{overlap}-{strategy}"

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
        llm_error = None
        generation_ms = None
        if has_llm:
            try:
                t_gen = time.perf_counter()
                answer = llm_client.generate_answer(q, topk_texts)
                generation_ms = round((time.perf_counter() - t_gen) * 1000, 2)
                faithfulness = llm_client.judge_faithfulness(q, answer, topk_texts)
                answer_relevance = llm_client.judge_answer_relevance(q, answer)
            except Exception as e:  # noqa: BLE001 - keep the rest of the run going
                llm_error = str(e)

        row = {
            "id": g["id"],
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
                "faithfulness": faithfulness,
                "answer_relevance": answer_relevance,
            },
        })

    summary = {
        "context_precision": _mean([r["context_precision"] for r in rows]),
        "context_recall": _mean([r["context_recall"] for r in rows]),
        "recall_at_pool": _mean([r["recall_at_pool"] for r in rows]),
        "faithfulness": _mean([r["faithfulness"] for r in rows]),
        "answer_relevance": _mean([r["answer_relevance"] for r in rows]),
        "mean_generation_ms": _mean([r["generation_ms"] for r in rows]),
        "mean_total_latency_ms": _mean([r["latency_ms"]["total"] for r in rows]),
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
    json_path = out_dir / "eval_report.json"
    md_path = out_dir / "eval_report.md"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")

    print(f"\nReport written to {json_path} and {md_path}")
    print(json.dumps({"summary": summary}, indent=2))


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
        lines.append(f"| {k} | {v if v is not None else 'n/a'} |")

    lines += ["", "### Generation (LLM-as-judge)", "", "| Metric | Mean |", "| --- | --- |"]
    for k in ("faithfulness", "answer_relevance", "mean_generation_ms"):
        v = report["summary"].get(k)
        lines.append(f"| {k} | {v if v is not None else 'n/a'} |")

    lines += ["", "## Per query", "", "| ID | Question | Retrieved | Relevant | Precision | Recall | Recall@pool | Faithfulness | Answer rel. | Latency (ms) |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in report["queries"]:
        lines.append(
            f"| {r['id']} | {r['question']} | {r['retrieved_count']} | {r['relevant_retrieved']} | "
            f"{r['context_precision']} | {r['context_recall']} | {r['recall_at_pool']} | "
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
    args = parser.parse_args()

    docs_dir = args.docs.resolve()
    print(f"Knowledge RAG eval — docs: {docs_dir}")
    run_eval(docs_dir, args.chunk_size, args.overlap, args.strategy, args.out, args.golden)


if __name__ == "__main__":
    main()
