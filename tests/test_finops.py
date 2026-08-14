"""Focused tests for AI FinOps persistence and KPI calculations."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import UTC, datetime

from server.finops_service import (
    attribution_breakdown,
    daily_spend_series,
    estimate_usage_cost,
    kpi_summary,
)
from server.usage_repository import record_usage, update_outcome


class FinOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["AI_FINOPS_DB_PATH"] = os.path.join(
            self.temp_dir.name,
            "finops.sqlite3",
        )
        os.environ["AI_DAILY_BUDGET_USD"] = "1.00"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()
        os.environ.pop("AI_FINOPS_DB_PATH", None)

    def _record_sample(
        self,
        request_id: str = "req-1",
        status: str = "success",
    ) -> None:
        record_usage(
            {
                "request_id": request_id,
                "occurred_at": datetime.now(UTC).isoformat(),
                "endpoint": "/ask",
                "provider": "OpenAI",
                "model_id": "gpt-4o-mini",
                "user_id": "ct",
                "business_owner_id": "Product",
                "use_case": "bootcamp-qa",
                "environment": "test",
                "input_tokens": 100,
                "output_tokens": 50,
                "cached_input_tokens": 20,
                "estimated_cost_usd": 0.01,
                "cost_basis": "test",
                "latency_ms": 100,
                "status": status,
                "outcome_status": "pending",
            }
        )

    def test_estimated_cost_uses_cached_rate(self) -> None:
        cost = estimate_usage_cost(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            cached_input_tokens=500_000,
        )
        self.assertAlmostEqual(cost, 0.7125)

    def test_kpis_include_spend_cache_and_reviewed_outcome(self) -> None:
        self._record_sample()
        self.assertTrue(update_outcome("req-1", "accepted"))

        summary = kpi_summary(7)

        self.assertEqual(summary["request_count"], 1)
        self.assertAlmostEqual(summary["total_spend_usd"], 0.01)
        self.assertAlmostEqual(summary["provider_cache_ratio"], 0.2)
        self.assertEqual(summary["accepted_outcomes"], 1)
        self.assertAlmostEqual(summary["cost_per_accepted_outcome_usd"], 0.01)
        self.assertEqual(summary["value_status"].split(":")[0], "Not validated")

    def test_daily_series_includes_zero_spend_days(self) -> None:
        self._record_sample()
        rows = daily_spend_series(7)
        self.assertEqual(len(rows), 7)
        self.assertEqual(rows[-1]["request_count"], 1)

    def test_attribution_rolls_up_by_owner(self) -> None:
        self._record_sample()
        rows = attribution_breakdown(30, "business_owner_id")
        self.assertEqual(rows[0]["dimension"], "Product")
        self.assertEqual(rows[0]["spend_share"], 1.0)

    def test_success_rate_includes_failed_attempts(self) -> None:
        self._record_sample("req-success")
        self._record_sample("req-failed", status="failed")
        summary = kpi_summary(7)
        self.assertEqual(summary["request_count"], 2)
        self.assertEqual(summary["successful_task_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
