"""Jake's data-based hypothesis — SQL on warehouse only. No LLM."""

from __future__ import annotations

import re
import statistics
from datetime import UTC, datetime
from typing import Any

from shop.synthetic import seed_if_empty
from shop.warehouse import connect

COMEBACK_DAYS = 30
MIN_N_FOR_INFERENCE = 1


def _pick(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 2)


def _complaint_tokens(complaint: str | None) -> list[str]:
    if not complaint:
        return []
    return [token for token in re.split(r"[^a-z0-9]+", complaint.lower()) if len(token) > 2]


def _match_vehicle(
    connection,
    *,
    vin: str | None,
    year: int | None,
    make: str | None,
    model: str | None,
    engine: str | None,
) -> tuple[list[dict[str, Any]], str, str]:
    if vin:
        rows = [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM vehicles WHERE vin = ? COLLATE NOCASE",
                (vin.strip(),),
            ).fetchall()
        ]
        if rows:
            return rows, "vin", f"VIN match on {len(rows)} vehicle(s)"
        return [], "unmatched", f"No vehicle with VIN {vin}"

    clauses: list[str] = []
    params: list[Any] = []
    if year is not None:
        clauses.append("year = ?")
        params.append(year)
    if make:
        clauses.append("LOWER(make) = LOWER(?)")
        params.append(make.strip())
    if model:
        clauses.append("LOWER(model) = LOWER(?)")
        params.append(model.strip())
    if engine:
        clauses.append("LOWER(engine) = LOWER(?)")
        params.append(engine.strip())

    if not clauses:
        return [], "unmatched", "Provide VIN or year + make + model"

    sql = f"SELECT * FROM vehicles WHERE {' AND '.join(clauses)}"
    rows = [dict(row) for row in connection.execute(sql, params).fetchall()]
    grain = "year_make_model_engine" if engine else "year_make_model"
    if rows:
        return rows, grain, f"{grain} match on {len(rows)} vehicle(s)"
    return [], "unmatched", "No matching vehicle in warehouse"


def build_hypothesis(
    *,
    vin: str | None = None,
    year: int | None = None,
    make: str | None = None,
    model: str | None = None,
    engine: str | None = None,
    complaint: str | None = None,
    mileage: int | None = None,
) -> dict[str, Any]:
    seed_if_empty()
    query_bits = [bit for bit in [vin, str(year or ""), make, model, engine, complaint] if bit]
    query = " · ".join(query_bits) or "empty intake"

    with connect() as connection:
        vehicles, grain, match_note = _match_vehicle(
            connection,
            vin=vin,
            year=year,
            make=make,
            model=model,
            engine=engine,
        )
        vehicle_ids = [row["id"] for row in vehicles]
        not_in_data: list[dict[str, str]] = []

        if not vehicle_ids:
            return _empty_packet(query, grain, match_note, not_in_data)

        placeholders = ",".join("?" for _ in vehicle_ids)
        orders = [
            dict(row)
            for row in connection.execute(
                f"""
                SELECT o.* FROM orders o
                WHERE o.vehicle_id IN ({placeholders})
                ORDER BY o.opened_at
                """,
                vehicle_ids,
            ).fetchall()
        ]
        order_ids = [row["id"] for row in orders]

        if not order_ids:
            not_in_data.append(
                {
                    "topic": "Shop history",
                    "why": "Vehicle matched but no orders in warehouse yet.",
                }
            )
            vehicle = vehicles[0]
            return _vehicle_only_packet(query, grain, match_note, vehicle, not_in_data)

        order_placeholders = ",".join("?" for _ in order_ids)
        services = [
            dict(row)
            for row in connection.execute(
                f"""
                SELECT * FROM order_services
                WHERE order_id IN ({order_placeholders})
                """,
                order_ids,
            ).fetchall()
        ]
        parts = [
            dict(row)
            for row in connection.execute(
                f"""
                SELECT * FROM order_parts
                WHERE order_id IN ({order_placeholders})
                """,
                order_ids,
            ).fetchall()
        ]
        gotchas = [
            dict(row)
            for row in connection.execute(
                f"""
                SELECT * FROM gotcha_events
                WHERE order_id IN ({order_placeholders})
                """,
                order_ids,
            ).fetchall()
        ]

    tokens = _complaint_tokens(complaint)
    reason_counts: dict[str, dict[str, Any]] = {}
    for service in services:
        label = service["reason"]
        bucket = reason_counts.setdefault(
            label,
            {"label": label, "order_ids": set(), "tag": "FACT", "source": "order_service_name"},
        )
        bucket["order_ids"].add(service["order_id"])
        if tokens and any(token in label.lower() for token in tokens):
            bucket["boost"] = bucket.get("boost", 0) + 1

    ranked_reasons = sorted(
        reason_counts.values(),
        key=lambda row: (row.get("boost", 0), len(row["order_ids"])),
        reverse=True,
    )
    total_services = len(services) or 1
    common_reasons = []
    for row in ranked_reasons[:8]:
        count = len(row["order_ids"])
        common_reasons.append(
            {
                "label": row["label"],
                "order_count": count,
                "share": round(count / total_services, 3),
                "source": row["source"],
                "tag": "FACT",
                "example_order_ids": sorted(row["order_ids"])[:5],
            }
        )

    selected_reason = common_reasons[0]["label"] if common_reasons else None
    selected_order_ids = (
        set(reason_counts[selected_reason]["order_ids"]) if selected_reason else set(order_ids)
    )

    part_stats: dict[str, dict[str, Any]] = {}
    for part in parts:
        if part["order_id"] not in selected_order_ids:
            continue
        key = part["sku"]
        bucket = part_stats.setdefault(
            key,
            {
                "name": part["name"],
                "sku": part["sku"],
                "times_sold": 0,
                "costs": [],
                "last_seen": None,
                "tag": "FACT",
            },
        )
        bucket["times_sold"] += part["qty"]
        if part["unit_usd"] is not None:
            bucket["costs"].append(float(part["unit_usd"]))
        opened = next((o["opened_at"] for o in orders if o["id"] == part["order_id"]), None)
        if opened and (bucket["last_seen"] is None or opened > bucket["last_seen"]):
            bucket["last_seen"] = opened[:10]

    parts_out = []
    for bucket in sorted(part_stats.values(), key=lambda r: r["times_sold"], reverse=True)[:12]:
        costs = bucket.pop("costs")
        bucket["avg_part_cost_usd"] = round(statistics.mean(costs), 2) if costs else None
        parts_out.append(bucket)

    ticket_amounts = [float(o["total_usd"]) for o in orders if o["total_usd"] is not None]
    hours_with = [float(o["labor_hours"]) for o in orders if o["labor_hours"] is not None]
    hours_missing = len(orders) - len(hours_with)

    dates = [o["opened_at"][:10] for o in orders if o["opened_at"]]
    vehicle = vehicles[0]

    gotcha_out: list[dict[str, Any]] = []
    by_kind: dict[str, list[str]] = {}
    for event in gotchas:
        by_kind.setdefault(event["kind"], []).append(event["order_id"])
    for kind, ids in by_kind.items():
        gotcha_out.append(
            {
                "kind": kind,
                "label": kind.replace("_", " "),
                "count": len(ids),
                "tag": "FACT",
                "source_order_ids": ids[:10],
            }
        )

    n = len(orders)
    likelihood_n = len(selected_order_ids) if selected_reason else n
    likelihood_pct = (
        round(100 * len(selected_order_ids) / n, 1) if selected_reason and n else None
    )

    not_in_data.extend(
        [
            {
                "topic": "Staff assignment",
                "why": "Orchestrator agent not built. ShopMonkey users exist but not mapped here.",
            },
            {
                "topic": "Tools and procedure steps",
                "why": "No licensed OEM/post-factory procedure library in warehouse.",
            },
            {
                "topic": "Live vendor inventory",
                "why": "Pelican/WorldPac require separate APIs — not ShopMonkey.",
            },
            {
                "topic": "3D model and torque specs",
                "why": "Separate content layer — slots only.",
            },
        ]
    )
    if mileage is not None:
        not_in_data.append(
            {
                "topic": "Mileage-based match",
                "why": "Mileage captured at intake but not stored per order in this warehouse cut.",
            }
        )
    if hours_missing:
        not_in_data.append(
            {
                "topic": "Labor hours",
                "why": f"{hours_missing} of {n} orders missing labor_hours in warehouse.",
            }
        )

    recommendations = []
    if selected_reason and likelihood_n >= MIN_N_FOR_INFERENCE:
        recommendations.append(
            {
                "action": f"Lead with shop history: {selected_reason}",
                "because": f"Seen on {len(selected_order_ids)} of {n} orders for this vehicle identity.",
                "tag": "INFERRED" if n < 5 else "FACT",
            }
        )
    if gotcha_out:
        recommendations.append(
            {
                "action": "Review gotcha rows before quoting ETA to customer",
                "because": "Comebacks and unsold inspection items are in shop history.",
                "tag": "FACT",
            }
        )

    return {
        "query": query,
        "generated_at": datetime.now(UTC).isoformat(),
        "persona": "Jake — service advisor",
        "vehicle_match": {
            "grain": grain,
            "identity": _pick(vehicle, "vin") or f"{vehicle['year']} {vehicle['make']} {vehicle['model']}",
            "year": vehicle.get("year"),
            "make": vehicle.get("make"),
            "model": vehicle.get("model"),
            "engine": vehicle.get("engine"),
            "vin": vehicle.get("vin"),
            "tag": "FACT",
            "note": match_note,
        },
        "evidence": {
            "order_count": n,
            "date_start": min(dates) if dates else None,
            "date_end": max(dates) if dates else None,
            "tag": "FACT" if n else "UNKNOWN",
        },
        "common_reasons": common_reasons,
        "parts": parts_out,
        "ticket": {
            "n_with_amount": len(ticket_amounts),
            "typical_usd": round(statistics.median(ticket_amounts), 2) if ticket_amounts else None,
            "best_observed_usd": _percentile(ticket_amounts, 0.25),
            "worst_observed_usd": _percentile(ticket_amounts, 0.75),
            "method": "Observed shop invoices for matched vehicle(s)",
            "tag": "FACT" if len(ticket_amounts) >= 5 else ("INFERRED" if ticket_amounts else "UNKNOWN"),
        },
        "time": {
            "n_with_hours": len(hours_with),
            "n_missing_hours": hours_missing,
            "typical_hours": round(statistics.median(hours_with), 1) if hours_with else None,
            "tag": "FACT" if len(hours_with) >= 5 else ("INFERRED" if hours_with else "UNKNOWN"),
            "note": (
                f"Based on {len(hours_with)} orders with labor_hours recorded."
                if hours_with
                else "No labor hours in warehouse for this match."
            ),
        },
        "gotchas": gotcha_out,
        "likelihood": {
            "selected_reason": selected_reason,
            "percent": likelihood_pct,
            "n": likelihood_n,
            "best_case": (
                f"Observed low ticket ${ _percentile(ticket_amounts, 0.25) }"
                if ticket_amounts
                else "UNKNOWN — no ticket amounts"
            ),
            "worst_case": (
                f"Observed high ticket ${ _percentile(ticket_amounts, 0.75) }"
                if ticket_amounts
                else "UNKNOWN — no ticket amounts"
            ),
            "tag": "INFERRED" if likelihood_n >= MIN_N_FOR_INFERENCE else "UNKNOWN",
            "statement": (
                f"Based on {n} shop orders, {likelihood_pct}% share for '{selected_reason}' "
                f"(not a Porsche diagnosis)."
                if selected_reason and likelihood_pct is not None
                else f"Only {n} order(s) — insufficient for a strong likelihood call."
            ),
        },
        "recommendations": recommendations,
        "not_in_data": not_in_data,
        "orchestrator": {
            "staff": {"status": "unknown", "tag": "UNKNOWN"},
            "parts_vendors": {"status": "unknown", "tag": "UNKNOWN"},
            "procedure": {"status": "unknown", "tag": "UNKNOWN"},
            "tools": {"status": "unknown", "tag": "UNKNOWN"},
        },
        "guardrail": {
            "no_fill": True,
            "human_gate": "Jake must approve before customer hears ETA or scope.",
        },
    }


def _empty_packet(
    query: str,
    grain: str,
    match_note: str,
    not_in_data: list[dict[str, str]],
) -> dict[str, Any]:
    not_in_data.append({"topic": "Vehicle match", "why": match_note})
    return {
        "query": query,
        "generated_at": datetime.now(UTC).isoformat(),
        "persona": "Jake — service advisor",
        "vehicle_match": {
            "grain": grain,
            "identity": None,
            "year": None,
            "make": None,
            "model": None,
            "engine": None,
            "vin": None,
            "tag": "UNKNOWN",
            "note": match_note,
        },
        "evidence": {"order_count": 0, "date_start": None, "date_end": None, "tag": "UNKNOWN"},
        "common_reasons": [],
        "parts": [],
        "ticket": {
            "n_with_amount": 0,
            "typical_usd": None,
            "best_observed_usd": None,
            "worst_observed_usd": None,
            "method": "No orders",
            "tag": "UNKNOWN",
        },
        "time": {
            "n_with_hours": 0,
            "n_missing_hours": 0,
            "typical_hours": None,
            "tag": "UNKNOWN",
            "note": "No matching orders.",
        },
        "gotchas": [],
        "likelihood": {
            "selected_reason": None,
            "percent": None,
            "n": 0,
            "best_case": "UNKNOWN",
            "worst_case": "UNKNOWN",
            "tag": "UNKNOWN",
            "statement": "No shop history for this vehicle identity.",
        },
        "recommendations": [],
        "not_in_data": not_in_data,
        "orchestrator": {
            "staff": {"status": "unknown", "tag": "UNKNOWN"},
            "parts_vendors": {"status": "unknown", "tag": "UNKNOWN"},
            "procedure": {"status": "unknown", "tag": "UNKNOWN"},
            "tools": {"status": "unknown", "tag": "UNKNOWN"},
        },
        "guardrail": {
            "no_fill": True,
            "human_gate": "Jake must approve before customer hears ETA or scope.",
        },
    }


def _vehicle_only_packet(
    query: str,
    grain: str,
    match_note: str,
    vehicle: dict[str, Any],
    not_in_data: list[dict[str, str]],
) -> dict[str, Any]:
    base = _empty_packet(query, grain, match_note, not_in_data)
    base["vehicle_match"] = {
        "grain": grain,
        "identity": _pick(vehicle, "vin") or f"{vehicle['year']} {vehicle['make']} {vehicle['model']}",
        "year": vehicle.get("year"),
        "make": vehicle.get("make"),
        "model": vehicle.get("model"),
        "engine": vehicle.get("engine"),
        "vin": vehicle.get("vin"),
        "tag": "FACT",
        "note": match_note,
    }
    return base
