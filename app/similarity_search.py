import openai

from dotenv import load_dotenv
import os


def embedding_openai(query):
    load_dotenv(".env")
    openai_apikey = os.getenv("OPENAI_APIKEY")
    client = openai.OpenAI(api_key=openai_apikey)

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )

    # Extract embeddings from response
    embeddings = [data.embedding for data in response.data]

    return embeddings[0]



