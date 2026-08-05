"""Builds the reference/candidate pairs that rouge_eval.py scores (DYP-48).

Takes articles the scrapers already collected, asks the RAG pipeline about each
one, and writes a CSV holding both texts side by side:

    reference  the source article (title + body) the question was derived from
    candidate  the answer the system produced for that question

ROUGE then measures how much of the source material survives into the answer.
Latency and the links the system cited are recorded in the same row, so the CSV
also carries the numbers for the performance and citation sections.

Run from the app/ directory:
    python build_eval_pairs.py                 # 10 articles, one per source in turn
    python build_eval_pairs.py --n 20          # more pairs
    python build_eval_pairs.py --queries q.txt # own questions, one per line

Then:
    python rouge_eval.py --csv eval_pairs.csv
"""

import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path

import openai
from dotenv import load_dotenv

# retriever reads OPENAI_APIKEY at call time, so the env has to be in place first
load_dotenv(dotenv_path=".env")

import retriever  # noqa: E402  (must follow load_dotenv)

SOURCES_DIR = Path(__file__).resolve().parent.parent / "scrapers" / "scrapers"

# csv module refuses very long fields by default; article bodies exceed the limit
csv.field_size_limit(10_000_000)


def lead_3(text):
    """The article's first three sentences — the standard cheap summarisation
    baseline (Hugging Face LLM course, ch. 7). News writing front-loads the facts,
    so this is a genuinely hard baseline to beat and it costs nothing to produce.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:3])


def no_retrieval_answer(question, model="gpt-4.1-mini"):
    """Same question, same model, no retrieved context — isolates what retrieval
    actually contributes. The model can only fall back on its training data.
    """
    client = openai.OpenAI(api_key=os.getenv("OPENAI_APIKEY"))
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a cybersecurity news assistant. Answer the user's question."},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


def write_pairs(path, rows, candidate_key):
    """Two-column CSV in the shape rouge_eval.py expects."""
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["reference", "candidate"])
        writer.writeheader()
        for r in rows:
            writer.writerow({"reference": r["reference"], "candidate": r[candidate_key]})


def load_articles():
    """Every scraped article, interleaved across sources so a sample stays mixed."""
    per_source = []
    for csv_path in sorted(SOURCES_DIR.glob("*/output.csv")):
        with csv_path.open(encoding="utf-8") as fh:
            rows = [r for r in csv.DictReader(fh) if (r.get("articleText") or "").strip()]
        if rows:
            per_source.append(rows)

    interleaved = []
    for i in range(max((len(r) for r in per_source), default=0)):
        for rows in per_source:
            if i < len(rows):
                interleaved.append(rows[i])
    return interleaved


def main():
    parser = argparse.ArgumentParser(description="Generate reference/candidate pairs for ROUGE")
    parser.add_argument("--n", type=int, default=10, help="how many pairs to build (default 10)")
    parser.add_argument("--out", default="eval_pairs.csv", help="output CSV (default eval_pairs.csv)")
    parser.add_argument("--queries", help="file with one question per line, used instead of article titles")
    parser.add_argument("--baselines", action="store_true",
                        help="also produce the lead-3 and no-retrieval baselines for comparison")
    args = parser.parse_args()

    articles = load_articles()
    if not articles:
        sys.exit(f"no articles found under {SOURCES_DIR} — run the scrapers first")

    if args.queries:
        questions = [q.strip() for q in Path(args.queries).read_text(encoding="utf-8").splitlines() if q.strip()]
        # hand-written questions have no single source article, so the reference
        # is whatever the system retrieved; see the note printed at the end
        pairs = [(q, None) for q in questions][: args.n]
    else:
        pairs = [(a["articleTitle"], a) for a in articles[: args.n]]

    rows = []
    for i, (question, article) in enumerate(pairs, start=1):
        print(f"[{i}/{len(pairs)}] {question[:70]}")
        started = time.time()
        try:
            answer = retriever.process_user_query(question)
        except Exception as e:
            print(f"    failed: {e}")
            continue
        seconds = round(time.time() - started, 2)

        if article is not None:
            reference = f"{article['articleTitle']}\n\n{article['articleText']}"
            expected = article["articleLink"]
        else:
            # no source article to compare against: fall back to the top retrieved one
            retrieved = retriever.retrieve_articles(question, top_k=1)
            reference = retrieved[0]["text"] if retrieved else ""
            expected = retrieved[0]["articleLink"] if retrieved else ""

        row = {
            "query": question,
            "reference": reference,
            "candidate": answer,
            "seconds": seconds,
            "expected_link": expected,
            "cited_expected": "yes" if expected and expected in (answer or "") else "no",
        }

        if args.baselines:
            row["lead3"] = lead_3(article["articleText"]) if article is not None else lead_3(reference)
            try:
                row["noretrieval"] = no_retrieval_answer(question)
            except Exception as e:
                print(f"    no-retrieval baseline failed: {e}")
                row["noretrieval"] = ""

        rows.append(row)
        print(f"    {seconds}s, cited expected source: {row['cited_expected']}")

    if not rows:
        sys.exit("no pairs were produced")

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    hits = sum(1 for r in rows if r["cited_expected"] == "yes")
    mean = sum(r["seconds"] for r in rows) / len(rows)
    print(f"\nwrote {len(rows)} pairs to {args.out}")
    print(f"mean latency {mean:.2f}s | answer cited the source article in {hits}/{len(rows)} cases")
    print(f"score them with:  python rouge_eval.py --csv {args.out}")

    if args.baselines:
        stem = Path(args.out).stem
        lead3_path = f"{stem}_lead3.csv"
        noretr_path = f"{stem}_noretrieval.csv"
        write_pairs(lead3_path, rows, "lead3")
        write_pairs(noretr_path, rows, "noretrieval")
        print(f"baselines: {lead3_path}, {noretr_path} — score each the same way")


if __name__ == "__main__":
    main()
