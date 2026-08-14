#!/usr/bin/env bash
# Quick health check for the API, Streamlit UI, and FinOps data path.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API="${API_BASE:-http://127.0.0.1:8000}"
UI="${UI_BASE:-http://127.0.0.1:8501}"
FAILS=0

check() {
  local desc="$1" cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    echo "OK   $desc"
  else
    echo "FAIL $desc"
    FAILS=$((FAILS + 1))
  fi
}

check "API /health"        "curl -sf $API/health | grep -q '\"status\":\"ok\"'"
check "API /docs"          "curl -sf -o /dev/null $API/docs"
check "API /finops/kpis"   "curl -sf $API/finops/kpis?days=7 | grep -q total_spend_usd"
check "Streamlit UI up"    "curl -sf -o /dev/null $UI"

if [[ -d .venv ]]; then
  check "Unit tests (tests/test_finops.py)" \
    ".venv/bin/python -m unittest tests/test_finops.py"
else
  echo "SKIP unit tests — no .venv"
fi

echo
if [[ $FAILS -eq 0 ]]; then
  echo "All checks passed."
else
  echo "$FAILS check(s) failed."
fi
exit "$FAILS"
