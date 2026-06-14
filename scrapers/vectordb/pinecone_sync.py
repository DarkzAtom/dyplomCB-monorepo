import argparse
import hashlib
import csv
import os
import openai
from pinecone import Pinecone
from dotenv import load_dotenv

# --- CHUNKER (LangChain semantic + recursive size guard + title prefix) ---
# chunking.py lives in the same folder as this file
from vectordb.chunking import build_semantic_chunker, chunk_article, token_len

# load env. vars
load_dotenv(dotenv_path=".env")

apikey_pinecone = os.getenv("APIKEY_PINECONE")
openai_apikey = os.getenv("OPENAI_APIKEY")
index_name = os.getenv("PINECONE_INDEX_NAME")
NAMESPACE = "sosomuzika"

client = openai.OpenAI(api_key=openai_apikey)

# Built lazily so importing this module (or a --dry-run) doesn't require Pinecone.
_dense_index = None
_chunker = None


def get_index():
    """Connect to Pinecone on first use only."""
    global _dense_index
    if _dense_index is None:
        pc = Pinecone(api_key=apikey_pinecone)
        _dense_index = pc.Index(index_name)  # type: ignore
    return _dense_index


def get_chunker():
    """Build the semantic chunker once and reuse it across articles/CSVs."""
    global _chunker
    if _chunker is None:
        _chunker = build_semantic_chunker(openai_apikey)
    return _chunker


def embedding_openai(article):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=article,
    )
    embeddings = [data.embedding for data in response.data]
    return embeddings[0]


def csv_to_dict_array(filename):
    result = []
    with open(filename, "r", encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            result.append(dict(row))
    return result


def short_hash(text, length=8):
    """Create a short hash for use as ID"""
    full_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return full_hash[:length]


def main(csv_filename, dry_run=False, limit=None):
    """Chunk every article in the CSV and upsert the chunks to Pinecone.

    dry_run=True: do all the chunking (so you can eyeball the result) but skip
    per-chunk embedding and the Pinecone upsert. Nothing is written.
    limit: process only the first N articles (handy for a quick smoke test).
    """
    print(f"Starting sync for: {csv_filename}  (dry_run={dry_run}, limit={limit})")
    articles = csv_to_dict_array(csv_filename)
    if limit:
        articles = articles[:limit]
    chunker = get_chunker()
    vectors = []
    chunk_token_sizes = []

    for i in range(len(articles)):
        title = articles[i]["articleTitle"]
        body = articles[i]["articleText"]

        # Semantic chunk the body; chunk_article prefixes the title onto each chunk
        chunks = chunk_article(body, title, chunker)

        base_id = short_hash(articles[i]["articleLink"])
        print(f"Article {i}: {len(chunks)} chunks  ({title[:60]})")

        for chunk_index, chunk_text in enumerate(chunks):
            chunk_token_sizes.append(token_len(chunk_text))
            chunk_id = f"{base_id}_chunk_{chunk_index}"

            metadata = articles[i].copy()
            metadata.pop("articleText", None)
            metadata["chunk_text"] = chunk_text
            metadata["chunk_index"] = chunk_index

            if dry_run:
                continue  # skip embedding + upsert, we only wanted the chunks

            vector = embedding_openai(chunk_text)
            vectors.append({"id": chunk_id, "values": vector, "metadata": metadata})

    n = len(chunk_token_sizes)
    if n:
        over = sum(1 for t in chunk_token_sizes if t > 512)
        print(f"Chunks: {n} | avg {sum(chunk_token_sizes)//n} tok | "
              f"max {max(chunk_token_sizes)} tok | over-512: {over}")

    if dry_run:
        print(f"DRY RUN complete for {csv_filename} — nothing written to Pinecone.")
        return

    print(f"Total vectors created from this CSV: {len(vectors)}")

    # Batch Upsert (chunks of 100 to avoid API timeouts)
    dense_index = get_index()
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i: i + batch_size]
        dense_index.upsert(vectors=batch, namespace=NAMESPACE)  # type: ignore
        print(f"Upserted batch {i // batch_size + 1}")

    print(f"Done processing {csv_filename}!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chunk a CSV of articles and sync to Pinecone.")
    parser.add_argument("csv", help="Path to the scraper output.csv")
    parser.add_argument("--dry-run", action="store_true",
                        help="Chunk only; do not embed or write to Pinecone.")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only process the first N articles.")
    args = parser.parse_args()
    main(args.csv, dry_run=args.dry_run, limit=args.limit)
