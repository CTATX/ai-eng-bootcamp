"""ShopMonkey → warehouse ingest. Idempotent upserts; watermark in meta."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from shop.warehouse import connect, initialize
from shop.shopmonkey_client import (
    ShopmonkeyAPIError,
    find_orders_by_number,
    get_order,
    get_vehicle,
    list_order_services,
    list_orders,
    list_vehicle_orders,
    lookup_vehicle_by_vin,
)

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


def _enrich_order(order: dict[str, Any]) -> dict[str, Any]:
    """Fetch full order + services + vehicle — list responses are often sparse."""
    order_id = str(_pick(order, "id") or "")
    if not order_id:
        return order

    try:
        detail = get_order(order_id)
        if isinstance(detail, dict):
            order = {**order, **detail}
    except ShopmonkeyAPIError:
        pass

    if not order.get("services"):
        try:
            services = list_order_services(order_id)
            if services:
                order["services"] = services
        except ShopmonkeyAPIError:
            pass

    vehicle_id = _pick(order, "vehicleId") or _pick(order.get("vehicle"), "id")
    embedded = order.get("vehicle") if isinstance(order.get("vehicle"), dict) else {}
    needs_vehicle = not embedded or not _pick(embedded, "vin", "make", "model", "year")
    if vehicle_id and needs_vehicle:
        try:
            vehicle = get_vehicle(str(vehicle_id))
            if vehicle:
                order["vehicle"] = {**embedded, **vehicle}
        except ShopmonkeyAPIError:
            pass

    return order


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
            make = CASE
                WHEN excluded.make = 'Unknown' AND vehicles.make != 'Unknown' THEN vehicles.make
                ELSE excluded.make
            END,
            model = CASE
                WHEN excluded.model = 'Unknown' AND vehicles.model != 'Unknown' THEN vehicles.model
                ELSE excluded.model
            END,
            year = CASE
                WHEN excluded.year = 0 AND vehicles.year != 0 THEN vehicles.year
                ELSE excluded.year
            END,
            engine = COALESCE(excluded.engine, vehicles.engine),
            vin = COALESCE(excluded.vin, vehicles.vin),
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
                row_counts = upsert_order(connection, _enrich_order(order))
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


def _merge_counts(totals: dict[str, int], row_counts: dict[str, int]) -> None:
    for key in ("vehicles", "orders", "services", "parts", "gotchas"):
        totals[key] += row_counts[key]


def ingest_one_order(order: dict[str, Any]) -> dict[str, int]:
    """Enrich and upsert a single ShopMonkey order into the warehouse."""
    initialize()
    enriched = _enrich_order(order)
    with connect() as connection:
        counts = upsert_order(connection, enriched)
        _meta_set(connection, "ingest_last_run", datetime.now(UTC).isoformat())
        _meta_set(connection, "ingest_last_error", "")
        connection.commit()
    return counts


def ingest_order_by_id(order_id: str) -> dict[str, Any]:
    """Pull one order by ShopMonkey id (UUID), with full vehicle + services."""
    order = get_order(order_id)
    if not isinstance(order, dict):
        raise ShopmonkeyAPIError(404, f"No order found for id {order_id}")
    counts = ingest_one_order(order)
    vehicle_id = _pick(order, "vehicleId") or _pick(order.get("vehicle"), "id")
    return {"order_id": str(_pick(order, "id")), "vehicle_id": vehicle_id, **counts}


def ingest_order_by_ticket(ticket_number: str | int, *, pull_vehicle_history: bool = True) -> dict[str, Any]:
    """Pull the work order matching a ShopMonkey ticket / RO number."""
    matches = find_orders_by_number(ticket_number)
    if not matches:
        raise ShopmonkeyAPIError(
            404,
            f"No order found with ticket number {ticket_number!r}. "
            "Use the RO # from ShopMonkey (numbers only, no #).",
        )

    order = matches[0]
    counts = ingest_one_order(order)
    vehicle_id = _pick(order, "vehicleId") or _pick(order.get("vehicle"), "id")
    result: dict[str, Any] = {
        "ticket": str(ticket_number).strip().lstrip("#"),
        "order_id": str(_pick(order, "id")),
        "vehicle_id": vehicle_id,
        "matches": len(matches),
        **counts,
    }

    if pull_vehicle_history and vehicle_id:
        history = ingest_vehicle_orders(str(vehicle_id))
        result["vehicle_history"] = history

    with connect() as connection:
        vin_row = connection.execute(
            "SELECT vin, make, model, year FROM vehicles WHERE id = ?",
            (str(vehicle_id),),
        ).fetchone()
    if vin_row:
        result["vin"] = vin_row["vin"]
        result["vehicle"] = {
            "make": vin_row["make"],
            "model": vin_row["model"],
            "year": vin_row["year"],
        }

    return result


def ingest_vehicle_orders(vehicle_id: str, *, page_size: int = 50, max_pages: int = 20) -> dict[str, int]:
    """Pull all known orders for a vehicle id into the warehouse."""
    initialize()
    totals = {"pages": 0, "orders": 0, "vehicles": 0, "services": 0, "parts": 0, "gotchas": 0}
    skip = 0
    for _ in range(max_pages):
        batch = list_vehicle_orders(vehicle_id, limit=page_size, skip=skip)
        if not batch:
            break
        with connect() as connection:
            for order in batch:
                _merge_counts(totals, upsert_order(connection, _enrich_order(order)))
            connection.commit()
        totals["pages"] += 1
        skip += len(batch)
        if len(batch) < page_size:
            break
    return totals


def ensure_vehicle_for_vin(vin: str) -> bool:
    """Backfill warehouse from ShopMonkey when VIN is missing locally."""
    vin = vin.strip()
    if not vin:
        return False

    initialize()
    with connect() as connection:
        row = connection.execute(
            "SELECT id FROM vehicles WHERE vin = ? COLLATE NOCASE",
            (vin,),
        ).fetchone()
        if row:
            return True

    vehicle = lookup_vehicle_by_vin(vin)
    if vehicle and vehicle.get("id"):
        ingest_vehicle_orders(str(vehicle["id"]))
        return True

    # Fallback: scan recent orders for matching embedded vehicle VIN.
    skip = 0
    page_size = 50
    for _ in range(10):
        payload = list_orders(limit=page_size, skip=skip)
        orders = _normalize_orders(payload)
        if not orders:
            break
        for order in orders:
            enriched = _enrich_order(order)
            embedded = enriched.get("vehicle") if isinstance(enriched.get("vehicle"), dict) else {}
            order_vin = _pick(embedded, "vin")
            if order_vin and str(order_vin).upper() == vin.upper():
                ingest_one_order(enriched)
                vehicle_id = _pick(enriched, "vehicleId") or _pick(embedded, "id")
                if vehicle_id:
                    ingest_vehicle_orders(str(vehicle_id))
                return True
        skip += len(orders)
        if len(orders) < page_size:
            break

    return False
