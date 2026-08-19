"""Unified system status — same payload for CLI, API, and Streamlit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shop.ingest import ingest_status
from shop.service import status as warehouse_status
from shop.shopmonkey_client import ShopmonkeyAPIError, api_key_configured, auth_status
from shop.synthetic import seed_if_empty

_VERSION_FILE = Path(__file__).resolve().parents[1] / "VERSION"


def product_version() -> str:
    try:
        return _VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "dev"


def build_system_status(*, probe_shopmonkey: bool = True) -> dict[str, Any]:
    """Mirror of `python -m shop.cli status` for API and UI."""
    seed_if_empty()
    payload: dict[str, Any] = {
        "product": "AutoZyte",
        "version": product_version(),
        "warehouse": warehouse_status(),
        "ingest": ingest_status(),
        "shopmonkey_key_configured": api_key_configured(),
    }
    if probe_shopmonkey and api_key_configured():
        try:
            payload["shopmonkey_auth"] = auth_status()
        except ShopmonkeyAPIError as exc:
            payload["shopmonkey_auth_error"] = {
                "status": exc.status_code,
                "message": exc.message,
            }
    return payload
