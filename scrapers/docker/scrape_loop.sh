#!/usr/bin/env bash
# Built-in scheduler for the scrapers container.
#
# Runs `python main.py` (all scrapers + Pinecone sync) on a fixed interval.
# A scrape run failing does NOT kill the loop — it logs and waits for the next
# tick. Tune via environment variables (see docker-compose.yml):
#   SCRAPE_INTERVAL_SECONDS  seconds between runs        (default 21600 = 6h)
#   RUN_ON_START             run immediately on boot     (default true)

set -uo pipefail

: "${SCRAPE_INTERVAL_SECONDS:=21600}"
: "${RUN_ON_START:=true}"

run_scrape() {
  echo "[scheduler] $(date -u '+%Y-%m-%dT%H:%M:%SZ') starting scrape run"
  if python main.py; then
    echo "[scheduler] $(date -u '+%Y-%m-%dT%H:%M:%SZ') run finished OK"
  else
    echo "[scheduler] $(date -u '+%Y-%m-%dT%H:%M:%SZ') run FAILED (exit $?), continuing"
  fi
}

if [ "${RUN_ON_START}" = "true" ]; then
  run_scrape
fi

while true; do
  echo "[scheduler] sleeping ${SCRAPE_INTERVAL_SECONDS}s until next run"
  sleep "${SCRAPE_INTERVAL_SECONDS}"
  run_scrape
done
