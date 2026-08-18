"""Read models for the synthetic (later ShopMonkey) warehouse. No LLM."""

from __future__ import annotations

from typing import Any

from shop.synthetic import seed_if_empty
from shop.warehouse import connect
from shop.shopmonkey_client import api_key_configured


def _rows(sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    seed_if_empty()
    with connect() as connection:
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


def _one(sql: str, params: tuple = ()) -> dict[str, Any] | None:
    seed_if_empty()
    with connect() as connection:
        row = connection.execute(sql, params).fetchone()
        return dict(row) if row else None


def status() -> dict[str, Any]:
    seed_if_empty()
    with connect() as connection:
        counts = {
            "vehicles": connection.execute("SELECT COUNT(*) AS n FROM vehicles").fetchone()["n"],
            "orders": connection.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"],
            "parts_catalog": connection.execute(
                "SELECT COUNT(*) AS n FROM parts_catalog"
            ).fetchone()["n"],
            "job_artifacts": connection.execute(
                "SELECT COUNT(*) AS n FROM job_artifacts"
            ).fetchone()["n"],
        }
        year_span = connection.execute(
            "SELECT MIN(year) AS min_year, MAX(year) AS max_year FROM vehicles"
        ).fetchone()
        makes = [
            row["make"]
            for row in connection.execute("SELECT DISTINCT make FROM vehicles").fetchall()
        ]
        missing_hours = connection.execute(
            "SELECT COUNT(*) AS n FROM orders WHERE labor_hours IS NULL"
        ).fetchone()["n"]
        source = connection.execute(
            "SELECT value FROM meta WHERE key = 'source'"
        ).fetchone()
        disclaimer = connection.execute(
            "SELECT value FROM meta WHERE key = 'disclaimer'"
        ).fetchone()
    return {
        "source": source["value"] if source else "unknown",
        "shopmonkey_key_configured": api_key_configured(),
        "shopmonkey_key_required": False,
        "disclaimer": disclaimer["value"] if disclaimer else "",
        "makes": makes,
        "vehicle_year_min": year_span["min_year"],
        "vehicle_year_max": year_span["max_year"],
        "counts": counts,
        "orders_missing_labor_hours": missing_hours,
        "missing_labor_share": (
            round(missing_hours / counts["orders"], 3) if counts["orders"] else None
        ),
        "tags": {
            "warehouse": "FACT",
            "labor_hours_gap": "UNKNOWN" if missing_hours else "FACT",
        },
    }


def ticket_trend() -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT strftime('%Y', opened_at) AS year,
               COUNT(*) AS order_count,
               ROUND(AVG(total_usd), 2) AS avg_ticket_usd,
               ROUND(MIN(total_usd), 2) AS min_ticket_usd,
               ROUND(MAX(total_usd), 2) AS max_ticket_usd
        FROM orders
        GROUP BY 1
        ORDER BY 1
        """
    )


def reason_mix() -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT reason,
               COUNT(*) AS order_count,
               ROUND(COUNT(*) * 1.0 / (SELECT COUNT(*) FROM order_services), 3) AS share
        FROM order_services
        GROUP BY reason
        ORDER BY order_count DESC
        """
    )


def model_mix() -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT v.model,
               COUNT(*) AS order_count,
               ROUND(AVG(o.total_usd), 2) AS avg_ticket_usd
        FROM orders o
        JOIN vehicles v ON v.id = o.vehicle_id
        GROUP BY v.model
        ORDER BY order_count DESC
        """
    )


def parts_catalog() -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT sku, name, vendor, vendor_kind, list_usd, lead_days, in_stock, source
        FROM parts_catalog
        ORDER BY vendor, name
        """
    )


def job_artifacts() -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT job_family, artifact_type, title, available, note, source
        FROM job_artifacts
        ORDER BY job_family, artifact_type
        """
    )


def gotchas() -> list[dict[str, Any]]:
    return _rows(
        """
        SELECT kind, label, COUNT(*) AS event_count
        FROM gotcha_events
        GROUP BY kind, label
        ORDER BY event_count DESC
        """
    )


def comeback_count() -> int:
    row = _one("SELECT COUNT(*) AS n FROM orders WHERE comeback = 1")
    return int(row["n"]) if row else 0
