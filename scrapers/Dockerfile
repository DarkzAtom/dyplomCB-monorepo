# Scrapers image: runs all sources + Pinecone sync on a schedule.
#
# Based on the official Playwright image so Chromium + all OS deps are already
# present and the browser version matches playwright==1.52.0 (see DOCKER.md).
FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# requirements-docker.txt is a full lockfile of the working venv (the committed
# scrapers/requirements.txt is incomplete: the code also needs openai, pinecone
# and the langchain-* packages). See DOCKER.md.
COPY requirements-docker.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt

# Application code. State files (lastsaved_articlelink.txt, output.csv) live
# under scrapers/scrapers/<source>/ and are bind-mounted from the host at run
# time (see docker-compose.yml) so they persist across runs.
COPY . .

ENTRYPOINT ["bash", "/app/docker/scrape_loop.sh"]
