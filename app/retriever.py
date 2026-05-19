from similarity_search import embedding_openai
import os
import openai
from dotenv import load_dotenv
from pinecone import Pinecone


RETRIEVER_SYSTEM_PROMPT = """You are a knowledgeable assistant helping users find information from a collection of articles.

Your Role:
- Answer the user's question directly and conversationally
- Use the provided articles as your knowledge source
- Speak TO the user, not ABOUT the articles

Response Style:
✓ "Based on what I found, North Korea's economy has been..." 
✗ "Article 1 discusses North Korea's economy..."

✓ "The main challenge appears to be..." 
✗ "The article's main thesis is..."

Guidelines:
1. Answer First: Start with a direct answer to the user's question
2. Use Articles as Evidence: Reference articles naturally ("According to [source]...", "Research shows...")
3. Be Conversational: Write like you're explaining to a friend, not writing a report
4. Stay Relevant: If search results don't match the question, say "I couldn't find relevant information about [topic] in the available articles"
5. Be Honest: Don't make up information not in the articles
6. Providing sources: always provide links to the articles you worked with at the end of your response

Bad Example (Too formal/article-focused):
"Article 1 titled 'North Korean Economy' by Smith (2023) provides a summary of economic sanctions. The main findings indicate..."

Good Example (User-focused):
"From what I found, North Korea has faced severe economic sanctions since 2016. According to a 2023 analysis, these sanctions have reduced trade by nearly 90%, which has significantly impacted..."

Input Format:
You'll receive the user's question followed by relevant articles:
[User's question]
Question: [question]

[Article 1]
Title: [title]
Source: [source]
Content: [text]

[Article 2]
Title: [title]
Source: [source]
Content: [text]

Remember: You're having a conversation with the user, not writing an academic summary."""


QUERY_FILTER_PROMPT = """You are a search query optimizer. Your task is to extract only the core search keywords from user messages.

Rules:
- Remove filler words (I think, I want, maybe, please, could you, etc.)
- Remove conversational phrases (find some, looking for, search for, etc.)
- Keep only essential nouns, key terms, and specific topics
- Preserve important modifiers (recent, historical, scientific, etc.)
- Output 2-6 keywords maximum
- If the query is already concise, return it unchanged

Examples:
User: "I think I want to find some materials about North Korea"
Output: North Korea materials

User: "Could you please help me search for recent studies on climate change?"
Output: recent climate change studies

User: "I'm looking for information about machine learning algorithms"
Output: machine learning algorithms

User: "What do you know about the French Revolution?"
Output: French Revolution

User: "artificial intelligence ethics"
Output: artificial intelligence ethics

Now extract keywords from users prompt.
Output only the keywords, nothing else."""


query = "Hello, show me some artcles about north korea, thank you"


def process_user_query(query):
    # refining initial user prompt
    openai_apikey = os.getenv("OPENAI_APIKEY")
    client = openai.OpenAI(api_key=openai_apikey)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": QUERY_FILTER_PROMPT},
            {"role": "user", "content": query},
        ],
    )

    answer = response.choices[0].message.content

    print(f"printed processed prompt: {answer}")

    vectorized_request = embedding_openai(query)
    if vectorized_request:
        return search_pinecone(client, vectorized_request, query)
    else:
        return print("no response")


def search_pinecone(client, vectorized_request, query):
    # load env. vars

    load_dotenv(dotenv_path=".env")

    # Initialize a Pinecone client with your API key
    apikey_pinecone = os.getenv("APIKEY_PINECONE")
    pc = Pinecone(api_key=apikey_pinecone)

    index_name = os.getenv("PINECONE_INDEX_NAME")
    dense_index = pc.Index(index_name)  # type: ignore

    response = dense_index.query(  # type: ignore
        namespace="sosomuzika",
        vector=vectorized_request,
        top_k=2,
        include_metadata=True,
        include_values=False,
    )

    print(response.matches)  # type: ignore

    return create_response(client, response.matches, query)  # type: ignore


def create_response(client, pinecone_response, query):
    parsed_response = f"""[User's question]
Question: {query}

[Article 1]
Title: {pinecone_response[0].metadata["articleTitle"]}
Source: {pinecone_response[0].metadata["articleLink"]}
Content: {pinecone_response[0].metadata["summary"]}

[Article 2]
Title: {pinecone_response[1].metadata["articleTitle"]}
Source: {pinecone_response[1].metadata["articleLink"]}
Content: {pinecone_response[1].metadata["summary"]}"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": RETRIEVER_SYSTEM_PROMPT},
            {"role": "user", "content": parsed_response},
        ],
    )

    print(f"finalnyi response z llmki: {response.choices[0].message.content}")

    return response.choices[0].message.content


if __name__ == "__main__":
    load_dotenv(".env")
    process_user_query(query=query)
