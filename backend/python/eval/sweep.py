"""Parameter sweep for retrieval tuning.

Runs eval across a grid of (candidates, top_k, RRF_K) combinations and
produces a comparison report. Usage:

    cd backend/python
    source .venv/bin/activate
    python -m eval.sweep --docs ../../eval-docs --tag sweep-v1

The sweep modifies env vars before each run, resets the session, and
reuses the same golden set. Results land in eval/reports/sweep-v1.*
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Sweep grid: (RETRIEVE_CANDIDATES, RERANK_TOP_K, RRF_K)
# Keep structure_aware + 500/100 as the fixed chunking config (best from benchmarks)
DEFAULT_SWEEP = [
    # Baseline
    (20, 5, 60),
    # Wider candidate pools
    (30, 5, 60),
    (50, 5, 60),
    # Narrower top-k (higher precision expected)
    (20, 3, 60),
    (30, 3, 60),
    (50, 3, 60),
    # Wider top-k (higher recall expected)
    (20, 7, 60),
    (30, 7, 60),
    # RRF_K tuning (lower = more weight on top ranks)
    (30, 5, 40),
    (30, 5, 100),
    (50, 5, 40),
    # Combined best-guess
    (50, 3, 40),
]


def run_single_eval(
    docs_dir: Path,
    golden_path: Path,
    out_dir: Path,
    candidates: int,
    top_k: int,
    rrf_k: int,
    chunk_size: int = 500,
    overlap: int = 100,
    strategy: str = "structure_aware",
    tag: str = None,
):
    """Run one eval configuration by patching env vars and module globals.

    The challenge: run_eval imports RETRIEVE_CANDIDATES/RERANK_TOP_K at module
    load time, so we must patch both the retrieval module (for hybrid_search
    defaults) AND run_eval's local copies (for the values passed to
    hybrid_search). RRF_K is read inside hybrid_search from the module global.
    """
    from app import retrieval
    from eval import run_eval as run_eval_mod

    # Save originals
    old = {
        "retrieval_candidates": retrieval.RETRIEVE_CANDIDATES,
        "rerank_top_k": retrieval.RERANK_TOP_K,
        "rrf_k": retrieval.RRF_K,
    }
    # run_eval imports these at the top: from app.retrieval import RETRIEVE_CANDIDATES, RERANK_TOP_K
    old_re = {
        "candidates": run_eval_mod.RETRIEVE_CANDIDATES,
        "top_k": run_eval_mod.RERANK_TOP_K,
    }

    # Patch both modules
    retrieval.RETRIEVE_CANDIDATES = candidates
    retrieval.RERANK_TOP_K = top_k
    retrieval.RRF_K = rrf_k
    run_eval_mod.RETRIEVE_CANDIDATES = candidates
    run_eval_mod.RERANK_TOP_K = top_k

    try:
        run_eval_mod.run_eval(
            docs_dir,
            chunk_size,
            overlap,
            strategy,
            out_dir,
            golden_path,
            tag=tag,
        )
    finally:
        # Restore originals
        retrieval.RETRIEVE_CANDIDATES = old["retrieval_candidates"]
        retrieval.RERANK_TOP_K = old["rerank_top_k"]
        retrieval.RRF_K = old["rrf_k"]
        run_eval_mod.RETRIEVE_CANDIDATES = old_re["candidates"]
        run_eval_mod.RERANK_TOP_K = old_re["top_k"]


def compare_results(report_dir: Path, tag: str) -> dict:
    """Read all sweep reports and produce a comparison table."""
    import re

    results = []
    # Match files like bench-{tag}-c20_t5_k60.json or sweep-{tag}-c20_t5_k60.json
    pattern = re.compile(r"(?:bench|sweep)-" + re.escape(tag) + r"-c(\d+)_t(\d+)_k(\d+)\.json")
    for f in sorted(report_dir.iterdir()):
        m = pattern.match(f.name)
        if not m:
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        settings = data["settings"]
        summary = data["summary"]
        results.append(
            {
                "file": f.name,
                "candidates": settings["retrieve_candidates"],
                "top_k": settings["rerank_top_k"],
                "rrf_k": int(m.group(3)),
                "precision": summary["context_precision"],
                "recall": summary["context_recall"],
                "recall_at_pool": summary["recall_at_pool"],
                "structure_pass_rate": summary.get("structure_pass_rate"),
                "faithfulness": summary.get("faithfulness"),
                "answer_relevance": summary.get("answer_relevance"),
                "mean_latency_ms": summary.get("mean_total_latency_ms"),
                "by_query_type": summary.get("by_query_type", {}),
            }
        )

    # Sort by precision (primary) then recall (secondary)
    results.sort(key=lambda r: (-r["precision"], -r["recall"]))

    return {"results": results, "generated_at": datetime.now(timezone.utc).isoformat()}


def print_comparison(comparison: dict):
    """Print a readable comparison table."""
    results = comparison["results"]
    if not results:
        print("No results found.")
        return

    print("\n" + "=" * 100)
    print("PARAMETER SWEEP RESULTS — sorted by precision (desc), then recall (desc)")
    print("=" * 100)
    print(
        f"{'Config':<25} {'Prec':>6} {'Recall':>7} {'R@Pool':>7} "
        f"{'Struct':>7} {'Faith':>6} {'Rel':>6} {'Lat(ms)':>8}"
    )
    print("-" * 100)

    baseline = None
    for r in results:
        label = f"c={r['candidates']},t={r['top_k']},k={r['rrf_k']}"
        prec = f"{r['precision']:.4f}" if r["precision"] is not None else "n/a"
        rec = f"{r['recall']:.4f}" if r["recall"] is not None else "n/a"
        rpool = f"{r['recall_at_pool']:.4f}" if r["recall_at_pool"] is not None else "n/a"
        struct = f"{r['structure_pass_rate']:.4f}" if r["structure_pass_rate"] is not None else "n/a"
        faith = f"{r['faithfulness']:.4f}" if r["faithfulness"] is not None else "n/a"
        rel = f"{r['answer_relevance']:.4f}" if r["answer_relevance"] is not None else "n/a"
        lat = f"{r['mean_latency_ms']:.0f}" if r["mean_latency_ms"] is not None else "n/a"

        # Mark baseline
        marker = " ← baseline" if r["candidates"] == 20 and r["top_k"] == 5 and r["rrf_k"] == 60 else ""
        if r["candidates"] == 20 and r["top_k"] == 5 and r["rrf_k"] == 60:
            baseline = r

        print(f"{label:<25} {prec:>6} {rec:>7} {rpool:>7} {struct:>7} {faith:>6} {rel:>6} {lat:>8}{marker}")

    if baseline:
        print("-" * 100)
        print(f"Baseline (c=20,t=5,k=60): precision={baseline['precision']:.4f}, recall={baseline['recall']:.4f}")
        best = results[0]
        if best["precision"] > baseline["precision"]:
            delta_p = best["precision"] - baseline["precision"]
            delta_r = best["recall"] - baseline["recall"]
            print(f"Best config: c={best['candidates']},t={best['top_k']},k={best['rrf_k']}")
            print(f"  Precision: +{delta_p:.4f} ({best['precision']:.4f} vs {baseline['precision']:.4f})")
            print(f"  Recall:    {delta_r:+.4f} ({best['recall']:.4f} vs {baseline['recall']:.4f})")

    print("=" * 100)


def main():
    parser = argparse.ArgumentParser(description="Retrieval parameter sweep")
    parser.add_argument("--docs", type=Path, default=Path("../../eval-docs"))
    parser.add_argument("--golden", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "reports")
    parser.add_argument("--tag", type=str, default="sweep", help="Report tag prefix")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=100)
    parser.add_argument("--strategy", type=str, default="structure_aware")
    parser.add_argument(
        "--configs",
        type=str,
        default=None,
        help='JSON list of [candidates, top_k, rrf_k] triples, e.g. "[[30,3,60],[50,5,40]]"',
    )
    args = parser.parse_args()

    configs = DEFAULT_SWEEP
    if args.configs:
        configs = json.loads(args.configs)

    docs_dir = args.docs.resolve()
    from eval.run_eval import DEFAULT_GOLDEN

    golden_path = (args.golden or DEFAULT_GOLDEN).resolve()
    out_dir = args.out.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Parameter sweep: {len(configs)} configurations")
    print(f"Docs: {docs_dir}")
    print(f"Golden: {golden_path}")
    print(f"Output: {out_dir}")
    print()

    t_start = time.perf_counter()
    for i, (candidates, top_k, rrf_k) in enumerate(configs, 1):
        tag = f"{args.tag}-c{candidates}_t{top_k}_k{rrf_k}"
        print(f"[{i}/{len(configs)}] candidates={candidates}, top_k={top_k}, RRF_K={rrf_k}")
        run_single_eval(
            docs_dir,
            golden_path,
            out_dir,
            candidates=candidates,
            top_k=top_k,
            rrf_k=rrf_k,
            chunk_size=args.chunk_size,
            overlap=args.overlap,
            strategy=args.strategy,
            tag=tag,
        )
        print()

    elapsed = time.perf_counter() - t_start
    print(f"Sweep completed in {elapsed:.1f}s")

    # Comparison
    comparison = compare_results(out_dir, args.tag)
    print_comparison(comparison)

    # Save comparison
    comp_path = out_dir / f"sweep-{args.tag}-comparison.json"
    comp_path.write_text(json.dumps(comparison, indent=2, default=str), encoding="utf-8")
    print(f"\nComparison saved to {comp_path}")


if __name__ == "__main__":
    main()
