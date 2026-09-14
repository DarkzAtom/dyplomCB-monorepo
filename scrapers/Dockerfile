# Scrapers image: runs all sources + Pinecone sync on a schedule.
# python:3.11-slim to match the venv (3.11). The Playwright base images are
# 3.10/3.12 only, so we install the browsers ourselves below.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
      libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
      libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 libxdamage1 libxext6 \
      libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    && playwright install chromium \
    && playwright install chrome \
    && rm -rf /var/lib/apt/lists/*


COPY . .

ENTRYPOINT ["bash", "/app/docker/scrape_loop.sh"]
