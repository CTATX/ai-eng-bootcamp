"""ShopMonkey → warehouse ingest. Idempotent upserts; watermark in meta."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from server.shop_warehouse import connect, initialize
from server.shopmonkey_client import ShopmonkeyAPIError, list_orders

SOURCE = "shopmonkey"
DEFAULT_PAGE_SIZE = 25


def _pick(row: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    if not row:
        return default
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def _meta_get(connection, key: str) -> str | None:
    row = connection.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def _meta_set(connection, key: str, value: str) -> None:
    connection.execute(
        "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )


def _cents_to_usd(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value) / 100.0, 2)
    except (TypeError, ValueError):
        return None


def _normalize_orders(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("data"), list):
            return [row for row in payload["data"] if isinstance(row, dict)]
        if isinstance(payload.get("orders"), list):
            return [row for row in payload["orders"] if isinstance(row, dict)]
    return []


def _vehicle_row(order: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    vehicle = order.get("vehicle")
    vehicle_id = _pick(order, "vehicleId") or _pick(vehicle, "id")
    if not vehicle_id:
        return None
    return (
        str(vehicle_id),
        {
            "id": str(vehicle_id),
            "make": _pick(vehicle, "make", default="Unknown"),
            "model": _pick(vehicle, "model", default="Unknown"),
            "year": int(_pick(vehicle, "year", default=0) or 0),
            "engine": _pick(vehicle, "engine", "submodel"),
            "vin": _pick(vehicle, "vin"),
            "source": SOURCE,
        },
    )


def _order_row(order: dict[str, Any], vehicle_id: str) -> dict[str, Any]:
    opened = (
        _pick(order, "orderCreatedDate", "createdDate", "updatedDate")
        or datetime.now(UTC).isoformat()
    )
    total = _cents_to_usd(_pick(order, "totalCostCents", "paidCostCents"))
    labor_hours = _pick(order, "totalLaborHours", "laborHours")
    try:
        labor_hours = float(labor_hours) if labor_hours is not None else None
    except (TypeError, ValueError):
        labor_hours = None
    return {
        "id": str(_pick(order, "id")),
        "vehicle_id": vehicle_id,
        "opened_at": opened,
        "total_usd": total,
        "labor_hours": labor_hours,
        "comeback": 0,
        "source": SOURCE,
    }


def _service_rows(order: dict[str, Any]) -> list[dict[str, Any]]:
    order_id = str(_pick(order, "id"))
    rows: list[dict[str, Any]] = []
    for service in order.get("services") or []:
        if not isinstance(service, dict):
            continue
        service_id = _pick(service, "id")
        name = _pick(service, "name", "generatedName", "coalescedName", default="Service")
        if not service_id:
            continue
        rows.append(
            {
                "id": str(service_id),
                "order_id": order_id,
                "reason": str(name),
                "source": SOURCE,
                "recommended": bool(service.get("recommended")),
            }
        )
    complaint = _pick(order, "complaint")
    if complaint and not rows:
        rows.append(
            {
                "id": f"{order_id}-complaint",
                "order_id": order_id,
                "reason": str(complaint),
                "source": SOURCE,
                "recommended": False,
            }
        )
    return rows


def _part_rows(order: dict[str, Any]) -> list[dict[str, Any]]:
    order_id = str(_pick(order, "id"))
    rows: list[dict[str, Any]] = []
    for service in order.get("services") or []:
        if not isinstance(service, dict):
            continue
        for part in service.get("parts") or []:
            if not isinstance(part, dict):
                continue
            part_id = _pick(part, "id")
            if not part_id:
                continue
            sku = _pick(part, "partNumber", default=f"SM-{part_id}")
            rows.append(
                {
                    "id": str(part_id),
                    "order_id": order_id,
                    "sku": str(sku),
                    "name": str(_pick(part, "name", default="Part")),
                    "qty": int(_pick(part, "quantity", default=1) or 1),
                    "unit_usd": _cents_to_usd(_pick(part, "retailCostCents", "wholesaleCostCents")),
                    "source": SOURCE,
                }
            )
    return rows


def _gotcha_rows(order: dict[str, Any], services: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order_id = str(_pick(order, "id"))
    rows: list[dict[str, Any]] = []
    for service in services:
        if not service.get("recommended"):
            continue
        rows.append(
            {
                "id": f"gotcha-{order_id}-{service['id']}",
                "order_id": order_id,
                "kind": "deferred_service",
                "label": f"Recommended not sold: {service['reason']}",
                "source": SOURCE,
            }
        )
    recommendation = _pick(order, "recommendation")
    if recommendation:
        rows.append(
            {
                "id": f"gotcha-{order_id}-recommendation",
                "order_id": order_id,
                "kind": "advisor_note",
                "label": str(recommendation)[:240],
                "source": SOURCE,
            }
        )
    return rows


def upsert_order(connection, order: dict[str, Any]) -> dict[str, int]:
    counts = {"vehicles": 0, "orders": 0, "services": 0, "parts": 0, "gotchas": 0}
    vehicle = _vehicle_row(order)
    if not vehicle:
        return counts
    vehicle_id, vehicle_payload = vehicle
    connection.execute(
        """
        INSERT INTO vehicles (id, make, model, year, engine, vin, source)
        VALUES (:id, :make, :model, :year, :engine, :vin, :source)
        ON CONFLICT(id) DO UPDATE SET
            make = excluded.make,
            model = excluded.model,
            year = excluded.year,
            engine = excluded.engine,
            vin = excluded.vin,
            source = excluded.source
        """,
        vehicle_payload,
    )
    counts["vehicles"] = 1

    order_payload = _order_row(order, vehicle_id)
    connection.execute(
        """
        INSERT INTO orders (id, vehicle_id, opened_at, total_usd, labor_hours, comeback, source)
        VALUES (:id, :vehicle_id, :opened_at, :total_usd, :labor_hours, :comeback, :source)
        ON CONFLICT(id) DO UPDATE SET
            vehicle_id = excluded.vehicle_id,
            opened_at = excluded.opened_at,
            total_usd = excluded.total_usd,
            labor_hours = excluded.labor_hours,
            comeback = excluded.comeback,
            source = excluded.source
        """,
        order_payload,
    )
    counts["orders"] = 1

    services = _service_rows(order)
    for row in services:
        connection.execute(
            """
            INSERT INTO order_services (id, order_id, reason, source)
            VALUES (:id, :order_id, :reason, :source)
            ON CONFLICT(id) DO UPDATE SET
                order_id = excluded.order_id,
                reason = excluded.reason,
                source = excluded.source
            """,
            {k: v for k, v in row.items() if k != "recommended"},
        )
        counts["services"] += 1

    for row in _part_rows(order):
        connection.execute(
            """
            INSERT INTO order_parts (id, order_id, sku, name, qty, unit_usd, source)
            VALUES (:id, :order_id, :sku, :name, :qty, :unit_usd, :source)
            ON CONFLICT(id) DO UPDATE SET
                order_id = excluded.order_id,
                sku = excluded.sku,
                name = excluded.name,
                qty = excluded.qty,
                unit_usd = excluded.unit_usd,
                source = excluded.source
            """,
            row,
        )
        counts["parts"] += 1

    for row in _gotcha_rows(order, services):
        connection.execute(
            """
            INSERT INTO gotcha_events (id, order_id, kind, label, source)
            VALUES (:id, :order_id, :kind, :label, :source)
            ON CONFLICT(id) DO UPDATE SET
                order_id = excluded.order_id,
                kind = excluded.kind,
                label = excluded.label,
                source = excluded.source
            """,
            row,
        )
        counts["gotchas"] += 1

    return counts


def ingest_status() -> dict[str, Any]:
    initialize()
    with connect() as connection:
        skip = int(_meta_get(connection, "ingest_watermark_skip") or "0")
        last_run = _meta_get(connection, "ingest_last_run")
        last_error = _meta_get(connection, "ingest_last_error")
        sm_orders = connection.execute(
            "SELECT COUNT(*) AS n FROM orders WHERE source = ?",
            (SOURCE,),
        ).fetchone()["n"]
    return {
        "watermark_skip": skip,
        "last_run": last_run,
        "last_error": last_error,
        "shopmonkey_orders": sm_orders,
    }


def ingest_orders(
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    max_pages: int | None = None,
    start_skip: int | None = None,
) -> dict[str, Any]:
    """Paginate ShopMonkey orders into the warehouse. Resumes from watermark."""
    initialize()
    totals = {"pages": 0, "orders": 0, "vehicles": 0, "services": 0, "parts": 0, "gotchas": 0}
    skip = start_skip
    if skip is None:
        with connect() as connection:
            skip = int(_meta_get(connection, "ingest_watermark_skip") or "0")

    page = 0
    while True:
        if max_pages is not None and page >= max_pages:
            break
        try:
            payload = list_orders(limit=page_size, skip=skip)
        except ShopmonkeyAPIError as exc:
            with connect() as connection:
                _meta_set(connection, "ingest_last_error", str(exc.message))
                connection.commit()
            raise

        orders = _normalize_orders(payload)
        if not orders:
            break

        with connect() as connection:
            for order in orders:
                row_counts = upsert_order(connection, order)
                for key in ("vehicles", "orders", "services", "parts", "gotchas"):
                    totals[key] += row_counts[key]
            skip += len(orders)
            _meta_set(connection, "ingest_watermark_skip", str(skip))
            _meta_set(connection, "ingest_last_run", datetime.now(UTC).isoformat())
            _meta_set(connection, "ingest_last_error", "")
            _meta_set(
                connection,
                "disclaimer",
                "Mixed warehouse: synthetic prototype and/or ShopMonkey ingest. Not live vendor inventory.",
            )
            sources = {
                row["source"]
                for row in connection.execute("SELECT DISTINCT source FROM orders").fetchall()
            }
            if len(sources) > 1:
                _meta_set(connection, "source", "mixed")
            elif SOURCE in sources:
                _meta_set(connection, "source", SOURCE)
            connection.commit()

        totals["pages"] += 1
        page += 1
        if len(orders) < page_size:
            break
        time.sleep(0.2)

    totals["watermark_skip"] = skip
    return totals
