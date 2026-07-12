#!/usr/bin/env bash
# Start the chat UI (FastAPI + uvicorn) on http://localhost:8000 (DYP-41)
set -e
cd "$(dirname "$0")/app"
exec .venv/bin/python frontend.py
