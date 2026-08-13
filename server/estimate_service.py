"""Cost estimate logic exposed via POST /estimate."""

from __future__ import annotations

from cost_engine import RESULT_SHAPE_TOKENS, CostEstimate, Workload, estimate_all, recommend_model

from server.schemas import EstimateRequest, EstimateResponse, ModelEstimateRow


def _to_row(estimate: CostEstimate) -> ModelEstimateRow:
    return ModelEstimateRow(
        model_id=estimate.model_id,
        provider=estimate.provider,
        name=estimate.name,
        scenario=estimate.scenario,
        cost_per_task_usd=estimate.cost_per_task_usd,
        monthly_usd=estimate.monthly_usd,
        output_tokens=estimate.output_tokens,
        attempted_calls=estimate.attempted_calls,
        eligible=estimate.eligible,
        ineligible_reason=estimate.ineligible_reason,
    )


def run_estimate(body: EstimateRequest) -> EstimateResponse:
    if body.result_shape not in RESULT_SHAPE_TOKENS:
        raise ValueError(f"Unknown result_shape. Choose one of: {', '.join(RESULT_SHAPE_TOKENS)}")

    workload = Workload(
        input_tokens=body.input_tokens,
        result_shape=body.result_shape,
        primary_steps=body.primary_steps,
        checker_steps=body.checker_steps,
        tasks_per_day=body.tasks_per_day,
    )

    recommendation = recommend_model(workload)
    estimates = estimate_all(workload)
    likely_rows = sorted(
        [_to_row(row) for row in estimates if row.scenario == "likely" and row.eligible],
        key=lambda row: row.cost_per_task_usd,
    )

    scenario_ranges: list[ModelEstimateRow] = []
    if recommendation:
        scenario_ranges = [
            _to_row(row) for row in estimates if row.model_id == recommendation.model_id
        ]

    return EstimateResponse(
        result_shapes=list(RESULT_SHAPE_TOKENS.keys()),
        recommendation=_to_row(recommendation) if recommendation else None,
        likely_comparison=likely_rows,
        scenario_ranges=scenario_ranges,
    )
