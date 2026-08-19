"""System status payload — CLI / API parity."""

from __future__ import annotations

import os
import tempfile
import unittest

from shop.system_status import build_system_status, product_version

_TMP = tempfile.TemporaryDirectory()
_DB_PATH = os.path.join(_TMP.name, "system.sqlite3")


class SystemStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["SHOP_INTEL_DB_PATH"] = _DB_PATH

    def test_build_system_status_shape(self) -> None:
        payload = build_system_status(probe_shopmonkey=False)
        self.assertEqual(payload["product"], "AutoZyte")
        self.assertIn("version", payload)
        self.assertIn("warehouse", payload)
        self.assertIn("ingest", payload)
        self.assertIn("shopmonkey_key_configured", payload)
        self.assertIn("counts", payload["warehouse"])

    def test_product_version_reads_file(self) -> None:
        version = product_version()
        self.assertTrue(version)
