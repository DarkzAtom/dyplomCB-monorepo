"""Dump the FULL semantic-chunker output to a readable text file for inspection.

Run from scrapers/:
  /home/rekru/PycharmProjects/dyplomCB-monorepo/scrapers/.venv/bin/python dump_chunks.py
"""
import csv, os
from dotenv import load_dotenv

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vectordb.chunking import build_semantic_chunker, chunk_article, token_len

load_dotenv("/home/rekru/PycharmProjects/dyplomCB-monorepo/scrapers/.env")
api_key = os.getenv("OPENAI_APIKEY")

CSV = "scrapers/thehackernews/output.csv"
SAMPLE = 25
OUT = "CHUNKS_semantic_tuned.txt"
SWEET_HI = 512


def load_articles(path, limit):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        body = (r.get("articleText") or "").strip()
        title = (r.get("articleTitle") or "").strip()
        if len(body.split()) >= 60:
            out.append((title, body))
        if len(out) >= limit:
            break
    return out


chunker = build_semantic_chunker(api_key, breakpoint_amount=90, buffer_size=1,
                                 min_chunk_size=200)
articles = load_articles(CSV, SAMPLE)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("TUNED LangChain SemanticChunker (percentile 90, buffer 1, "
            "min_chunk_size 200) + title prefix\n")
    f.write(f"{SAMPLE} articles\n\n")
    for a_idx, (title, body) in enumerate(articles):
        chunks = chunk_article(body, title, chunker)
        f.write("#" * 100 + "\n")
        f.write(f"ARTICLE {a_idx + 1}/{len(articles)}: {title}\n")
        f.write(f"split into {len(chunks)} chunks\n")
        f.write("#" * 100 + "\n\n")
        for i, c in enumerate(chunks):
            flag = "   <-- OVER 512 (would be re-split by recursive guard)" \
                if token_len(c) > SWEET_HI else ""
            f.write("=" * 90 + "\n")
            f.write(f"CHUNK {i + 1}/{len(chunks)}   ({token_len(c)} tokens, "
                    f"{len(c.split())} words){flag}\n")
            f.write("=" * 90 + "\n")
            f.write(c + "\n\n")

print(f"Wrote {OUT}")
