"""Official ShopMonkey REST v3 client. Integration only — not a reskin."""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.shopmonkey.cloud/v3"
DEFAULT_TIMEOUT = 30


class ShopmonkeyConfigError(ValueError):
    """SHOPMONKEY_API_KEY missing or placeholder."""


class ShopmonkeyAPIError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def api_key_configured() -> bool:
    key = os.getenv("SHOPMONKEY_API_KEY", "").strip()
    return bool(key) and not key.lower().startswith("replace")


def _headers() -> dict[str, str]:
    key = os.getenv("SHOPMONKEY_API_KEY", "").strip()
    if not key or key.lower().startswith("replace"):
        raise ShopmonkeyConfigError(
            "SHOPMONKEY_API_KEY is missing. In ShopMonkey: Settings → Integration → "
            "API Keys → Add New Key. Put it in .env (never commit)."
        )
    return {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _unwrap(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def request_json(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Any:
    url = f"{BASE_URL}{path}"
    try:
        response = requests.request(
            method,
            url,
            headers=_headers(),
            params=params,
            json=json,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise ShopmonkeyAPIError(502, f"ShopMonkey request failed: {exc}") from exc

    if response.status_code == 401:
        raise ShopmonkeyAPIError(401, "ShopMonkey rejected the API key.")
    if response.status_code == 403:
        raise ShopmonkeyAPIError(
            403,
            "Valid key but insufficient permission. Keys inherit the creating admin.",
        )
    if response.status_code == 429:
        raise ShopmonkeyAPIError(429, "Rate limited. Check Retry-After and backoff.")
    if response.status_code >= 400:
        detail = response.text
        try:
            body = response.json()
            detail = body.get("message") or detail
        except ValueError:
            pass
        raise ShopmonkeyAPIError(response.status_code, str(detail))

    if not response.content:
        return None
    return _unwrap(response.json())


def auth_status() -> Any:
    return request_json("GET", "/auth/api_key/status")


def list_orders(limit: int = 25, skip: int = 0) -> Any:
    return request_json(
        "GET",
        "/order",
        params={
            "limit": limit,
            "skip": skip,
            "include[customer]": "true",
            "include[vehicle]": "true",
            "include[services]": "true",
        },
    )
