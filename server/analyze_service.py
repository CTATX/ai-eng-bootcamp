"""Prompt analysis → workload forecast → cost ranges."""

from __future__ import annotations

from cost_engine import forecast_cost_ranges
from prompt_analyzer import forecast_workload
from server.openai_client import classify_prompt_complexity

from server.estimate_service import run_estimate
from server.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ComplexityDimensionsRow,
    CostRangeRow,
    EstimateRequest,
    WorkloadDerivedRow,
)


def run_analyze(body: AnalyzeRequest) -> AnalyzeResponse:
    llm_payload = None
    if body.use_llm_classifier:
        llm_payload = classify_prompt_complexity(body.prompt_text)

    forecast = forecast_workload(
        body.prompt_text,
        body.tasks_per_day,
        apply_headroom=body.apply_headroom,
        llm_payload=llm_payload,
    )
    dims = forecast.dimensions
    uncertainty = dims.uncertainty_pct
    if dims.ambiguity_risk >= 4:
        uncertainty = min(0.45, uncertainty + 0.08)

    cost_ranges = forecast_cost_ranges(
        forecast.workload,
        uncertainty_pct=uncertainty,
        reasoning_depth=dims.reasoning_depth,
    )
    if cost_ranges is None:
        raise ValueError(
            "No model in the catalog fits this prompt size. "
            "Try a shorter prompt or increase context limits in the catalog."
        )

    estimate_body = EstimateRequest(
        input_tokens=forecast.workload.input_tokens,
        result_shape=forecast.workload.result_shape,
        primary_steps=forecast.workload.primary_steps,
        checker_steps=forecast.workload.checker_steps,
        tasks_per_day=forecast.workload.tasks_per_day,
        workload_note=body.prompt_text.strip()[:500] or None,
        reasoning_depth=dims.reasoning_depth,
    )
    estimate = run_estimate(estimate_body)

    headroom_note = None
    if body.apply_headroom and forecast.headroom_savings_pct:
        headroom_note = (
            f"Headroom-style trim applied (~{forecast.headroom_savings_pct:.0%} input reduction). "
            "Broad range reflects optimized token count."
        )
    elif forecast.headroom_savings_pct:
        headroom_note = (
            f"Optional Headroom savings ~{forecast.headroom_savings_pct:.0%} on input tokens "
            "(toggle apply_headroom to include in forecast)."
        )

    if body.use_llm_classifier and llm_payload is None:
        forecast.rationale.append(
            "LLM classifier requested but unavailable (missing OPENAI_API_KEY) — using heuristics."
        )
        forecast.analyzer_source = "heuristic"

    return AnalyzeResponse(
        complexity=ComplexityDimensionsRow(
            label=dims.label,
            composite_score=dims.composite_score,
            input_size=dims.input_size,
            output_depth=dims.output_depth,
            reasoning_depth=dims.reasoning_depth,
            verification_need=dims.verification_need,
            ambiguity_risk=dims.ambiguity_risk,
            agentic_pattern=dims.agentic_pattern,
            uncertainty_pct=uncertainty,
        ),
        workload_derived=WorkloadDerivedRow(
            input_tokens_raw=forecast.input_tokens_raw,
            input_tokens=forecast.workload.input_tokens,
            result_shape=forecast.workload.result_shape,
            primary_steps=forecast.workload.primary_steps,
            checker_steps=forecast.workload.checker_steps,
            tasks_per_day=forecast.workload.tasks_per_day,
        ),
        cost_ranges=CostRangeRow(
            broad_min_per_task_usd=cost_ranges.broad_min_per_task_usd,
            broad_max_per_task_usd=cost_ranges.broad_max_per_task_usd,
            broad_min_monthly_usd=cost_ranges.broad_min_monthly_usd,
            broad_max_monthly_usd=cost_ranges.broad_max_monthly_usd,
            close_center_per_task_usd=cost_ranges.close_center_per_task_usd,
            close_low_per_task_usd=cost_ranges.close_low_per_task_usd,
            close_high_per_task_usd=cost_ranges.close_high_per_task_usd,
            close_delta_per_task_usd=cost_ranges.close_delta_per_task_usd,
            close_center_monthly_usd=cost_ranges.close_center_monthly_usd,
            close_low_monthly_usd=cost_ranges.close_low_monthly_usd,
            close_high_monthly_usd=cost_ranges.close_high_monthly_usd,
            recommended_model_id=cost_ranges.recommended_model_id,
            recommended_model_name=cost_ranges.recommended_model_name,
        ),
        rationale=forecast.rationale,
        analyzer_source=forecast.analyzer_source,
        headroom_note=headroom_note,
        estimate=estimate,
    )
