"""Tests for prompt complexity and cost range forecasting."""

from __future__ import annotations

import pytest

from cost_engine import Workload, forecast_cost_ranges
from prompt_analyzer import forecast_workload, score_complexity


SIMPLE_PROMPT = "What is an API? Answer in one sentence."
COMPLEX_PROMPT = (
    "Compare three vendor proposals for SOC2 compliance, debug integration risks, "
    "plan a migration step by step, and produce a detailed report. "
    "Double-check all figures and cite sources. Best effort on edge cases."
)


def test_simple_prompt_low_complexity():
    dims = score_complexity(SIMPLE_PROMPT)
    assert dims.label == "Simple"
    assert dims.composite_score < 12


def test_complex_prompt_high_complexity():
    dims = score_complexity(COMPLEX_PROMPT)
    assert dims.label in ("Complex", "Agentic", "Moderate")
    assert dims.verification_need >= 2
    assert dims.uncertainty_pct >= 0.12


def test_forecast_workload_maps_steps():
    forecast = forecast_workload(COMPLEX_PROMPT, tasks_per_day=10)
    assert forecast.workload.primary_steps >= 2
    assert forecast.workload.checker_steps >= 1
    assert forecast.workload.result_shape.startswith("Report")


def test_cost_ranges_broad_wider_than_close():
    forecast = forecast_workload(SIMPLE_PROMPT, tasks_per_day=50)
    ranges = forecast_cost_ranges(
        forecast.workload,
        uncertainty_pct=forecast.dimensions.uncertainty_pct,
    )
    assert ranges is not None
    broad_span = ranges.broad_max_per_task_usd - ranges.broad_min_per_task_usd
    close_span = ranges.close_high_per_task_usd - ranges.close_low_per_task_usd
    assert broad_span >= close_span
    assert ranges.close_center_per_task_usd == pytest.approx(
        (ranges.close_low_per_task_usd + ranges.close_high_per_task_usd) / 2,
        rel=0.01,
    )


def test_headroom_reduces_input_tokens():
    base = forecast_workload(COMPLEX_PROMPT, apply_headroom=False)
    trimmed = forecast_workload(COMPLEX_PROMPT, apply_headroom=True)
    assert trimmed.workload.input_tokens <= base.workload.input_tokens


def test_forecast_cost_ranges_none_when_too_large():
    workload = Workload(
        input_tokens=2_000_000,
        result_shape="Short answer (≈150 tokens)",
        primary_steps=1,
        checker_steps=0,
        tasks_per_day=1,
    )
    assert forecast_cost_ranges(workload) is None
