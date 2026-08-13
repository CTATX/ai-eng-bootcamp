"""Shared HTTP helpers for Streamlit clients."""

from __future__ import annotations

import os

import requests

# Local default; set API_BASE=https://your-app.onrender.com to use cloud API
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000").rstrip("/")


def server_is_up() -> bool:
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False
