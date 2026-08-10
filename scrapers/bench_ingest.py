"""Ingestion-throughput benchmark for the write side of the pipeline (thesis 7.1).

Measures how fast a newly scraped article becomes searchable, decomposed into the
three ingestion stages per article:

    chunk   semantic chunking (vectordb.chunking.chunk_article; note this itself
            calls the embedding API for topic-boundary detection)
    embed   embedding each final chunk into its vector (text-embedding-3-small)
    upsert  writing the vectors to Pinecone (namespace sosomuzika)

Reuses the exact functions vectordb/pinecone_sync.py uses in production, so the
timed path matches the real sync. Idempotent: chunk ids are short_hash(link)-based,
so re-running upserts the same ids already in the index (no pollution).

Run from the scrapers/ directory (same cwd rule as pinecone_sync.py):

    cd scrapers
    python bench_ingest.py                                   # default CSV, 20 articles
    python bench_ingest.py scrapers/nask/output.csv --limit 30
    python bench_ingest.py --dry-run                         # skip the Pinecone upsert

Writes scrapers/bench_ingest.csv (one row per article) and prints the throughput
summary used to fill the section 7.1 ingestion placeholder.
"""
import argparse
import csv
import time

from vectordb.chunking import chunk_article, token_len
from vectordb.pinecone_sync import (
    NAMESPACE,
    csv_to_dict_array,
    embedding_openai,
    get_chunker,
    get_index,
    short_hash,
)

DEFAULT_CSV = "scrapers/thehackernews/output.csv"


def main():
    parser = argparse.ArgumentParser(description="Ingestion throughput benchmark.")
    parser.add_argument("csv", nargs="?", default=DEFAULT_CSV,
                        help=f"Scraper output.csv (default {DEFAULT_CSV}).")
    parser.add_argument("--limit", type=int, default=20,
                        help="Number of articles to process (default 20).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chunk + embed but skip the Pinecone upsert.")
    parser.add_argument("--out", default="bench_ingest.csv",
                        help="CSV output path (default bench_ingest.csv).")
    args = parser.parse_args()

    articles = csv_to_dict_array(args.csv)[: args.limit]
    chunker = get_chunker()
    dense_index = None if args.dry_run else get_index()

    rows = []
    tot_chunk = tot_embed = tot_upsert = 0.0
    tot_chunks = 0
    wall_start = time.perf_counter()

    for i, art in enumerate(articles):
        title = art["articleTitle"]
        body = art["articleText"]

        # chunk stage
        t0 = time.perf_counter()
        chunks = chunk_article(body, title, chunker)
        t_chunk = time.perf_counter() - t0

        # embed stage (one vector per chunk)
        base_id = short_hash(art["articleLink"])
        vectors = []
        t0 = time.perf_counter()
        for idx, chunk_text in enumerate(chunks):
            metadata = art.copy()
            metadata.pop("articleText", None)
            metadata["chunk_text"] = chunk_text
            metadata["chunk_index"] = idx
            vectors.append({
                "id": f"{base_id}_chunk_{idx}",
                "values": embedding_openai(chunk_text),
                "metadata": metadata,
            })
        t_embed = time.perf_counter() - t0

        # upsert stage
        t_upsert = 0.0
        if not args.dry_run and vectors:
            t0 = time.perf_counter()
            dense_index.upsert(vectors=vectors, namespace=NAMESPACE)
            t_upsert = time.perf_counter() - t0

        tokens = sum(token_len(c) for c in chunks)
        tot_chunk += t_chunk
        tot_embed += t_embed
        tot_upsert += t_upsert
        tot_chunks += len(chunks)
        rows.append({
            "article": i,
            "title": title[:60],
            "chunks": len(chunks),
            "tokens": tokens,
            "chunk_s": round(t_chunk, 3),
            "embed_s": round(t_embed, 3),
            "upsert_s": round(t_upsert, 3),
            "total_s": round(t_chunk + t_embed + t_upsert, 3),
        })
        print(f"article {i}: {len(chunks)} chunks | chunk {t_chunk:.2f}s / "
              f"embed {t_embed:.2f}s / upsert {t_upsert:.2f}s  ({title[:50]})")

    wall = time.perf_counter() - wall_start
    n = len(rows)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\nArticles processed : {n}")
    print(f"Total chunks       : {tot_chunks}  (avg {tot_chunks / n:.1f} per article)")
    print(f"Wall-clock         : {wall:.2f}s")
    print(f"Stage totals       : chunk {tot_chunk:.2f}s / embed {tot_embed:.2f}s / "
          f"upsert {tot_upsert:.2f}s")
    print(f"Per article (mean) : chunk {tot_chunk / n:.2f}s / embed {tot_embed / n:.2f}s / "
          f"upsert {tot_upsert / n:.2f}s / total {(tot_chunk + tot_embed + tot_upsert) / n:.2f}s")
    print(f"Throughput         : {n / wall:.2f} articles/s | {tot_chunks / wall:.2f} chunks/s")
    if args.dry_run:
        print("(dry-run: upsert skipped, upsert timings are 0)")
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
