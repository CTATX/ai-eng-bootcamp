"""Jake hypothesis engine — synthetic warehouse, no LLM."""

from __future__ import annotations

import os
import tempfile
import unittest

from ferdai.hypothesis import build_hypothesis
from shop.synthetic import seed_if_empty
from shop.warehouse import connect

_TMP = tempfile.TemporaryDirectory()
_DB_PATH = os.path.join(_TMP.name, "hypothesis.sqlite3")


class HypothesisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["SHOP_INTEL_DB_PATH"] = _DB_PATH
        seed_if_empty()

    def test_vin_match_returns_jake_packet(self) -> None:
        with connect() as connection:
            vin = connection.execute("SELECT vin FROM vehicles LIMIT 1").fetchone()["vin"]
        packet = build_hypothesis(vin=vin, complaint="oil")
        self.assertEqual(packet["persona"], "Jake — service advisor")
        self.assertEqual(packet["vehicle_match"]["tag"], "FACT")
        self.assertGreater(packet["evidence"]["order_count"], 0)
        self.assertTrue(packet["guardrail"]["no_fill"])

    def test_unknown_vin_is_honest(self) -> None:
        packet = build_hypothesis(vin="NOT-A-REAL-VIN")
        self.assertEqual(packet["vehicle_match"]["tag"], "UNKNOWN")
        self.assertEqual(packet["evidence"]["order_count"], 0)
        self.assertEqual(packet["likelihood"]["tag"], "UNKNOWN")

    def test_complaint_boosts_matching_reason(self) -> None:
        packet = build_hypothesis(vin="SYNWP020240053", complaint="AOS oil separator")
        self.assertEqual(packet["likelihood"]["selected_reason"], "AOS / oil separator")
        self.assertTrue(packet["guardrail"]["complaint_matched"])

    def test_aos_complaint_without_history_is_unknown_not_ac(self) -> None:
        packet = build_hypothesis(vin="SYNWP020140002", complaint="AOS oil separator")
        self.assertEqual(packet["likelihood"]["tag"], "UNKNOWN")
        self.assertIsNone(packet["likelihood"]["selected_reason"])
        self.assertFalse(packet["guardrail"]["complaint_matched"])
        self.assertTrue(packet["guardrail"]["no_invented_match"])
        self.assertGreater(len(packet["clarify"]), 0)
        self.assertEqual(packet["parts"], [])

    def test_no_complaint_does_not_invent_likelihood(self) -> None:
        packet = build_hypothesis(vin="SYNWP020140002")
        self.assertIsNone(packet["likelihood"]["selected_reason"])
        self.assertEqual(packet["likelihood"]["tag"], "UNKNOWN")

    def test_orchestrator_slots_are_unknown(self) -> None:
        packet = build_hypothesis(vin="SYNWP020140002")
        for slot in packet["orchestrator"].values():
            self.assertEqual(slot["tag"], "UNKNOWN")
