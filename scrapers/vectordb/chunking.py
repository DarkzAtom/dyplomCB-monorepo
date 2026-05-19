import re
import numpy as np

def cosine_similarity(v1, v2):
    """Calculates the similarity between two vectors."""
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def semantic_chunker(text, openai_client, similarity_threshold=0.75):
    """
    Splits text into semantic chunks without using LangChain.
    similarity_threshold: How similar sentences need to be to stay in the same chunk.
                          Lower number = larger, fewer chunks.
                          Higher number = smaller, more chunks.
    """
    # 1. Split text into individual sentences using regex (looks for ., ?, or !)
    sentences = re.split(r'(?<=[.?!])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return []
    if len(sentences) == 1:
        return sentences

    # 2. Get embeddings for ALL sentences at once (saves API calls!)
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=sentences,
    )
    embeddings = [data.embedding for data in response.data]

    # 3. Group sentences based on meaning
    chunks = []
    current_chunk = [sentences[0]]
    
    for i in range(1, len(sentences)):
        # Compare current sentence to the previous one
        sim = cosine_similarity(embeddings[i-1], embeddings[i])
        
        if sim >= similarity_threshold:
            # Topic is similar enough, add to the current chunk
            current_chunk.append(sentences[i])
        else:
            # Topic changed! Save the old chunk and start a new one
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentences[i]]
            
    # Add the final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks