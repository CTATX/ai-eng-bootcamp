#!/usr/bin/env bash
# Idempotent dependency refresh for the AI Eng Bootcamp Cloud Agent environment.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# python3.12-venv provides ensurepip, which the default image lacks.
if ! dpkg -s python3.12-venv >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3.12-venv
fi

# Create the virtualenv if missing (venv creation is safe to re-run).
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
fi

.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo "Install complete: $(.venv/bin/python --version)"
