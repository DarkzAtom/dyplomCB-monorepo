# Scrapers image: runs all sources + Pinecone sync on a schedule.
#
# Base is python:3.11-slim to exactly match the venv that requirements-docker.txt
# was frozen on (Python 3.11). The official Playwright images only ship Python
# 3.10 (jammy) or 3.12 (noble) — neither matches 3.11, and 3.12 drops the bundled
# setuptools that playwright-stealth's pkg_resources import needs. So instead of
# the Playwright base image, we install the browser + its OS deps ourselves with
# `playwright install --with-deps` (see below). See DOCKER.md.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# requirements-docker.txt is a full lockfile of the working venv (the committed
# scrapers/requirements.txt is incomplete: the code also needs openai, pinecone
# and the langchain-* packages). See DOCKER.md.
COPY requirements-docker.txt ./
RUN pip install --no-cache-dir -r requirements-docker.txt

# Browsers + their OS libraries. The slim base ships neither (the Playwright
# image would have, but it has no 3.11 variant). We can't use `playwright install
# --with-deps` here: its auto dep-installer only knows Ubuntu and chokes on this
# Debian base (missing ttf-* font packages abort apt). So install the documented
# runtime libs explicitly, then download the browsers:
#   - chromium: the bundled browser used by the *_links_collector scrapers.
#   - chrome:   real Google Chrome, required by the article processors that pass
#               channel='chrome' (thehackernews, securityweek, darkreading).
# Both use the pinned playwright==1.52.0 so versions stay matched.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
      libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 libxext6 \
      libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    && playwright install chromium \
    && playwright install chrome \
    && rm -rf /var/lib/apt/lists/*

# Application code. State files (lastsaved_articlelink.txt, output.csv) live
# under scrapers/scrapers/<source>/ and are bind-mounted from the host at run
# time (see docker-compose.yml) so they persist across runs.
COPY . .

ENTRYPOINT ["bash", "/app/docker/scrape_loop.sh"]
