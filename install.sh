#!/usr/bin/env bash
# One-shot installer for the whole project (DYP-41): creates both virtualenvs,
# installs dependencies and the Playwright browsers, and checks that the .env
# files with the API keys are in place.
#
#   ./install.sh
#
# afterwards:
#   ./run_app.sh        # chat UI on http://localhost:8000
#   ./run_scrapers.sh   # scrape all sources + sync to Pinecone
#
# (containerized alternative: docker compose up --build)

set -e
cd "$(dirname "$0")"

# the project targets Python 3.11 — prefer it when available
if command -v python3.11 >/dev/null 2>&1; then
    PY=python3.11
else
    PY=python3
    echo "warning: python3.11 not found, falling back to $($PY --version 2>&1)"
fi

# NB: always `python -m pip`, not `.venv/bin/pip` — the venvs in this repo
# were moved from an older project folder and the pip script shebangs still
# point at the old absolute path
echo "== app: virtualenv + dependencies =="
[ -d app/.venv ] || "$PY" -m venv app/.venv
app/.venv/bin/python -m pip install -q --upgrade pip
app/.venv/bin/python -m pip install -r app/requirements.txt

echo "== scrapers: virtualenv + dependencies =="
[ -d scrapers/.venv ] || "$PY" -m venv scrapers/.venv
scrapers/.venv/bin/python -m pip install -q --upgrade pip
scrapers/.venv/bin/python -m pip install -r scrapers/requirements.txt

echo "== scrapers: playwright browsers =="
(cd scrapers && .venv/bin/python -m playwright install chromium)
# securityweek launches with channel='chrome' and needs real Chrome
(cd scrapers && .venv/bin/python -m playwright install chrome) ||
    echo "warning: couldn't install the Chrome channel (securityweek uses it) — install Google Chrome manually"

echo "== checking .env files =="
for envfile in app/.env scrapers/.env; do
    if [ ! -f "$envfile" ]; then
        echo "MISSING: $envfile — create it with OPENAI_APIKEY, APIKEY_PINECONE, PINECONE_INDEX_NAME"
    else
        for key in OPENAI_APIKEY APIKEY_PINECONE PINECONE_INDEX_NAME; do
            grep -q "$key" "$envfile" || echo "WARNING: $key missing in $envfile"
        done
    fi
done

echo
echo "done. next steps:"
echo "  ./run_app.sh        # chat UI on http://localhost:8000"
echo "  ./run_scrapers.sh   # scrape all sources + sync to Pinecone"
