"""Official ShopMonkey REST v3 client. Integration only — not a reskin."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

# Load autozyte/.env even when CLI is run from another cwd
_AUTOZYTE_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_AUTOZYTE_ROOT / ".env")
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


def list_orders(
    limit: int = 25,
    skip: int = 0,
    *,
    where: dict[str, Any] | None = None,
    orderby: str | None = None,
) -> Any:
    """List orders. Optional `where` is JSON-encoded per ShopMonkey v3 (e.g. {"number": 1234})."""
    params: dict[str, Any] = {"limit": limit, "skip": skip}
    if where:
        params["where"] = json.dumps(where)
    if orderby:
        params["orderby"] = orderby
    return request_json("GET", "/order", params=params)


def find_orders_by_number(ticket_number: str | int) -> list[dict[str, Any]]:
    """Find work orders by ShopMonkey ticket number (RO #)."""
    raw = str(ticket_number).strip().lstrip("#")
    if not raw:
        return []

    candidates: list[Any] = [raw]
    if raw.isdigit():
        candidates.extend([int(raw), str(int(raw))])

    seen: set[str] = set()
    matches: list[dict[str, Any]] = []
    for candidate in candidates:
        payload = list_orders(limit=10, where={"number": candidate})
        rows = payload if isinstance(payload, list) else []
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            rows = payload["data"]
        for row in rows:
            if isinstance(row, dict):
                order_id = str(row.get("id") or "")
                if order_id and order_id not in seen:
                    seen.add(order_id)
                    matches.append(row)
        if matches:
            break
    return matches


def get_order(order_id: str) -> Any:
    return request_json("GET", f"/order/{order_id}")


def list_order_services(order_id: str) -> list[dict[str, Any]]:
    payload = request_json("GET", f"/order/{order_id}/service")
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def get_vehicle(vehicle_id: str) -> dict[str, Any] | None:
    payload = request_json("GET", f"/vehicle/{vehicle_id}")
    return payload if isinstance(payload, dict) else None


def lookup_vehicle_by_vin(vin: str) -> dict[str, Any] | None:
    """Shop record for VIN when present; may return validation-only payload."""
    payload = request_json("GET", f"/vehicle/vin/{vin.strip()}")
    if isinstance(payload, dict) and payload.get("id"):
        return payload
    return None


def list_vehicle_orders(
    vehicle_id: str,
    *,
    limit: int = 50,
    skip: int = 0,
) -> list[dict[str, Any]]:
    """All service orders linked to a vehicle."""
    payload = request_json(
        "GET",
        f"/vehicle/{vehicle_id}/order",
        params={"limit": limit, "skip": skip},
    )
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []
