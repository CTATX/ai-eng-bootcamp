"""AI FinOps KPI calculations and budget controls."""

from __future__ import annotations

import calendar
import os
from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Any

from server.usage_repository import query_events, today_spend


def configured_pricing() -> dict[str, float]:
    """Return configurable per-million-token rates.

    Defaults are planning values for gpt-4o-mini, not provider invoices.
    """
    return {
        "input": float(os.getenv("OPENAI_INPUT_USD_PER_M", "0.15")),
        "cached_input": float(os.getenv("OPENAI_CACHED_INPUT_USD_PER_M", "0.075")),
        "output": float(os.getenv("OPENAI_OUTPUT_USD_PER_M", "0.60")),
    }


def estimate_usage_cost(
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int,
) -> float:
    rates = configured_pricing()
    uncached_input = max(input_tokens - cached_input_tokens, 0)
    return (
        uncached_input * rates["input"]
        + cached_input_tokens * rates["cached_input"]
        + output_tokens * rates["output"]
    ) / 1_000_000


def budget_settings() -> dict[str, Any]:
    return {
        "daily_budget_usd": float(os.getenv("AI_DAILY_BUDGET_USD", "5.00")),
        "alert_threshold_pct": float(os.getenv("AI_ALERT_THRESHOLD_PCT", "0.80")),
        "hard_stop_enabled": os.getenv("AI_HARD_STOP_ENABLED", "false").lower() == "true",
    }


def enforce_daily_budget() -> None:
    settings = budget_settings()
    if (
        settings["hard_stop_enabled"]
        and today_spend() >= settings["daily_budget_usd"]
    ):
        raise RuntimeError(
            "Daily AI budget reached. Hard stop is enabled; increase the cap or wait until tomorrow."
        )


def _budget_status(spend: float, budget: float, alert_threshold: float) -> str:
    utilization = spend / budget if budget else 0
    if utilization >= 1:
        return "critical"
    if utilization >= alert_threshold:
        return "warning"
    if utilization >= 0.5:
        return "informational"
    return "within_budget"


def kpi_summary(days: int = 30) -> dict[str, Any]:
    events = query_events(days)
    total_spend = sum(float(event["estimated_cost_usd"]) for event in events)
    input_tokens = sum(int(event["input_tokens"]) for event in events)
    cached_tokens = sum(int(event["cached_input_tokens"]) for event in events)
    successful = sum(event["status"] == "success" for event in events)
    reviewed = sum(event["outcome_status"] in {"accepted", "rejected"} for event in events)
    accepted = sum(event["outcome_status"] == "accepted" for event in events)
    settings = budget_settings()
    daily_spend = today_spend()

    now = date.today()
    month_events = [
        event
        for event in events
        if event["occurred_at"].startswith(now.strftime("%Y-%m"))
    ]
    month_spend = sum(float(event["estimated_cost_usd"]) for event in month_events)
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    projected_month_end = month_spend / now.day * days_in_month

    return {
        "window_days": days,
        "total_spend_usd": total_spend,
        "average_daily_spend_usd": total_spend / days,
        "request_count": len(events),
        "successful_task_rate": successful / len(events) if events else None,
        "accepted_outcomes": accepted,
        "reviewed_outcomes": reviewed,
        "acceptance_rate": accepted / reviewed if reviewed else None,
        "cost_per_accepted_outcome_usd": total_spend / accepted if accepted else None,
        "provider_cache_ratio": cached_tokens / input_tokens if input_tokens else None,
        "cache_metric_label": "Provider-reported cached input tokens / total input tokens",
        "normalized_cache_ratio": None,
        "normalized_cache_note": "Unavailable: cache-eligible token denominator is not reported.",
        "today_spend_usd": daily_spend,
        "daily_budget_usd": settings["daily_budget_usd"],
        "daily_budget_utilization": (
            daily_spend / settings["daily_budget_usd"]
            if settings["daily_budget_usd"]
            else None
        ),
        "budget_status": _budget_status(
            daily_spend,
            settings["daily_budget_usd"],
            settings["alert_threshold_pct"],
        ),
        "hard_stop_enabled": settings["hard_stop_enabled"],
        "month_to_date_spend_usd": month_spend,
        "projected_month_end_spend_usd": projected_month_end,
        "cost_confidence": "Estimated from provider token usage and configured pricing; not invoice reconciled.",
        "value_status": "Not validated: people cost and realized business value are not yet captured.",
    }


def daily_spend_series(days: int = 30) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"estimated_spend_usd": 0.0, "request_count": 0}
    )
    for event in query_events(days):
        day = event["occurred_at"][:10]
        totals[day]["estimated_spend_usd"] += float(event["estimated_cost_usd"])
        totals[day]["request_count"] += 1

    today = datetime.now(UTC).date()
    rows = []
    for offset in range(days - 1, -1, -1):
        day = today.fromordinal(today.toordinal() - offset).isoformat()
        rows.append({"date": day, **totals[day]})
    return rows


def attribution_breakdown(days: int = 30, dimension: str = "business_owner_id") -> list[dict[str, Any]]:
    allowed = {"business_owner_id", "user_id", "use_case", "model_id"}
    if dimension not in allowed:
        raise ValueError(f"dimension must be one of: {', '.join(sorted(allowed))}")
    totals: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"estimated_spend_usd": 0.0, "request_count": 0, "accepted_outcomes": 0}
    )
    events = query_events(days)
    total_spend = sum(float(event["estimated_cost_usd"]) for event in events)
    for event in events:
        key = str(event[dimension])
        totals[key]["estimated_spend_usd"] += float(event["estimated_cost_usd"])
        totals[key]["request_count"] += 1
        totals[key]["accepted_outcomes"] += event["outcome_status"] == "accepted"

    return [
        {
            "dimension": key,
            **values,
            "spend_share": values["estimated_spend_usd"] / total_spend if total_spend else 0,
            "cost_per_accepted_outcome_usd": (
                values["estimated_spend_usd"] / values["accepted_outcomes"]
                if values["accepted_outcomes"]
                else None
            ),
        }
        for key, values in sorted(
            totals.items(),
            key=lambda item: item[1]["estimated_spend_usd"],
            reverse=True,
        )
    ]
