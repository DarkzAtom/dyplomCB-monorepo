#!/usr/bin/env bash
# Start the chat UI (FastAPI + uvicorn) on http://localhost:8000 (DYP-41)
set -e
cd "$(dirname "$0")/app"

# Both processes are children of this script: killing it (Ctrl-C) takes them down
# together, and if either one dies the other is not left running headless.
pids=()
cleanup() { kill "${pids[@]}" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

# The Telegram bot (DYP-50/DYP-54) is optional — it only runs once a token is
# configured, so the chat UI still starts on a checkout without one.
if grep -qsE '^TELEGRAM_BOT_TOKEN[[:space:]]*=' .env; then
    .venv/bin/python telegram_bot.py &
    pids+=($!)
    echo "[run_app] telegram bot polling (pid ${pids[-1]})"
else
    echo "[run_app] no TELEGRAM_BOT_TOKEN in app/.env - starting chat UI only"
fi

.venv/bin/python frontend.py &
pids+=($!)

# return as soon as either process exits, then let the trap stop the other
wait -n
