"""Deterministic cost estimation — simplified slice of ai-build-crew logic."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Scenario = Literal["low", "likely", "high"]
RESULT_SHAPE_TOKENS = {
    "Short answer (≈150 tokens)": 150,
    "Paragraph (≈400 tokens)": 400,
    "Report section (≈900 tokens)": 900,
}


@dataclass(frozen=True)
class Workload:
    input_tokens: int
    result_shape: str
    primary_steps: int
    checker_steps: int
    tasks_per_day: int


@dataclass(frozen=True)
class CostEstimate:
    model_id: str
    provider: str
    name: str
    scenario: Scenario
    cost_per_task_usd: float
    monthly_usd: float
    output_tokens: int
    attempted_calls: float
    eligible: bool
    ineligible_reason: str | None = None


def load_models(catalog_path: Path | None = None) -> list[dict]:
    path = catalog_path or Path(__file__).with_name("models.json")
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["models"]


def _per_million_tokens(tokens: int, price_per_million: float) -> float:
    return (tokens / 1_000_000) * price_per_million


def estimate_for_model(model: dict, workload: Workload, scenario: Scenario) -> CostEstimate:
    base_output = RESULT_SHAPE_TOKENS[workload.result_shape]
    output_tokens = int(base_output * model["output_multiplier"][scenario])
    retry_mult = model["retry_multiplier"][scenario]
    attempted_calls = (workload.primary_steps + workload.checker_steps) * retry_mult

    eligible = workload.input_tokens <= model["context_tokens"]
    ineligible_reason = None
    if not eligible:
        ineligible_reason = (
            f"Input needs {workload.input_tokens:,} tokens; "
            f"model context is {model['context_tokens']:,}."
        )

    primary_calls = workload.primary_steps * retry_mult
    checker_calls = workload.checker_steps * retry_mult

    input_cost = _per_million_tokens(workload.input_tokens, model["input"]) * attempted_calls
    output_cost = _per_million_tokens(output_tokens, model["output"]) * attempted_calls
    cost_per_task = input_cost + output_cost if eligible else float("inf")
    monthly = cost_per_task * workload.tasks_per_day * 30 if eligible else float("inf")

    return CostEstimate(
        model_id=model["id"],
        provider=model["provider"],
        name=model["name"],
        scenario=scenario,
        cost_per_task_usd=cost_per_task,
        monthly_usd=monthly,
        output_tokens=output_tokens,
        attempted_calls=attempted_calls,
        eligible=eligible,
        ineligible_reason=ineligible_reason,
    )


def estimate_all(workload: Workload, catalog_path: Path | None = None) -> list[CostEstimate]:
    models = load_models(catalog_path)
    return [
        estimate_for_model(model, workload, scenario)
        for model in models
        for scenario in ("low", "likely", "high")
    ]


def recommend_model(workload: Workload, catalog_path: Path | None = None) -> CostEstimate | None:
    likely = [
        estimate
        for estimate in estimate_all(workload, catalog_path)
        if estimate.scenario == "likely" and estimate.eligible
    ]
    if not likely:
        return None
    return min(likely, key=lambda item: item.cost_per_task_usd)


@dataclass(frozen=True)
class CostRangeForecast:
    """Broad envelope (all models × scenarios) and closer band (recommended model)."""

    broad_min_per_task_usd: float
    broad_max_per_task_usd: float
    broad_min_monthly_usd: float
    broad_max_monthly_usd: float
    close_center_per_task_usd: float
    close_low_per_task_usd: float
    close_high_per_task_usd: float
    close_delta_per_task_usd: float
    close_center_monthly_usd: float
    close_low_monthly_usd: float
    close_high_monthly_usd: float
    uncertainty_pct: float
    recommended_model_id: str | None
    recommended_model_name: str | None


def forecast_cost_ranges(
    workload: Workload,
    *,
    uncertainty_pct: float = 0.15,
    catalog_path: Path | None = None,
) -> CostRangeForecast | None:
    """Return broad x–y range and a tighter delta around the likely recommendation."""
    estimates = estimate_all(workload, catalog_path)
    eligible = [row for row in estimates if row.eligible]
    if not eligible:
        return None

    low_rows = [row for row in eligible if row.scenario == "low"]
    high_rows = [row for row in eligible if row.scenario == "high"]
    broad_min = min(row.cost_per_task_usd for row in low_rows)
    broad_max = max(row.cost_per_task_usd for row in high_rows)

    recommendation = recommend_model(workload, catalog_path)
    if recommendation is None:
        return None

    rec_rows = {
        row.scenario: row
        for row in eligible
        if row.model_id == recommendation.model_id
    }
    likely_row = rec_rows["likely"]
    low_row = rec_rows["low"]
    high_row = rec_rows["high"]

    center = likely_row.cost_per_task_usd
    close_low = center * (1 - uncertainty_pct)
    close_high = center * (1 + uncertainty_pct)
    delta = center * uncertainty_pct

    return CostRangeForecast(
        broad_min_per_task_usd=broad_min,
        broad_max_per_task_usd=broad_max,
        broad_min_monthly_usd=broad_min * workload.tasks_per_day * 30,
        broad_max_monthly_usd=broad_max * workload.tasks_per_day * 30,
        close_center_per_task_usd=center,
        close_low_per_task_usd=close_low,
        close_high_per_task_usd=close_high,
        close_delta_per_task_usd=delta,
        close_center_monthly_usd=likely_row.monthly_usd,
        close_low_monthly_usd=close_low * workload.tasks_per_day * 30,
        close_high_monthly_usd=close_high * workload.tasks_per_day * 30,
        uncertainty_pct=uncertainty_pct,
        recommended_model_id=recommendation.model_id,
        recommended_model_name=recommendation.name,
    )
