"""Ticket / targeted ingest — mocked ShopMonkey, no live key."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from shop.ingest import ingest_order_by_ticket, ingest_one_order
from shop.warehouse import connect, initialize

_TMP = tempfile.TemporaryDirectory()
_DB_PATH = os.path.join(_TMP.name, "ticket.sqlite3")

TICKET_ORDER = {
    "id": "sm-order-bmw",
    "number": 1042,
    "createdDate": "2026-08-18T10:00:00.000Z",
    "totalCostCents": 85000,
    "vehicleId": "sm-veh-bmw",
    "vehicle": {
        "id": "sm-veh-bmw",
        "year": 2012,
        "make": "BMW",
        "model": "328i",
        "vin": "WBA3A5C51CF346278",
    },
    "services": [{"id": "svc-1", "name": "Check engine light", "recommended": False, "parts": []}],
}


class TicketIngestTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["SHOP_INTEL_DB_PATH"] = _DB_PATH
        initialize()

    @patch("shop.ingest.list_vehicle_orders", return_value=[])
    @patch("shop.ingest.find_orders_by_number", return_value=[TICKET_ORDER])
    @patch("shop.ingest.get_order", return_value=TICKET_ORDER)
    @patch("shop.ingest.list_order_services", return_value=TICKET_ORDER["services"])
    @patch("shop.ingest.get_vehicle", return_value=TICKET_ORDER["vehicle"])
    def test_ingest_ticket_stores_vin(
        self,
        *_mocks: object,
    ) -> None:
        result = ingest_order_by_ticket("1042", pull_vehicle_history=False)
        self.assertEqual(result["ticket"], "1042")
        self.assertEqual(result["vin"], "WBA3A5C51CF346278")

        with connect() as connection:
            row = connection.execute(
                "SELECT vin, make, model FROM vehicles WHERE id = ?",
                ("sm-veh-bmw",),
            ).fetchone()
            self.assertEqual(row["vin"], "WBA3A5C51CF346278")
            self.assertEqual(row["make"], "BMW")

    @patch("shop.ingest.get_vehicle", return_value=TICKET_ORDER["vehicle"])
    @patch("shop.ingest.list_order_services", return_value=TICKET_ORDER["services"])
    @patch("shop.ingest.get_order", return_value=TICKET_ORDER)
    def test_vin_not_wiped_on_sparse_reingest(self, *_mocks: object) -> None:
        ingest_one_order(TICKET_ORDER)
        sparse = {
            **TICKET_ORDER,
            "vehicle": {
                "id": "sm-veh-bmw",
                "make": "Unknown",
                "model": "Unknown",
                "year": 0,
            },
        }
        ingest_one_order(sparse)
        with connect() as connection:
            vin = connection.execute(
                "SELECT vin FROM vehicles WHERE id = ?", ("sm-veh-bmw",)
            ).fetchone()["vin"]
            self.assertEqual(vin, "WBA3A5C51CF346278")
