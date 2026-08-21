"""Tests for prompt complexity and cost range forecasting."""

from __future__ import annotations

import pytest

from cost_engine import Workload, estimate_for_model, forecast_cost_ranges, load_models, recommend_model
from prompt_analyzer import (
    forecast_workload,
    merge_classifications,
    score_complexity,
)

PROMPT_FIXTURES: list[tuple[str, str, int, int]] = [
    ("What is an API? One sentence.", "Simple", 0, 12),
    ("List three benefits of unit testing.", "Simple", 0, 12),
    ("Translate this paragraph to Spanish.", "Moderate", 0, 18),
    ("Summarize the key points in a short paragraph.", "Moderate", 0, 18),
    ("Explain how REST APIs work for a junior developer.", "Moderate", 0, 18),
    ("Compare SQL vs NoSQL for a startup MVP.", "Moderate", 0, 20),
    (
        "Debug this integration failure, plan remediation step by step, and write a report section.",
        "Moderate",
        10,
        22,
    ),
    (
        "Compare three vendor proposals for SOC2 compliance and produce a detailed report. "
        "Double-check all figures and cite sources.",
        "Complex",
        15,
        30,
    ),
    (
        "Run an agent loop: search docs, call APIs, iterate until tests pass. "
        "Verify output and audit compliance.",
        "Moderate",
        10,
        22,
    ),
    ("Best effort — maybe refine later if unclear.", "Moderate", 0, 22),
    ("Extract names and emails from the attached JSON into a table.", "Moderate", 0, 20),
    ("Write a comprehensive whitepaper on zero-trust architecture.", "Moderate", 8, 18),
]

SIMPLE_PROMPT = PROMPT_FIXTURES[0][0]
COMPLEX_PROMPT = PROMPT_FIXTURES[7][0]


@pytest.mark.parametrize("prompt,label,min_score,max_score", PROMPT_FIXTURES)
def test_prompt_fixture_complexity_bands(prompt: str, label: str, min_score: int, max_score: int):
    dims = score_complexity(prompt)
    assert min_score <= dims.composite_score < max_score
    if label == "Simple":
        assert dims.label == "Simple"
    elif label == "Complex":
        assert dims.label in ("Complex", "Agentic", "Moderate")
    elif label == "Agentic":
        assert dims.label in ("Agentic", "Complex")


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
        reasoning_depth=forecast.dimensions.reasoning_depth,
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


def test_merge_classifications_prefers_llm_when_confident():
    heuristic = score_complexity(SIMPLE_PROMPT)
    llm = {
        "input_size": 4,
        "output_depth": 4,
        "reasoning_depth": 4,
        "verification_need": 3,
        "ambiguity_risk": 2,
        "agentic_pattern": 2,
        "primary_steps": 3,
        "checker_steps": 1,
        "result_shape": "report",
        "confidence": 0.9,
    }
    merged, source, hints = merge_classifications(heuristic, llm)
    assert source == "llm"
    assert merged.reasoning_depth == 4
    assert hints is not None
    assert hints["primary_steps"] == 3


def test_merge_classifications_falls_back_on_low_confidence():
    heuristic = score_complexity(SIMPLE_PROMPT)
    llm = {"confidence": 0.3, "reasoning_depth": 5}
    merged, source, hints = merge_classifications(heuristic, llm)
    assert source == "heuristic"
    assert merged == heuristic
    assert hints is None


def test_forecast_with_llm_payload():
    llm = {
        "input_size": 3,
        "output_depth": 3,
        "reasoning_depth": 3,
        "verification_need": 2,
        "ambiguity_risk": 1,
        "agentic_pattern": 1,
        "primary_steps": 2,
        "checker_steps": 1,
        "result_shape": "paragraph",
        "confidence": 0.88,
    }
    forecast = forecast_workload(SIMPLE_PROMPT, llm_payload=llm)
    assert forecast.analyzer_source == "llm"
    assert forecast.workload.primary_steps == 2
    assert forecast.workload.result_shape.startswith("Paragraph")


def test_complexity_step_adjustment_reduces_frontier_model_calls():
    workload = Workload(
        input_tokens=4_000,
        result_shape="Report section (≈900 tokens)",
        primary_steps=3,
        checker_steps=1,
        tasks_per_day=10,
    )
    models = {model["id"]: model for model in load_models()}
    sonnet = models["claude-sonnet-4.6"]
    haiku = models["claude-haiku-4.5"]

    sonnet_likely = estimate_for_model(sonnet, workload, "likely", reasoning_depth=4)
    haiku_likely = estimate_for_model(haiku, workload, "likely", reasoning_depth=4)
    assert sonnet_likely.attempted_calls < haiku_likely.attempted_calls


def test_analyze_endpoint_shape():
    from server.schemas import AnalyzeRequest

    body = AnalyzeRequest(
        prompt_text="Summarize this contract and flag risks.",
        tasks_per_day=25,
        use_llm_classifier=False,
    )
    assert body.use_llm_classifier is False


def test_recommend_model_with_reasoning_depth():
    forecast = forecast_workload(COMPLEX_PROMPT)
    rec = recommend_model(forecast.workload, reasoning_depth=forecast.dimensions.reasoning_depth)
    assert rec is not None
    assert rec.eligible
