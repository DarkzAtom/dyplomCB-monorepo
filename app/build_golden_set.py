"""Freezes a reproducible reference/candidate set for the golden-summary ROUGE
eval (DYP-48, Option 1: golden = the ideal *answer* to the query).

For each query it mirrors retriever.process_user_query EXACTLY — the same
keyword filter, the same embedding, the same top_k=6 Pinecone search — so the
context captured here is the context the answer was actually generated from.
Everything is frozen into one CSV: because the Pinecone corpus keeps changing,
re-running retrieval later would drift, so the eval reads only this file.

Columns written to golden_workset.csv:
    query          the user question posed to the system
    keywords       what QUERY_FILTER_PROMPT reduced the query to (provenance)
    retrieved      the retrieved articles, readable — DRAFT THE GOLDEN FROM THIS
    candidate      the system answer, Sources: list stripped (scored by ROUGE)
    candidate_raw  the untouched answer, links and all (provenance)
    seconds        end-to-end latency (filter + embed + search + generate)
    sources        the links the retrieved articles came from
    reference      EMPTY — the golden answer goes here, then rouge_eval reads it

Run from the app/ directory:
    python build_golden_set.py            # all queries below
    python build_golden_set.py --n 5      # first 5 only (cheap smoke run)

Then a human writes the golden answer into the `reference` column of each row,
and scores the file straight away (rouge_eval ignores the extra columns):
    python rouge_eval.py --csv golden_workset.csv
"""

import argparse
import csv
import os
import re
import sys
import time

from dotenv import load_dotenv

# retriever + embedding read OPENAI_APIKEY at call time, so env must be loaded first
load_dotenv(dotenv_path=".env")

import openai  # noqa: E402
from pinecone import Pinecone  # noqa: E402

import retriever  # noqa: E402
from similarity_search import embedding_openai  # noqa: E402

# article bodies exceed the csv default field limit
csv.field_size_limit(10_000_000)

# Realistic user questions spread across the topics/sources in the corpus.
QUERIES = [
    "ransomware attacks targeting healthcare organizations",
    "critical vulnerabilities currently being actively exploited",
    "North Korean state-sponsored hacking activity",
    "recent large-scale data breaches",
    "phishing campaigns using AI and deepfakes",
    "software supply chain attacks",
    "SAP NetWeaver vulnerability exploitation",
    "Lazarus Group cryptocurrency theft",
    "vulnerabilities added to the CISA known exploited catalog",
    "malware targeting macOS users",
    "Microsoft security updates and patched flaws",
    "Chinese APT cyber espionage campaigns",
    "attacks exploiting VPN and firewall appliances",
    "malware stealing cryptocurrency wallets",
    "Russian hackers targeting Ukraine",
    "security vulnerabilities in AI and LLM tools",
    "fake IT worker and job interview scams",
    "Linux kernel security vulnerabilities",
    "credential theft and infostealer malware",
    "cloud security misconfigurations and breaches",
]


def filter_query(client, query):
    """Same keyword reduction retriever.process_user_query runs before embedding."""
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": retriever.QUERY_FILTER_PROMPT},
            {"role": "user", "content": query},
        ],
    )
    return response.choices[0].message.content


def search(vector):
    pc = Pinecone(api_key=os.getenv("APIKEY_PINECONE"))
    index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))  # type: ignore
    response = index.query(  # type: ignore
        namespace="sosomuzika",
        vector=vector,
        top_k=6,  # identical to retriever.search_pinecone
        include_metadata=True,
        include_values=False,
    )
    return response.matches  # type: ignore


def group_articles(matches):
    """Group chunks back into source articles, same as create_response, but
    return readable text + links for drafting the golden and citing sources.
    """
    articles = {}
    order = []
    for match in matches:
        md = match.metadata
        link = md.get("articleLink", "")
        if link not in articles:
            articles[link] = {
                "title": md.get("articleTitle", ""),
                "link": link,
                "chunks": [],
            }
            order.append(link)
        text = md.get("chunk_text", md.get("summary", ""))
        articles[link]["chunks"].append((retriever._chunk_index(md.get("chunk_index")), text))

    blocks, links = [], []
    for n, link in enumerate(order, start=1):
        art = articles[link]
        ordered = sorted(art["chunks"], key=lambda c: c[0])
        content = "\n\n".join(text for _, text in ordered)
        blocks.append(f"[Article {n}] {art['title']}\n{art['link']}\n{content}")
        links.append(link)
    return "\n\n".join(blocks), links


def strip_sources(answer):
    """Remove the trailing link list the model appends. The body sometimes
    contains legitimate 'If you're managing...' advice, so only drop lines that
    actually carry a URL plus a dangling lead-in line right before them.
    """
    lines = (answer or "").splitlines()
    kept = [ln for ln in lines if "http" not in ln]
    while kept:
        tail = kept[-1].strip().lower()
        if tail == "" or tail.endswith(":") or tail.startswith(("sources", "source", "here are", "if you're interested")):
            kept.pop()
        else:
            break
    return "\n".join(kept).strip()


def main():
    parser = argparse.ArgumentParser(description="Freeze the golden-set workset for ROUGE (Option 1)")
    parser.add_argument("--n", type=int, help="only the first N queries (default: all)")
    parser.add_argument("--out", default="golden_workset.csv", help="output CSV (default golden_workset.csv)")
    args = parser.parse_args()

    queries = QUERIES[: args.n] if args.n else QUERIES
    client = openai.OpenAI(api_key=os.getenv("OPENAI_APIKEY"))

    rows = []
    for i, query in enumerate(queries, start=1):
        print(f"[{i}/{len(queries)}] {query}")
        started = time.time()
        try:
            keywords = filter_query(client, query)
            vector = embedding_openai(keywords)
            if not vector:
                print("    embedding failed, skipping")
                continue
            matches = search(vector)
            retrieved, links = group_articles(matches)
            answer = retriever.create_response(client, matches, query)
        except Exception as e:  # noqa: BLE001
            print(f"    failed: {e}")
            continue
        seconds = round(time.time() - started, 2)

        rows.append({
            "query": query,
            "keywords": keywords,
            "retrieved": retrieved,
            "candidate": strip_sources(answer),
            "candidate_raw": answer,
            "seconds": seconds,
            "sources": " ".join(links),
            "reference": "",  # golden answer goes here
        })
        print(f"    {seconds}s, {len(links)} articles retrieved")

    if not rows:
        sys.exit("no rows produced — check the API keys and that Pinecone has data")

    fields = ["query", "keywords", "retrieved", "candidate", "candidate_raw", "seconds", "sources", "reference"]
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nwrote {len(rows)} rows to {args.out}")
    print("next: fill the `reference` column with the golden answer, then")
    print(f"      python rouge_eval.py --csv {args.out}")


if __name__ == "__main__":
    main()
