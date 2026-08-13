#!/usr/bin/env bash
# Boot AI Eng Bootcamp — API server + Streamlit UI (one command, two processes).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  echo "Missing .venv — run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if lsof -i :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Port 8000 already in use — API may already be running."
  echo "If not, stop it: lsof -i :8000  then  kill <PID>"
else
  echo "Starting API server on http://127.0.0.1:8000 ..."
  uvicorn server.main:app --reload --host 127.0.0.1 --port 8000 &
  UVICORN_PID=$!
  trap 'kill "$UVICORN_PID" 2>/dev/null || true' EXIT INT TERM

  for _ in {1..20}; do
    if curl -sf http://127.0.0.1:8000/health >/dev/null 2>&1; then
      echo "API ready."
      break
    fi
    sleep 0.25
  done
fi

echo "Starting Streamlit — sidebar: Cost Estimator | Bootcamp Q&A"
echo "Stop everything: Ctrl+C in this terminal."
streamlit run app.py
