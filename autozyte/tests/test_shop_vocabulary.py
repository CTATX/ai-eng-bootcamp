"""Shop vocabulary — AOS vs A/C and related term guards."""

from __future__ import annotations

import unittest

from ferdai.shop_vocabulary import (
    best_complaint_reason_match,
    detect_complaint_concepts,
    score_reason_for_concepts,
)


class ShopVocabularyTests(unittest.TestCase):
    def test_aos_and_ac_are_different_concepts(self) -> None:
        aos = detect_complaint_concepts("AOS oil separator noise")
        ac = detect_complaint_concepts("A/C not cold")
        self.assertTrue(any(c.id == "aos" for c in aos))
        self.assertTrue(any(c.id == "ac" for c in ac))

    def test_aos_does_not_match_ac_service_label(self) -> None:
        concepts = detect_complaint_concepts("AOS")
        score, _ = score_reason_for_concepts("A/C service", concepts)
        self.assertLess(score, 0)

    def test_aos_matches_oil_separator_reason(self) -> None:
        concepts = detect_complaint_concepts("air oil separator")
        score, notes = score_reason_for_concepts("AOS / oil separator", concepts)
        self.assertGreater(score, 0)
        self.assertTrue(notes)

    def test_best_match_prefers_aos_over_ac(self) -> None:
        concepts = detect_complaint_concepts("AOS")
        label, score, _ = best_complaint_reason_match(
            ["A/C service", "AOS / oil separator", "Brake service"],
            concepts,
        )
        self.assertEqual(label, "AOS / oil separator")
        self.assertGreater(score, 0)

    def test_no_false_pick_when_aos_missing_from_history(self) -> None:
        concepts = detect_complaint_concepts("AOS oil separator")
        label, score, _ = best_complaint_reason_match(
            ["A/C service", "Brake service", "Clutch"],
            concepts,
        )
        self.assertIsNone(label)
        self.assertLessEqual(score, 0)
