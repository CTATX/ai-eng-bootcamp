"""SQLite warehouse for shop intelligence. Synthetic now; ShopMonkey later."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def db_path() -> Path:
    return Path(os.getenv("SHOP_INTEL_DB_PATH", "data/shop_intel.sqlite3"))


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vehicles (
    id TEXT PRIMARY KEY,
    make TEXT NOT NULL,
    model TEXT NOT NULL,
    year INTEGER NOT NULL,
    engine TEXT,
    vin TEXT,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    vehicle_id TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    total_usd REAL,
    labor_hours REAL,
    comeback INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS order_services (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS order_parts (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    qty INTEGER NOT NULL,
    unit_usd REAL,
    source TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE TABLE IF NOT EXISTS parts_catalog (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    vendor TEXT NOT NULL,
    vendor_kind TEXT NOT NULL,
    list_usd REAL NOT NULL,
    lead_days INTEGER NOT NULL,
    in_stock INTEGER NOT NULL,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_artifacts (
    id TEXT PRIMARY KEY,
    job_family TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    title TEXT NOT NULL,
    available INTEGER NOT NULL,
    note TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS gotcha_events (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    label TEXT NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
"""


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize() -> None:
    with connect() as connection:
        connection.executescript(SCHEMA)
