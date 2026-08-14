"""ShopMonkey catalog and client contract tests. No live ShopMonkey calls."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from server.shopmonkey_catalog import catalog
from server.shopmonkey_client import ShopmonkeyConfigError, request_json
from server.shopmonkey_service import shop_snapshot


class ShopmonkeyCatalogTests(unittest.TestCase):
    def test_catalog_forbids_reskin(self) -> None:
        payload = catalog()
        self.assertFalse(payload["reskin_allowed"])
        self.assertEqual(payload["mode"], "integration")
        self.assertTrue(payload["allowed_resources"])
        self.assertTrue(payload["not_allowed"])
        blocked = " ".join(item["action"].lower() for item in payload["not_allowed"])
        self.assertIn("reskin", blocked)

    def test_catalog_endpoint_does_not_need_a_key(self) -> None:
        os.environ.pop("SHOPMONKEY_API_KEY", None)
        from server.main import get_shopmonkey_catalog

        payload = get_shopmonkey_catalog()
        self.assertFalse(payload["reskin_allowed"])


class ShopmonkeyClientTests(unittest.TestCase):
    def test_missing_key_raises_config_error(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SHOPMONKEY_API_KEY", None)
            with self.assertRaises(ShopmonkeyConfigError):
                request_json("GET", "/order")

    def test_unwraps_success_envelope(self) -> None:
        class FakeResponse:
            status_code = 200
            content = b'{"success": true, "data": [{"id": "ord-1"}]}'

            def json(self):
                return {"success": True, "data": [{"id": "ord-1"}]}

        with patch.dict(os.environ, {"SHOPMONKEY_API_KEY": "test-key"}):
            with patch("server.shopmonkey_client.requests.request", return_value=FakeResponse()):
                payload = request_json("GET", "/order")
        self.assertEqual(payload, [{"id": "ord-1"}])

    def test_snapshot_maps_order_and_customer_rows(self) -> None:
        with patch.dict(os.environ, {"SHOPMONKEY_API_KEY": "test-key"}):
            with (
                patch("server.shopmonkey_client.auth_status", return_value={"ok": True}),
                patch(
                    "server.shopmonkey_client.list_orders",
                    return_value=[
                        {
                            "id": "o1",
                            "number": "1001",
                            "status": "In Progress",
                            "createdDate": "2026-08-14",
                            "customer": {"firstName": "Ada", "lastName": "Lovelace"},
                            "vehicle": {"vin": "VIN123"},
                        }
                    ],
                ),
                patch(
                    "server.shopmonkey_client.search_customers",
                    return_value=[{"id": "c1", "firstName": "Ada", "lastName": "Lovelace"}],
                ),
                patch("server.shopmonkey_client.list_appointments", return_value=[]),
                patch("server.shopmonkey_client.list_users", return_value=[{"id": "u1"}]),
            ):
                snapshot = shop_snapshot(limit=10)

        self.assertTrue(snapshot["connected"])
        self.assertEqual(snapshot["orders"][0]["customer"], "Ada Lovelace")
        self.assertEqual(snapshot["customers"][0]["name"], "Ada Lovelace")
        self.assertEqual(snapshot["user_count"], 1)
