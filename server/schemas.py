"""JSON shapes for API endpoints — contracts between client and server."""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, example="What is an API?")


class AskResponse(BaseModel):
    answer: str
    confidence: float = Field(..., ge=0.0, le=1.0)


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


class HypothesisRequest(BaseModel):
    vin: str | None = Field(default=None, example="SYNWP020140002")
    year: int | None = Field(default=None, ge=1900, le=2100)
    make: str | None = Field(default=None, example="Porsche")
    model: str | None = Field(default=None, example="911")
    engine: str | None = None
    complaint: str | None = Field(default=None, example="AOS / oil smell")
    mileage: int | None = Field(default=None, ge=0)
