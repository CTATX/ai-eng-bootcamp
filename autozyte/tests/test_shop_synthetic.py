"""Synthetic Porsche warehouse bounds. No ShopMonkey, no vendor scrape."""

from __future__ import annotations

import os
import tempfile
import unittest

from shop.service import job_artifacts, parts_catalog, status, ticket_trend
from shop.synthetic import ORDER_COUNT, VEHICLE_COUNT, seed_if_empty
from shop.warehouse import connect

_TMP = tempfile.TemporaryDirectory()
_DB_PATH = os.path.join(_TMP.name, "synthetic.sqlite3")


class SyntheticPorscheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["SHOP_INTEL_DB_PATH"] = _DB_PATH
        seed_if_empty()

    def test_status_is_synthetic_without_a_key(self) -> None:
        payload = status()
        self.assertEqual(payload["source"], "synthetic")
        self.assertFalse(payload["shopmonkey_key_required"])
        self.assertEqual(payload["counts"]["vehicles"], VEHICLE_COUNT)
        self.assertEqual(payload["counts"]["orders"], ORDER_COUNT)

    def test_vehicles_are_porsche_1980_to_2025(self) -> None:
        with connect() as connection:
            rows = connection.execute(
                "SELECT make, year FROM vehicles"
            ).fetchall()
        self.assertEqual(len(rows), VEHICLE_COUNT)
        for row in rows:
            self.assertEqual(row["make"], "Porsche")
            self.assertGreaterEqual(row["year"], 1980)
            self.assertLessEqual(row["year"], 2025)

    def test_catalog_names_vendors_but_marks_synthetic(self) -> None:
        catalog = parts_catalog()
        vendors = {row["vendor"] for row in catalog}
        self.assertIn("Pelican Parts", vendors)
        self.assertIn("WorldPac", vendors)
        self.assertTrue(all(row["source"] == "synthetic" for row in catalog))
        self.assertTrue(all(row["sku"].startswith("SYN-") for row in catalog))

    def test_job_media_slots_are_mostly_unknown(self) -> None:
        artifacts = job_artifacts()
        present = [row for row in artifacts if row["available"]]
        missing = [row for row in artifacts if not row["available"]]
        self.assertTrue(missing)
        self.assertTrue(all(row["artifact_type"] == "checklist" for row in present))

    def test_ticket_trend_has_more_than_one_year(self) -> None:
        years = [row["year"] for row in ticket_trend()]
        self.assertGreaterEqual(len(years), 5)
