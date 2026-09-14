from similarity_search import embedding_openai
import os
import re
from datetime import date
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
7. Mind Recency: Each article carries a Date. When the user asks for recent / latest / newly disclosed events, lead with the most recently dated articles and state each item's date explicitly. If the freshest article you actually have is not recent, say so plainly (e.g. "the most recent I found is from May 2025") instead of presenting older news as if it were current. Treat a Date of "unknown" as undated, not as recent.

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
Date: [publication date]
Source: [source]
Content: [text]

[Article 2]
Title: [title]
Date: [publication date]
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
    openai_apikey = os.getenv("OPENAI_APIKEY")
    client = openai.OpenAI(api_key=openai_apikey)
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": QUERY_FILTER_PROMPT},
            {"role": "user", "content": query},
        ],
    )

    answer = response.choices[0].message.content

    print(f"printed processed prompt: {answer}")

    # Embed the cleaned keywords (filler stripped), not the raw user sentence,
    # for a tighter retrieval vector.
    vectorized_request = embedding_openai(answer)
    if vectorized_request:
        return search_pinecone(client, vectorized_request, query)
    else:
        return print("no response")


def search_pinecone(client, vectorized_request, query):
    load_dotenv(dotenv_path=".env")

    apikey_pinecone = os.getenv("APIKEY_PINECONE")
    pc = Pinecone(api_key=apikey_pinecone)

    index_name = os.getenv("PINECONE_INDEX_NAME")
    dense_index = pc.Index(index_name)  # type: ignore

    response = dense_index.query(  # type: ignore
        namespace="sosomuzika",
        vector=vectorized_request,
        top_k=6,  # chunks are small; pull several so the LLM has enough context
        include_metadata=True,
        include_values=False,
    )

    print(response.matches)  # type: ignore

    return create_response(client, response.matches, query)  # type: ignore


def _chunk_index(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _article_date(md):
    raw = (md.get("creationDate") or "").strip()
    if any(c.isdigit() for c in raw):
        return raw
    m = re.search(r"/(20\d{2})/(\d{1,2})/", md.get("articleLink", "") or "")
    if m:
        return f"{m.group(1)}-{m.group(2).zfill(2)}"
    return "unknown"


def create_response(client, pinecone_response, query):
    
    articles = {}
    order = []
    for match in pinecone_response:
        md = match.metadata
        link = md.get("articleLink", "")
        if link not in articles:
            articles[link] = {
                "title": md.get("articleTitle", ""),
                "link": link,
                "date": _article_date(md),
                "chunks": [],
            }
            order.append(link)
        text = md.get("chunk_text", md.get("summary", ""))
        articles[link]["chunks"].append((_chunk_index(md.get("chunk_index")), text))

    blocks = []
    for n, link in enumerate(order, start=1):
        art = articles[link]
        # restore original reading order within the article
        ordered = sorted(art["chunks"], key=lambda c: c[0])
        content = "\n\n".join(text for _, text in ordered)
        blocks.append(
            f"[Article {n}]\nTitle: {art['title']}\nDate: {art['date']}\n"
            f"Source: {art['link']}\nContent: {content}"
        )

    parsed_response = f"[User's question]\nQuestion: {query}\n\n" + "\n\n".join(blocks)

    
    system_prompt = (
        f"{RETRIEVER_SYSTEM_PROMPT}\n\nFor recency judgments: today's date is "
        f"{date.today().isoformat()}. Compare each article's Date against it."
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": parsed_response},
        ],
    )

    print(f"finalnyi response z llmki: {response.choices[0].message.content}")

    return response.choices[0].message.content


def retrieve_articles(query, top_k=6):
    load_dotenv(dotenv_path=".env")

    vectorized_request = embedding_openai(query)
    if not vectorized_request:
        return []

    apikey_pinecone = os.getenv("APIKEY_PINECONE")
    pc = Pinecone(api_key=apikey_pinecone)
    dense_index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))  # type: ignore

    response = dense_index.query(  # type: ignore
        namespace="sosomuzika",
        vector=vectorized_request,
        top_k=top_k,
        include_metadata=True,
        include_values=False,
    )

    articles = {}
    order = []
    for match in response.matches:  # type: ignore
        md = match.metadata
        link = md.get("articleLink", "")
        if link not in articles:
            articles[link] = {
                "articleTitle": md.get("articleTitle", ""),
                "articleLink": link,
                "score": match.score,  # matches arrive sorted, so this is the article's best chunk
                "chunks": [],
            }
            order.append(link)
        text = md.get("chunk_text", md.get("summary", ""))
        articles[link]["chunks"].append((_chunk_index(md.get("chunk_index")), text))

    results = []
    for link in order:
        art = articles[link]
        ordered = sorted(art["chunks"], key=lambda c: c[0])
        results.append(
            {
                "articleTitle": art["articleTitle"],
                "articleLink": art["articleLink"],
                "score": art["score"],
                "text": "\n\n".join(text for _, text in ordered),
            }
        )
    return results


if __name__ == "__main__":
    load_dotenv(".env")
    process_user_query(query=query)
