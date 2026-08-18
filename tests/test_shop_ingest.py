"""ShopMonkey ingest mapping — mock payload, no live key."""

from __future__ import annotations

import os
import tempfile
import unittest

from server.shop_ingest import upsert_order
from server.shop_warehouse import connect, initialize

_TMP = tempfile.TemporaryDirectory()
_DB_PATH = os.path.join(_TMP.name, "ingest.sqlite3")

SAMPLE_ORDER = {
    "id": "sm-order-1",
    "createdDate": "2024-06-01T12:00:00.000Z",
    "totalCostCents": 125000,
    "totalLaborHours": 3.5,
    "complaint": "Brake noise",
    "vehicleId": "sm-veh-1",
    "vehicle": {
        "id": "sm-veh-1",
        "year": 2019,
        "make": "Porsche",
        "model": "911",
        "engine": "flat-6",
        "vin": "WP0TESTVIN00001",
    },
    "services": [
        {
            "id": "sm-svc-1",
            "name": "Brake service",
            "recommended": False,
            "parts": [
                {
                    "id": "sm-part-1",
                    "name": "Front brake pad set",
                    "partNumber": "SM-BRK-001",
                    "quantity": 1,
                    "retailCostCents": 18900,
                }
            ],
        },
        {
            "id": "sm-svc-2",
            "name": "Flush brake fluid",
            "recommended": True,
            "parts": [],
        },
    ],
}


class IngestMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SHOP_INTEL_DB_PATH"] = _DB_PATH

    def test_upsert_order_maps_shopmonkey_shape(self) -> None:
        initialize()
        with connect() as connection:
            counts = upsert_order(connection, SAMPLE_ORDER)
            connection.commit()
            self.assertEqual(counts["orders"], 1)
            self.assertEqual(counts["services"], 2)
            self.assertEqual(counts["parts"], 1)
            self.assertGreaterEqual(counts["gotchas"], 1)
            vin = connection.execute(
                "SELECT vin FROM vehicles WHERE id = ?", ("sm-veh-1",)
            ).fetchone()["vin"]
            self.assertEqual(vin, "WP0TESTVIN00001")
            source = connection.execute(
                "SELECT source FROM orders WHERE id = ?", ("sm-order-1",)
            ).fetchone()["source"]
            self.assertEqual(source, "shopmonkey")
