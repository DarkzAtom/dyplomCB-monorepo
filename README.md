# dyplomCB — cybersecurity-news RAG

Two parts sharing one Pinecone index:

- `scrapers/` — scrape cybersecurity-news sources, embed the articles, upsert to Pinecone.
- `app/` — FastAPI chat UI that answers questions from the indexed articles.

## Setup

Requires Python 3.11.

1. Create the two env files — `app/.env` and `scrapers/.env` — each with your keys:

   ```
   OPENAI_APIKEY=...
   APIKEY_PINECONE=...
   PINECONE_INDEX_NAME=...
   ```

   Optionally add `TELEGRAM_BOT_TOKEN=...` to `app/.env` to also run the Telegram bot.
2. Create both virtualenvs, install dependencies and the Playwright browsers:

   ```
   ./install.sh
   ```

## Run

```
./run_app.sh        # chat UI on http://localhost:8000
./run_scrapers.sh   # scrape every source once + sync to Pinecone
```

## Or with Docker

Still create the `.env` files (step 1). Then, instead of `install.sh` and the run
scripts, run everything in containers:

```
docker compose up --build
```

Runs the chat UI and a scheduled scraper loop.
