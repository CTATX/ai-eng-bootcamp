"""Official ShopMonkey REST v3 client. Integration only — no UI scrape or reskin."""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv

from server.shopmonkey_catalog import SHOPMONKEY_BASE_URL

load_dotenv()

DEFAULT_TIMEOUT_SECONDS = 20


class ShopmonkeyConfigError(ValueError):
    """Raised when SHOPMONKEY_API_KEY is missing."""


class ShopmonkeyAPIError(RuntimeError):
    """Raised when ShopMonkey returns a non-success response."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def api_key_configured() -> bool:
    key = os.getenv("SHOPMONKEY_API_KEY", "").strip()
    return bool(key) and not key.startswith("replace-me")


def _headers() -> dict[str, str]:
    key = os.getenv("SHOPMONKEY_API_KEY", "").strip()
    if not key or key.startswith("replace-me"):
        raise ShopmonkeyConfigError(
            "SHOPMONKEY_API_KEY is missing. Copy .env.example to .env and add a "
            "key from ShopMonkey Settings → Integration → API Keys."
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
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> Any:
    url = f"{SHOPMONKEY_BASE_URL}{path}"
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
            "ShopMonkey key is valid but lacks permission. Keys inherit the creating admin.",
        )
    if response.status_code == 429:
        raise ShopmonkeyAPIError(429, "ShopMonkey rate limit hit. Retry after the Retry-After header.")
    if response.status_code >= 400:
        detail = response.text
        try:
            body = response.json()
            detail = body.get("message") or body.get("detail") or detail
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
            "include[customer]": True,
            "include[vehicle]": True,
        },
    )


def search_customers(limit: int = 25, skip: int = 0) -> Any:
    return request_json(
        "POST",
        "/customer/search",
        json={"limit": limit, "skip": skip},
    )


def list_appointments(limit: int = 25, skip: int = 0) -> Any:
    return request_json("GET", "/appointment", params={"limit": limit, "skip": skip})


def list_users(limit: int = 25, skip: int = 0) -> Any:
    return request_json("GET", "/user", params={"limit": limit, "skip": skip})
