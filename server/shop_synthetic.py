"""Deterministic synthetic Porsche shop history. Not live vendor data."""

from __future__ import annotations

import random
from datetime import date, timedelta

from server.shop_warehouse import connect, initialize

SEED = 1980
SOURCE = "synthetic"
VEHICLE_COUNT = 72
ORDER_COUNT = 420
SHOP_START = date(2016, 1, 15)
SHOP_END = date(2025, 12, 15)

# Plausible production windows only. Not a full registry.
PORSCHE_MODELS: list[tuple[str, int, int, str]] = [
    ("911", 1980, 2025, "flat-6"),
    ("924", 1980, 1988, "2.0 I4"),
    ("944", 1982, 1991, "2.5 I4"),
    ("928", 1980, 1995, "V8"),
    ("968", 1992, 1995, "3.0 I4"),
    ("Boxster", 1997, 2025, "flat-6"),
    ("Cayman", 2006, 2025, "flat-6"),
    ("Cayenne", 2003, 2025, "V6"),
    ("Panamera", 2010, 2025, "V6"),
    ("Macan", 2015, 2025, "I4 turbo"),
    ("Taycan", 2020, 2025, "electric"),
]

VENDORS = [
    ("Pelican Parts", "specialty catalog", 3),
    ("WorldPac", "wholesale distributor", 1),
    ("Porsche Classic", "dealer / classic", 7),
    ("Suncoast", "specialty catalog", 4),
    ("Shop stock", "on-hand bin", 0),
]

# Shop-authored catalog. Fake SKUs and round prices. Not scraped.
CATALOG: list[tuple[str, str, str, float]] = [
    ("SYN-BRK-PAD-F", "Front brake pad set", "Pelican Parts", 189.00),
    ("SYN-BRK-PAD-R", "Rear brake pad set", "WorldPac", 142.00),
    ("SYN-BRK-ROT-F", "Front rotor pair", "WorldPac", 310.00),
    ("SYN-BRK-ROT-R", "Rear rotor pair", "Pelican Parts", 275.00),
    ("SYN-OIL-FLT", "Oil filter", "Shop stock", 18.00),
    ("SYN-OIL-5W40", "5W-40 oil (case)", "Shop stock", 72.00),
    ("SYN-AOS-996", "Air-oil separator", "Pelican Parts", 245.00),
    ("SYN-IMS-KIT", "IMS bearing kit (prototype SKU)", "Pelican Parts", 890.00),
    ("SYN-CLT-KIT", "Clutch kit", "Suncoast", 1120.00),
    ("SYN-WP-996", "Water pump", "WorldPac", 265.00),
    ("SYN-COOL-PIPE", "Coolant pipe set", "Pelican Parts", 410.00),
    ("SYN-COIL-PACK", "Ignition coil", "WorldPac", 68.00),
    ("SYN-SPARK", "Spark plug set", "Shop stock", 96.00),
    ("SYN-BUSH-CTRL", "Control-arm bushing set", "Suncoast", 340.00),
    ("SYN-WIN-REG", "Window regulator", "WorldPac", 195.00),
    ("SYN-FUEL-PMP", "Fuel pump", "Pelican Parts", 420.00),
    ("SYN-BELT-DRV", "Drive belt", "Shop stock", 54.00),
    ("SYN-AC-DRY", "A/C dryer", "WorldPac", 88.00),
    ("SYN-TIRE-PS", "Performance tire (each)", "Shop stock", 265.00),
    ("SYN-ALIGN-KIT", "Alignment kit / shims", "Shop stock", 35.00),
    ("SYN-AXLE-CV", "Axle / CV assembly", "Suncoast", 480.00),
    ("SYN-RAD-FAN", "Radiator fan", "WorldPac", 310.00),
    ("SYN-MAF", "MAF sensor", "Pelican Parts", 215.00),
    ("SYN-BAT-AGM", "AGM battery", "Shop stock", 249.00),
    ("SYN-CAB-FLT", "Cabin filter", "Shop stock", 28.00),
    ("SYN-BRK-FLUID", "DOT 4 brake fluid", "Shop stock", 16.00),
    ("SYN-COOL-HOSE", "Coolant hose", "Pelican Parts", 78.00),
    ("SYN-SERP", "Serpentine belt", "WorldPac", 42.00),
    ("SYN-TSTAT", "Thermostat", "WorldPac", 64.00),
    ("SYN-O2", "O2 sensor", "Pelican Parts", 155.00),
    ("SYN-PAN-GSKT", "Oil pan gasket", "Porsche Classic", 95.00),
    ("SYN-VALVE-CVR", "Valve cover gasket set", "Porsche Classic", 180.00),
    ("SYN-SHIFT-CBL", "Shift cable", "Suncoast", 220.00),
    ("SYN-TIE-ROD", "Tie rod end", "WorldPac", 86.00),
    ("SYN-SWAY-LNK", "Sway bar link", "WorldPac", 44.00),
    ("SYN-WPR-BLD", "Wiper blade set", "Shop stock", 32.00),
    ("SYN-EVAP-CAN", "EVAP canister", "Pelican Parts", 260.00),
    ("SYN-STARTER", "Starter", "WorldPac", 390.00),
    ("SYN-ALT", "Alternator", "Suncoast", 510.00),
    ("SYN-PLUG-WIRE", "Plug wire set (air-cooled)", "Porsche Classic", 210.00),
]

JOBS: list[dict] = [
    {
        "reason": "Brake service",
        "family": "brakes",
        "hours": 2.2,
        "parts": ["SYN-BRK-PAD-F", "SYN-BRK-PAD-R", "SYN-BRK-FLUID"],
        "weight": 18,
    },
    {
        "reason": "Oil service",
        "family": "maintenance",
        "hours": 0.8,
        "parts": ["SYN-OIL-FLT", "SYN-OIL-5W40"],
        "weight": 16,
    },
    {
        "reason": "AOS / oil separator",
        "family": "engine",
        "hours": 3.5,
        "parts": ["SYN-AOS-996"],
        "weight": 6,
    },
    {
        "reason": "IMS bearing",
        "family": "engine",
        "hours": 14.0,
        "parts": ["SYN-IMS-KIT", "SYN-CLT-KIT"],
        "weight": 3,
    },
    {
        "reason": "Clutch",
        "family": "driveline",
        "hours": 8.5,
        "parts": ["SYN-CLT-KIT"],
        "weight": 5,
    },
    {
        "reason": "Coolant pipes / water pump",
        "family": "cooling",
        "hours": 6.0,
        "parts": ["SYN-WP-996", "SYN-COOL-PIPE", "SYN-COOL-HOSE"],
        "weight": 7,
    },
    {
        "reason": "Ignition (coils / plugs)",
        "family": "engine",
        "hours": 1.5,
        "parts": ["SYN-COIL-PACK", "SYN-SPARK"],
        "weight": 8,
    },
    {
        "reason": "Suspension bushings",
        "family": "chassis",
        "hours": 4.0,
        "parts": ["SYN-BUSH-CTRL", "SYN-SWAY-LNK"],
        "weight": 6,
    },
    {
        "reason": "Window regulator",
        "family": "body",
        "hours": 1.8,
        "parts": ["SYN-WIN-REG"],
        "weight": 4,
    },
    {
        "reason": "Fuel pump",
        "family": "fuel",
        "hours": 3.2,
        "parts": ["SYN-FUEL-PMP"],
        "weight": 3,
    },
    {
        "reason": "Drive belt",
        "family": "engine",
        "hours": 0.6,
        "parts": ["SYN-BELT-DRV", "SYN-SERP"],
        "weight": 5,
    },
    {
        "reason": "A/C service",
        "family": "hvac",
        "hours": 1.4,
        "parts": ["SYN-AC-DRY"],
        "weight": 4,
    },
    {
        "reason": "Tires and alignment",
        "family": "chassis",
        "hours": 1.6,
        "parts": ["SYN-TIRE-PS", "SYN-ALIGN-KIT"],
        "weight": 9,
    },
    {
        "reason": "Battery / no-start",
        "family": "electrical",
        "hours": 0.7,
        "parts": ["SYN-BAT-AGM"],
        "weight": 4,
    },
    {
        "reason": "Cooling fan / overheat",
        "family": "cooling",
        "hours": 2.4,
        "parts": ["SYN-RAD-FAN", "SYN-TSTAT"],
        "weight": 3,
    },
]

ARTIFACT_TYPES = [
    ("design", "Design / exploded view"),
    ("schematic", "Schematic"),
    ("take_apart_steps", "Take-apart steps"),
    ("build_steps", "Build steps"),
    ("images", "Job images"),
    ("videos", "Job video"),
    ("checklist", "Advisor / tech checklist"),
]

CATALOG_MAP = {row[0]: row for row in CATALOG}
VENDOR_LEAD = {name: lead for name, _kind, lead in VENDORS}
VENDOR_KIND = {name: kind for name, kind, _lead in VENDORS}


def _pick_model(rng: random.Random) -> tuple[str, int, str]:
    model, start, end, engine = rng.choice(PORSCHE_MODELS)
    year = rng.randint(start, end)
    return model, year, engine


def _random_day(rng: random.Random) -> date:
    span = (SHOP_END - SHOP_START).days
    return SHOP_START + timedelta(days=rng.randint(0, span))


def seed_if_empty() -> dict[str, int]:
    initialize()
    with connect() as connection:
        row = connection.execute("SELECT COUNT(*) AS n FROM vehicles").fetchone()
        if row["n"] > 0:
            return counts(connection)
        _seed(connection)
        return counts(connection)


def counts(connection) -> dict[str, int]:
    tables = [
        "vehicles",
        "orders",
        "order_services",
        "order_parts",
        "parts_catalog",
        "job_artifacts",
        "gotcha_events",
    ]
    return {
        table: int(connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"])
        for table in tables
    }


def _seed(connection) -> None:
    rng = random.Random(SEED)
    catalog_rows = []
    for sku, name, vendor, list_usd in CATALOG:
        catalog_rows.append(
            (
                sku,
                name,
                vendor,
                VENDOR_KIND[vendor],
                list_usd,
                VENDOR_LEAD[vendor],
                1 if vendor == "Shop stock" or rng.random() > 0.18 else 0,
                SOURCE,
            )
        )
    connection.executemany(
        """
        INSERT INTO parts_catalog
        (sku, name, vendor, vendor_kind, list_usd, lead_days, in_stock, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        catalog_rows,
    )

    families = sorted({job["family"] for job in JOBS})
    artifact_rows = []
    for family in families:
        for artifact_type, title in ARTIFACT_TYPES:
            available = artifact_type == "checklist"
            note = (
                "Shop-authored prototype checklist stub. Not an OEM procedure."
                if available
                else "Slot only. No licensed schematic, media, or OEM steps in this prototype."
            )
            artifact_rows.append(
                (
                    f"art-{family}-{artifact_type}",
                    family,
                    artifact_type,
                    f"{family}: {title}",
                    1 if available else 0,
                    note,
                    SOURCE,
                )
            )
    connection.executemany(
        """
        INSERT INTO job_artifacts
        (id, job_family, artifact_type, title, available, note, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        artifact_rows,
    )

    vehicles = []
    for index in range(VEHICLE_COUNT):
        model, year, engine = _pick_model(rng)
        vin = f"SYNWP0{year:04d}{index:04d}"
        vehicles.append(
            (
                f"veh-{index:03d}",
                "Porsche",
                model,
                year,
                engine,
                vin,
                SOURCE,
            )
        )
    connection.executemany(
        """
        INSERT INTO vehicles (id, make, model, year, engine, vin, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        vehicles,
    )

    weights = [job["weight"] for job in JOBS]
    orders = []
    services = []
    parts = []
    gotchas = []
    last_visit: dict[str, date] = {}

    for index in range(ORDER_COUNT):
        vehicle = rng.choice(vehicles)
        vehicle_id = vehicle[0]
        opened = _random_day(rng)
        job = rng.choices(JOBS, weights=weights, k=1)[0]
        if job["reason"] == "IMS bearing" and vehicle[2] not in {"911", "Boxster", "Cayman"}:
            job = JOBS[1]
        labor_hours = None if rng.random() < 0.22 else round(job["hours"] * rng.uniform(0.85, 1.2), 1)
        parts_total = 0.0
        for part_index, sku in enumerate(job["parts"]):
            _sku, pname, _vendor, list_usd = CATALOG_MAP[sku]
            qty = 4 if sku == "SYN-TIRE-PS" else 1
            unit = round(list_usd * rng.uniform(0.95, 1.08), 2)
            parts_total += unit * qty
            parts.append(
                (
                    f"op-{index:04d}-{part_index}",
                    f"ord-{index:04d}",
                    sku,
                    pname,
                    qty,
                    unit,
                    SOURCE,
                )
            )
        labor_rate = 185.0
        labor_usd = (labor_hours or 0) * labor_rate
        total = round(parts_total + labor_usd, 2) if labor_hours is not None else round(parts_total, 2)
        comeback = 0
        previous = last_visit.get(vehicle_id)
        if previous and 0 < (opened - previous).days <= 30:
            comeback = 1
            gotchas.append(
                (
                    f"gch-{index:04d}-cb",
                    f"ord-{index:04d}",
                    "comeback_within_window",
                    f"Return visit within 30 days of {previous.isoformat()}",
                    SOURCE,
                )
            )
        last_visit[vehicle_id] = opened
        if rng.random() < 0.12:
            gotchas.append(
                (
                    f"gch-{index:04d}-ins",
                    f"ord-{index:04d}",
                    "inspection_recommended_not_sold",
                    "Inspection flagged extra work not sold on this visit",
                    SOURCE,
                )
            )
        orders.append(
            (
                f"ord-{index:04d}",
                vehicle_id,
                opened.isoformat(),
                total,
                labor_hours,
                comeback,
                SOURCE,
            )
        )
        services.append(
            (
                f"svc-{index:04d}",
                f"ord-{index:04d}",
                job["reason"],
                SOURCE,
            )
        )

    connection.executemany(
        """
        INSERT INTO orders
        (id, vehicle_id, opened_at, total_usd, labor_hours, comeback, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        orders,
    )
    connection.executemany(
        """
        INSERT INTO order_services (id, order_id, reason, source)
        VALUES (?, ?, ?, ?)
        """,
        services,
    )
    connection.executemany(
        """
        INSERT INTO order_parts (id, order_id, sku, name, qty, unit_usd, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        parts,
    )
    connection.executemany(
        """
        INSERT INTO gotcha_events (id, order_id, kind, label, source)
        VALUES (?, ?, ?, ?, ?)
        """,
        gotchas,
    )
    connection.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        ("source", SOURCE),
    )
    connection.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
        ("disclaimer", "Synthetic Porsche prototype. Not ShopMonkey. Not live vendor inventory."),
    )
    connection.commit()
