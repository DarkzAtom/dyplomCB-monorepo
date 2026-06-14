import hashlib
import csv
import os
import openai
from pinecone import Pinecone
from dotenv import load_dotenv

# --- IMPORT YOUR CHUNKER ---
# Package-qualified so it resolves under a clean sys.path (e.g. `python main.py`
# from the scrapers root, as in Docker). A bare `from chunking import ...` only
# works when vectordb/ happens to be on the path, e.g. via PyCharm source roots.
from vectordb.chunking import semantic_chunker

# load env. vars
load_dotenv(dotenv_path=".env")

# Initialize a Pinecone client with your API key
apikey_pinecone = os.getenv("APIKEY_PINECONE")
openai_apikey = os.getenv("OPENAI_APIKEY")
pc = Pinecone(api_key=apikey_pinecone)

# Create a dense index with integrated embedding
index_name = os.getenv("PINECONE_INDEX_NAME")
dense_index = pc.Index(index_name)  # type: ignore

client = openai.OpenAI(api_key=openai_apikey)

def embedding_openai(article):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=article,
    )
    # Extract embeddings from response
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


def main(csv_filename):
    print(f"Starting sync for: {csv_filename}")
    articles = csv_to_dict_array(csv_filename)
    vectors = []

    for i in range(len(articles)):
        print(f"Processing article i: {i}")
        
        # 1. Combine title and text for context
        full_text = articles[i]["articleTitle"] + "\n\n" + articles[i]["articleText"]
        
        # 2. Chop it into semantic chunks using your imported function
        # We pass the OpenAI client so your chunker can embed the sentences
        chunks = semantic_chunker(full_text, client)
        
        # Base ID for the whole article
        base_id = short_hash(articles[i]["articleLink"])
        
        # 3. Loop through every chunk we just created
        for chunk_index, chunk_text in enumerate(chunks):
            # Create a unique ID for this specific chunk (e.g., hash_chunk_0)
            chunk_id = f"{base_id}_chunk_{chunk_index}"
            
            # Embed the chunk
            vector = embedding_openai(chunk_text)
            
            # Setup Metadata - Use .copy() so we don't destroy the original article dictionary
            metadata = articles[i].copy()
            metadata.pop("articleText", None) # Remove full text like you did before
            
            # CRITICAL: Save the actual chunk text so you can read it later when you search
            metadata["chunk_text"] = chunk_text 
            metadata["chunk_index"] = chunk_index
            
            vectors.append({"id": chunk_id, "values": vector, "metadata": metadata})

    print(f"Total vectors created from this CSV: {len(vectors)}")

    # 4. Batch Upsert to Pinecone
    # Upserts in chunks of 100 to prevent API timeouts/crashes
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        dense_index.upsert(vectors=batch, namespace="sosomuzika")  # type: ignore
        print(f"Upserted batch {i//batch_size + 1}")
        
    print(f"Done processing {csv_filename}!")