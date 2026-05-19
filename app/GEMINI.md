# Project Overview: dyplomCB_FastDenis

This project is a Retrieval-Augmented Generation (RAG) application that allows users to chat with a collection of articles. It uses OpenAI for embeddings and language generation, Pinecone as a vector database for similarity search, and FastAPI for the web-based chat interface.

## Core Technologies
- **Backend:** Python, FastAPI, Uvicorn
- **AI/ML:** OpenAI (GPT-4, text-embedding-3-small), Pinecone (Vector Database)
- **Frontend:** HTML/CSS/JS (Static files), Jinja2 (implied by file serving)
- **Data:** CSV (input data source)
- **Environment Management:** `python-dotenv`

## Project Structure
- `main.py`: Script for indexing articles from `output.csv` into Pinecone. It handles embedding generation and vector upsertion.
- `frontend.py`: The FastAPI application server. It serves the chat interface and handles the `/chat` endpoint.
- `retriever.py`: Logic for processing user queries, optimizing search terms, querying Pinecone, and generating the final conversational response.
- `similarity_search.py`: Helper functions for generating OpenAI embeddings and performing standalone Pinecone queries.
- `static/`: Contains the frontend assets (`chat.html`).
- `requirements.txt`: Project dependencies.
- `backlog.txt`: Tracks completed and pending tasks/bugs.
- `output.csv`: The dataset containing articles (Title, Link, Text).

## Building and Running

### Prerequisites
- Python 3.x
- OpenAI API Key
- Pinecone API Key and Index

### Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment variables in a `.env` file (see `env.example` for required keys):
   - `OPENAI_APIKEY`
   - `APIKEY_PINECONE`
   - `PINECONE_INDEX_NAME`

### Running the Application
1. **Indexing Data:** If you need to refresh the vector database with new articles:
   ```bash
   python main.py
   ```
2. **Starting the Web Server:**
   ```bash
   python frontend.py
   ```
   The application will be available at `http://0.0.0.0:8000`.

## Development Conventions

### Coding Style
- Follow PEP 8 guidelines for Python code.
- Use `dotenv` for all sensitive configuration and API keys.
- Prefer explicit type hints where possible (e.g., `ChatMessage(BaseModel)`).

### AI Logic
- **Query Optimization:** User queries are refined using a specialized prompt in `retriever.py` to extract core keywords before searching Pinecone.
- **System Prompts:** Instructional prompts for the AI are stored as constants in `retriever.py` (`RETRIEVER_SYSTEM_PROMPT`, `QUERY_FILTER_PROMPT`).

### TODOs / Next Steps (from `backlog.txt`)
- Integrate scrapers into a single project with a cron job.
- Improve out-of-context message handling.
- Implement relevance score filtering for search results.
- Fix UI bugs (newline on enter, summary key mapping).
