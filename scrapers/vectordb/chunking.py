"""Semantic chunking for article ingestion.

SemanticChunker finds topic boundaries; anything over MAX_TOKENS gets re-split by
a tiktoken-aware RecursiveCharacterTextSplitter (with overlap). Each chunk is
prefixed with the article title so it stays tied to its source when retrieved alone.
"""
import tiktoken
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

EMBED_MODEL = "text-embedding-3-small"
MAX_TOKENS = 512       # soft ceiling; blocks bigger than this get re-split
OVERLAP_TOKENS = 64    # repeated tail between sub-pieces so nothing gets cut in half

_enc = tiktoken.encoding_for_model(EMBED_MODEL)


def token_len(text):
    return len(_enc.encode(text))


def build_semantic_chunker(api_key,
                           breakpoint_amount=90,
                           buffer_size=1,
                           min_chunk_size=200):
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL, api_key=api_key)
    return SemanticChunker(
        embeddings,
        buffer_size=buffer_size,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=breakpoint_amount,
        min_chunk_size=min_chunk_size,
    )


def chunk_article(text, title, chunker, max_tokens=MAX_TOKENS):
    prefix = f"{title}\n\n"
    budget = max(max_tokens - token_len(prefix), OVERLAP_TOKENS * 2)

    
    guard = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name=_enc.name,
        chunk_size=budget,
        chunk_overlap=OVERLAP_TOKENS,
    )

    blocks = [b for b in chunker.split_text(text) if b.strip()]

    sized = []
    for b in blocks:
        if token_len(b) > budget:
            sized.extend(guard.split_text(b))    # break the monster, keep overlap
        else:
            sized.append(b)

    return [prefix + p for p in sized if p.strip()]
