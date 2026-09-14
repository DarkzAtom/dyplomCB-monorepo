"""Measure the semantic chunker on real articles - do chunks land in the 256-512
token sweet spot or come out too big (needing the recursive guard)? Run from scrapers/.
"""
import csv, os, re, statistics, textwrap
from dotenv import load_dotenv

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vectordb.chunking import build_semantic_chunker, chunk_article, token_len

# worktree has no .env -> load the real one from the main checkout
load_dotenv("/home/rekru/PycharmProjects/dyplomCB-monorepo/scrapers/.env")
api_key = os.getenv("OPENAI_APIKEY")

CSV = "scrapers/thehackernews/output.csv"
SAMPLE = 25          # how many articles to measure
SWEET_LO, SWEET_HI = 256, 512


def load_articles(path, limit):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = []
    for r in rows:
        body = (r.get("articleText") or "").strip()
        title = (r.get("articleTitle") or "").strip()
        if len(body.split()) >= 60:          # skip stubs
            out.append((title, body))
        if len(out) >= limit:
            break
    return out


def preview(c, width=85):
    return textwrap.shorten(" ".join(c.split()), width=width, placeholder=" …")


chunker = build_semantic_chunker(api_key, breakpoint_amount=90, buffer_size=1,
                                 min_chunk_size=200)

articles = load_articles(CSV, SAMPLE)
print(f"Measuring {len(articles)} articles | semantic chunker "
      f"(percentile 90, buffer 1, min_chunk_size 200) + title prefix\n")

all_tokens = []
oversize = []          # chunks above sweet-hi
for title, body in articles:
    chunks = chunk_article(body, title, chunker)
    for c in chunks:
        t = token_len(c)
        all_tokens.append(t)
        if t > SWEET_HI:
            oversize.append((t, title, c))

all_tokens.sort()
n = len(all_tokens)
over = sum(1 for t in all_tokens if t > SWEET_HI)
under = sum(1 for t in all_tokens if t < SWEET_LO)
inband = n - over - under

print(f"{'='*70}")
print(f"TOTAL chunks: {n}  (avg {sum(all_tokens)//n} tok per article: "
      f"{n/len(articles):.1f})")
print(f"  min={all_tokens[0]}  median={statistics.median(all_tokens):.0f}  "
      f"p90={all_tokens[int(n*0.9)]}  max={all_tokens[-1]} tokens")
print(f"{'='*70}")
print(f"  < {SWEET_LO} tok (small) : {under:3d}  ({under/n:5.1%})")
print(f"  {SWEET_LO}-{SWEET_HI} tok (sweet): {inband:3d}  ({inband/n:5.1%})")
print(f"  > {SWEET_HI} tok (BIG)    : {over:3d}  ({over/n:5.1%})  "
      f"<-- these would need the recursive guard")
print(f"{'='*70}\n")

if oversize:
    oversize.sort(reverse=True)
    print("Biggest oversize chunks:")
    for t, title, c in oversize[:5]:
        print(f"  [{t} tok] {preview(c)}")
    print()

# detail view of ONE representative article
print(f"{'#'*70}\nEXAMPLE ARTICLE (chunk-by-chunk):\n{'#'*70}")
title, body = articles[0]
print(f"TITLE: {title[:75]}")
for i, c in enumerate(chunk_article(body, title, chunker)):
    flag = "  <-- BIG" if token_len(c) > SWEET_HI else ""
    print(f"[chunk {i:02d} | {token_len(c):4d} tok] {preview(c)}{flag}")
