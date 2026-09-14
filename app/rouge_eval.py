"""Score candidate texts (the RAG answers) against references with ROUGE-1/2/L.

    python rouge_eval.py --reference ref.txt --candidate cand.txt   # one pair
    python rouge_eval.py --csv pairs.csv    # many, from 'reference'/'candidate' cols
"""

import argparse
import csv
import json
import sys

from rouge_score import rouge_scorer

METRICS = ["rouge1", "rouge2", "rougeL", "rougeLsum"]


def print_scores(label, scores):
    print(label)
    for m in METRICS:
        s = scores[m]
        print(f"  {m:<7} precision={s.precision:.4f}  recall={s.recall:.4f}  f1={s.fmeasure:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Compute ROUGE-1/2/L between reference and candidate texts")
    parser.add_argument("--reference", help="path to a plain-text file with the reference text")
    parser.add_argument("--candidate", help="path to a plain-text file with the candidate text")
    parser.add_argument("--csv", help="path to a CSV with 'reference' and 'candidate' columns")
    parser.add_argument("--json", dest="json_out", help="also save per-row and average scores to this JSON file")
    args = parser.parse_args()

    scorer = rouge_scorer.RougeScorer(METRICS, use_stemmer=True)

    if args.csv:
        with open(args.csv, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows or "reference" not in rows[0] or "candidate" not in rows[0]:
            sys.exit("CSV must have 'reference' and 'candidate' columns")

        sums = {m: {"precision": 0.0, "recall": 0.0, "fmeasure": 0.0} for m in METRICS}
        per_row = []
        for i, row in enumerate(rows, start=1):
            scores = scorer.score(row["reference"], row["candidate"])
            print_scores(f"[pair {i}]", scores)
            per_row.append({
                "query": row.get("query", ""),
                **{m: {"precision": round(scores[m].precision, 4),
                       "recall": round(scores[m].recall, 4),
                       "f1": round(scores[m].fmeasure, 4)} for m in METRICS},
            })
            for m in METRICS:
                sums[m]["precision"] += scores[m].precision
                sums[m]["recall"] += scores[m].recall
                sums[m]["fmeasure"] += scores[m].fmeasure

        n = len(rows)
        print(f"\n=== averages over {n} pairs ===")
        for m in METRICS:
            print(
                f"  {m:<7} precision={sums[m]['precision'] / n:.4f}  "
                f"recall={sums[m]['recall'] / n:.4f}  f1={sums[m]['fmeasure'] / n:.4f}"
            )

        if args.json_out:
            averages = {m: {"precision": round(sums[m]["precision"] / n, 4),
                            "recall": round(sums[m]["recall"] / n, 4),
                            "f1": round(sums[m]["fmeasure"] / n, 4)} for m in METRICS}
            with open(args.json_out, "w", encoding="utf-8") as jf:
                json.dump({"source": args.csv, "n_pairs": n, "averages": averages, "per_row": per_row},
                          jf, indent=2, ensure_ascii=False)
            print(f"\nsaved scores to {args.json_out}")
    elif args.reference and args.candidate:
        with open(args.reference, encoding="utf-8") as f:
            reference = f.read()
        with open(args.candidate, encoding="utf-8") as f:
            candidate = f.read()
        print_scores("scores", scorer.score(reference, candidate))
    else:
        parser.print_help()
        sys.exit("\nprovide either --csv, or both --reference and --candidate")


if __name__ == "__main__":
    main()
