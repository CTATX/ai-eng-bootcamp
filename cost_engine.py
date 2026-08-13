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
