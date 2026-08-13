"""Shared HTTP helpers for Streamlit clients."""

from __future__ import annotations

import requests

API_BASE = "http://127.0.0.1:8000"


def server_is_up() -> bool:
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False
