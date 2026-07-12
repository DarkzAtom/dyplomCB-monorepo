#!/usr/bin/env bash
# Run every scraper once and sync the results to Pinecone (DYP-41)
set -e
cd "$(dirname "$0")/scrapers"
exec .venv/bin/python main.py
