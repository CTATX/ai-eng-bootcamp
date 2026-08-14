"""SQLite persistence for append-only AI usage and reviewed outcomes."""

from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def _database_path() -> Path:
    configured = os.getenv("AI_FINOPS_DB_PATH", "data/finops.sqlite3")
    path = Path(configured)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent.parent / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(_database_path())
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_events (
                request_id TEXT PRIMARY KEY,
                occurred_at TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                provider TEXT NOT NULL,
                model_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                business_owner_id TEXT NOT NULL,
                use_case TEXT NOT NULL,
                environment TEXT NOT NULL,
                input_tokens INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                cached_input_tokens INTEGER NOT NULL DEFAULT 0,
                estimated_cost_usd REAL NOT NULL,
                cost_basis TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                status TEXT NOT NULL,
                outcome_status TEXT NOT NULL DEFAULT 'pending'
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_usage_occurred_at ON usage_events(occurred_at)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_usage_owner ON usage_events(business_owner_id)"
        )


def record_usage(event: dict[str, Any]) -> None:
    initialize_database()
    columns = ", ".join(event)
    placeholders = ", ".join("?" for _ in event)
    with _connect() as connection:
        connection.execute(
            f"INSERT INTO usage_events ({columns}) VALUES ({placeholders})",
            tuple(event.values()),
        )


def update_outcome(request_id: str, outcome_status: str) -> bool:
    if outcome_status not in {"accepted", "rejected"}:
        raise ValueError("outcome_status must be accepted or rejected")
    initialize_database()
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE usage_events SET outcome_status = ? WHERE request_id = ?",
            (outcome_status, request_id),
        )
        return cursor.rowcount > 0


def query_events(days: int = 30) -> list[dict[str, Any]]:
    initialize_database()
    start_day = datetime.now(UTC).date() - timedelta(days=max(days - 1, 0))
    start = datetime.combine(start_day, datetime.min.time(), tzinfo=UTC)
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM usage_events
            WHERE occurred_at >= ?
            ORDER BY occurred_at DESC
            """,
            (start.isoformat(),),
        ).fetchall()
    return [dict(row) for row in rows]


def today_spend() -> float:
    initialize_database()
    today_prefix = datetime.now(UTC).date().isoformat()
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT COALESCE(SUM(estimated_cost_usd), 0) AS spend
            FROM usage_events
            WHERE substr(occurred_at, 1, 10) = ?
            """,
            (today_prefix,),
        ).fetchone()
    return float(row["spend"])
