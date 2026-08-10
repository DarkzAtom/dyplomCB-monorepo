"""Per-stage latency benchmark for the query-side RAG pipeline (thesis section 7.1).

Times the four cost centres of a single query separately, so the report can show
which stage dominates end-to-end latency:

    (a) query-filter  chat completion   gpt-4.1-mini
    (b) query embed   embedding call    text-embedding-3-small
    (c) retrieval     Pinecone top_k=6 similarity search
    (d) answer-gen    chat completion   gpt-4.1-mini

It reuses retriever.py's prompts and grouping helpers so the timed path matches
production (retriever.process_user_query); it only wraps each call in
time.perf_counter() instead of running them opaquely.

Run from the app/ directory (same cwd rule as retriever.py):

    cd app
    python bench_latency.py                 # default: 12 queries x 3 runs
    python bench_latency.py --runs 5        # more repeats for tighter spread

Writes app/bench_latency.csv (one row per query iteration) and prints the
per-stage mean/median/p95 table used to fill the section 7.1 placeholder.
"""
import argparse
import csv
import os
import statistics
import time
from datetime import date

import openai
from dotenv import load_dotenv
from pinecone import Pinecone

# Reuse the exact prompts and grouping helpers the production retriever uses,
# so this benchmark times the real pipeline, not a re-implementation of it.
from retriever import (
    QUERY_FILTER_PROMPT,
    RETRIEVER_SYSTEM_PROMPT,
    _article_date,
    _chunk_index,
)
from similarity_search import embedding_openai

NAMESPACE = "sosomuzika"
TOP_K = 6
CHAT_MODEL = "gpt-4.1-mini"

# Representative query set: four buckets so the spread reflects real usage,
# not one query type. Labels are carried into the CSV for per-bucket inspection.
QUERY_SET = [
    ("short_inscope", "ransomware attacks"),
    ("short_inscope", "zero-day exploit"),
    ("short_inscope", "phishing campaign"),
    ("medium_inscope", "recent data breach affecting healthcare providers"),
    ("medium_inscope", "state-sponsored threat actors critical infrastructure"),
    ("medium_inscope", "vulnerability in VPN and firewall products"),
    ("long_inscope",
     "I've been reading a lot lately and I was wondering if you could tell me "
     "about recent ransomware incidents that hit hospitals and what was stolen"),
    ("long_inscope",
     "Could you please help me understand what the latest news says about "
     "state-sponsored groups targeting power grids and other critical systems"),
    ("long_inscope",
     "What do we currently know about newly disclosed remote code execution "
     "vulnerabilities in widely used enterprise VPN and firewall appliances"),
    ("out_of_scope", "best pizza recipe in Naples"),
    ("out_of_scope", "who won the 2018 FIFA World Cup"),
    ("out_of_scope", "how do I knit a wool scarf for winter"),
]


def percentile(values, pct):
    """Nearest-rank percentile (pct in 0..100). Small samples, so no interpolation."""
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1))))
    return ordered[k]


def build_context(matches, query):
    """Replicate retriever.create_response's context assembly (group chunks back
    per source article) so stage (d) is timed on the exact prompt production sends.
    Kept in sync with retriever.create_response."""
    articles = {}
    order = []
    for match in matches:
        md = match.metadata
        link = md.get("articleLink", "")
        if link not in articles:
            articles[link] = {
                "title": md.get("articleTitle", ""),
                "link": link,
                "date": _article_date(md),
                "chunks": [],
            }
            order.append(link)
        text = md.get("chunk_text", md.get("summary", ""))
        articles[link]["chunks"].append((_chunk_index(md.get("chunk_index")), text))

    blocks = []
    for n, link in enumerate(order, start=1):
        art = articles[link]
        ordered = sorted(art["chunks"], key=lambda c: c[0])
        content = "\n\n".join(text for _, text in ordered)
        blocks.append(
            f"[Article {n}]\nTitle: {art['title']}\nDate: {art['date']}\n"
            f"Source: {art['link']}\nContent: {content}"
        )
    return f"[User's question]\nQuestion: {query}\n\n" + "\n\n".join(blocks)


def time_query(client, dense_index, query):
    """Run the four stages of one query, returning per-stage seconds + total."""
    # (a) query-filter chat completion
    t0 = time.perf_counter()
    filt = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": QUERY_FILTER_PROMPT},
            {"role": "user", "content": query},
        ],
    )
    keywords = filt.choices[0].message.content
    t_filter = time.perf_counter() - t0

    # (b) embed the cleaned keywords (matches retriever: it embeds the filter output)
    t0 = time.perf_counter()
    vector = embedding_openai(keywords)
    t_embed = time.perf_counter() - t0

    # (c) Pinecone similarity search
    t0 = time.perf_counter()
    resp = dense_index.query(
        namespace=NAMESPACE,
        vector=vector,
        top_k=TOP_K,
        include_metadata=True,
        include_values=False,
    )
    t_search = time.perf_counter() - t0

    # (d) answer-generation chat completion
    context = build_context(resp.matches, query)
    system_prompt = (
        f"{RETRIEVER_SYSTEM_PROMPT}\n\nFor recency judgments: today's date is "
        f"{date.today().isoformat()}. Compare each article's Date against it."
    )
    t0 = time.perf_counter()
    client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context},
        ],
    )
    t_answer = time.perf_counter() - t0

    total = t_filter + t_embed + t_search + t_answer
    return {
        "filter": t_filter,
        "embed": t_embed,
        "search": t_search,
        "answer": t_answer,
        "end_to_end": total,
    }


def summarize(rows, stage):
    vals = [r[stage] for r in rows]
    return {
        "mean": statistics.mean(vals),
        "median": statistics.median(vals),
        "p95": percentile(vals, 95),
    }


def main():
    parser = argparse.ArgumentParser(description="Per-stage RAG query latency benchmark.")
    parser.add_argument("--runs", type=int, default=3,
                        help="Repeats of the whole query set (default 3).")
    parser.add_argument("--out", default="bench_latency.csv",
                        help="CSV output path (default bench_latency.csv).")
    args = parser.parse_args()

    load_dotenv(".env")
    client = openai.OpenAI(api_key=os.getenv("OPENAI_APIKEY"))
    pc = Pinecone(api_key=os.getenv("APIKEY_PINECONE"))
    dense_index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

    stages = ["filter", "embed", "search", "answer", "end_to_end"]
    rows = []
    for run in range(1, args.runs + 1):
        for bucket, query in QUERY_SET:
            t = time_query(client, dense_index, query)
            t.update({"run": run, "bucket": bucket, "query": query})
            rows.append(t)
            print(f"run {run} [{bucket}] {t['end_to_end']:.2f}s "
                  f"(filter {t['filter']:.2f} / embed {t['embed']:.2f} / "
                  f"search {t['search']:.2f} / answer {t['answer']:.2f})")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["run", "bucket", "query"] + stages)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in ["run", "bucket", "query"] + stages})

    print(f"\nSamples: {len(rows)}  ({args.runs} runs x {len(QUERY_SET)} queries)\n")
    header = f"{'stage':<12}{'mean':>10}{'median':>10}{'p95':>10}"
    print(header)
    print("-" * len(header))
    for stage in stages:
        s = summarize(rows, stage)
        print(f"{stage:<12}{s['mean']:>9.3f}s{s['median']:>9.3f}s{s['p95']:>9.3f}s")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
