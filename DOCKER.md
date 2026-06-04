# Containerized deployment (DYP-40)

Runs the whole RAG system in Docker: the FastAPI chat **app** as an always-on
web server, and the **scrapers** as a self-scheduling batch job that periodically
collects articles and syncs them to Pinecone.

## Prerequisites

- Docker + Docker Compose v2 (`docker compose version`).
- A `.env` file in **both** `app/` and `scrapers/` with the three keys:
  ```
  OPENAI_APIKEY=...
  APIKEY_PINECONE=...
  PINECONE_INDEX_NAME=...
  ```
  (These are gitignored. `app/env.example` shows the shape.)

## Run

```bash
docker compose up --build        # build + run both services in the foreground
docker compose up -d             # ...or detached
docker compose logs -f scrapers  # watch scheduled scrape runs
docker compose down              # stop everything
```

- Chat UI: http://localhost:8000
- Scrapers: run once on start, then every `SCRAPE_INTERVAL_SECONDS` (default 6h).

## Design notes

**Two images, one Python each.**
- `app/` → `python:3.10-slim`, served by `uvicorn frontend:app` (no `--reload`).
- `scrapers/` → `mcr.microsoft.com/playwright/python:v1.52.0-jammy`, so Chromium
  and all OS libraries are preinstalled and the browser matches
  `playwright==1.52.0`.

**Scheduler.** The scrapers container runs `docker/scrape_loop.sh`, which calls
`python main.py` on an interval. Knobs (set in `docker-compose.yml`):
- `SCRAPE_INTERVAL_SECONDS` — seconds between runs (default `21600` = 6h).
- `RUN_ON_START` — run immediately on boot (default `true`).
A failed run is logged and the loop continues to the next tick.

**State persistence.** `docker-compose.yml` bind-mounts `./scrapers/scrapers`
into the container, so the incremental markers (`lastsaved_articlelink.txt`) and
each `output.csv` are written back to the host and survive restarts. Scraping
stays incremental. (`output.csv` still appends as before — cleaning that up is
tracked separately in DYP-38.)

**Secrets** are injected at runtime via `env_file` and never baked into images
(see the `.dockerignore` files). `env_file` is marked `required: false` so the
stack still builds in checkouts without a local `.env`, but the keys must be
present at run time.

**`requirements-docker.txt`** (scrapers) is a full lockfile generated from the
working virtualenv. The committed `scrapers/requirements.txt` is incomplete — the
code imports `openai`, `pinecone`, and the `langchain-*` packages that aren't
listed there — so the image installs from the lockfile instead.
