"""Assemble ShopMonkey integration status and a read-only shop snapshot."""

from __future__ import annotations

from typing import Any

from server import shopmonkey_client
from server.shopmonkey_catalog import catalog as api_catalog


def _as_list(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        nested = value.get("data") or value.get("items") or value.get("results")
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
        return [value]
    return []


def _pick(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def _customer_name(row: dict[str, Any]) -> str | None:
    company = _pick(row, "companyName")
    if company:
        return str(company)
    first = _pick(row, "firstName", default="")
    last = _pick(row, "lastName", default="")
    name = f"{first} {last}".strip()
    return name or None


def _summarize_order(row: dict[str, Any]) -> dict[str, Any]:
    customer = row.get("customer") if isinstance(row.get("customer"), dict) else {}
    vehicle = row.get("vehicle") if isinstance(row.get("vehicle"), dict) else {}
    return {
        "id": _pick(row, "id"),
        "number": _pick(row, "number", "orderNumber", "name"),
        "status": _pick(row, "status", "workflowStatus", "coalescedName"),
        "customer": _customer_name(customer) or _pick(row, "customerId"),
        "vehicle": _pick(vehicle, "generatedName", "name", "vin") or _pick(row, "vehicleId"),
        "created_date": _pick(row, "createdDate"),
        "invoiced": _pick(row, "invoiced"),
    }


def _summarize_customer(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _pick(row, "id"),
        "name": _customer_name(row),
        "email": _pick(row, "email"),
        "phone": _pick(row, "phone", "phoneNumber"),
        "created_date": _pick(row, "createdDate"),
    }


def _summarize_appointment(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _pick(row, "id"),
        "status": _pick(row, "status"),
        "start": _pick(row, "startDate", "start", "scheduledStart"),
        "end": _pick(row, "endDate", "end", "scheduledEnd"),
        "customer_id": _pick(row, "customerId"),
        "vehicle_id": _pick(row, "vehicleId"),
        "order_id": _pick(row, "orderId"),
    }


def connection_status() -> dict[str, Any]:
    configured = shopmonkey_client.api_key_configured()
    if not configured:
        return {
            "configured": False,
            "connected": False,
            "message": (
                "Add SHOPMONKEY_API_KEY to .env. Generate it in ShopMonkey as an admin: "
                "Settings → Integration → API Keys."
            ),
            "auth": None,
        }
    auth = shopmonkey_client.auth_status()
    return {
        "configured": True,
        "connected": True,
        "message": "ShopMonkey API key accepted.",
        "auth": auth,
    }


def shop_snapshot(limit: int = 25) -> dict[str, Any]:
    status = connection_status()
    orders = _as_list(shopmonkey_client.list_orders(limit=limit))
    customers = _as_list(shopmonkey_client.search_customers(limit=limit))
    appointments = _as_list(shopmonkey_client.list_appointments(limit=limit))
    users = _as_list(shopmonkey_client.list_users(limit=limit))
    return {
        **status,
        "limit": limit,
        "orders": [_summarize_order(row) for row in orders],
        "customers": [_summarize_customer(row) for row in customers],
        "appointments": [_summarize_appointment(row) for row in appointments],
        "user_count": len(users),
    }


def catalog() -> dict[str, Any]:
    return api_catalog()
