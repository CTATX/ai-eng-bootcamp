"""JSON shapes for API endpoints — contracts between client and server."""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, example="What is an API?")
    user_id: str = Field(default="local-user", min_length=1)
    business_owner_id: str = Field(default="CT", min_length=1)
    use_case: str = Field(default="bootcamp-qa", min_length=1)
    environment: str = Field(default="local", min_length=1)


class UsageReceipt(BaseModel):
    request_id: str
    provider: str
    model_id: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    estimated_cost_usd: float
    cost_basis: str


class AskResponse(BaseModel):
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    usage: UsageReceipt | None = None


class OutcomeReviewRequest(BaseModel):
    outcome_status: str = Field(pattern="^(accepted|rejected)$")


class OutcomeReviewResponse(BaseModel):
    request_id: str
    outcome_status: str


class FinOpsKpiSummary(BaseModel):
    window_days: int
    total_spend_usd: float
    average_daily_spend_usd: float
    request_count: int
    successful_task_rate: float | None
    accepted_outcomes: int
    reviewed_outcomes: int
    acceptance_rate: float | None
    cost_per_accepted_outcome_usd: float | None
    provider_cache_ratio: float | None
    cache_metric_label: str
    normalized_cache_ratio: float | None
    normalized_cache_note: str
    today_spend_usd: float
    daily_budget_usd: float
    daily_budget_utilization: float | None
    budget_status: str
    hard_stop_enabled: bool
    month_to_date_spend_usd: float
    projected_month_end_spend_usd: float
    cost_confidence: str
    value_status: str


class DailySpendRow(BaseModel):
    date: str
    estimated_spend_usd: float
    request_count: int


class AttributionRow(BaseModel):
    dimension: str
    estimated_spend_usd: float
    request_count: int
    accepted_outcomes: int
    spend_share: float
    cost_per_accepted_outcome_usd: float | None


class EstimateRequest(BaseModel):
    input_tokens: int = Field(..., ge=500, le=500_000)
    result_shape: str = Field(..., min_length=1)
    primary_steps: int = Field(..., ge=1, le=5)
    checker_steps: int = Field(..., ge=0, le=3)
    tasks_per_day: int = Field(..., ge=1, le=10_000)
    workload_note: str | None = None


class ModelEstimateRow(BaseModel):
    model_id: str
    provider: str
    name: str
    scenario: str
    cost_per_task_usd: float
    monthly_usd: float
    output_tokens: int
    attempted_calls: float
    eligible: bool
    ineligible_reason: str | None = None


class EstimateResponse(BaseModel):
    result_shapes: list[str]
    recommendation: ModelEstimateRow | None
    likely_comparison: list[ModelEstimateRow]
    scenario_ranges: list[ModelEstimateRow]


class ShopmonkeyResource(BaseModel):
    name: str
    path: str
    use: str


class ShopmonkeyRestriction(BaseModel):
    action: str
    why: str


class ShopmonkeyCatalog(BaseModel):
    mode: str
    reskin_allowed: bool
    base_url: str
    docs_url: str
    terms_url: str
    acceptable_use_url: str
    summary: str
    allowed_resources: list[ShopmonkeyResource]
    not_allowed: list[ShopmonkeyRestriction]
    webhook_events: list[str]


class ShopmonkeyStatus(BaseModel):
    configured: bool
    connected: bool
    message: str
    auth: dict | list | str | int | float | bool | None = None
