"""Week 1 server — /health, POST /ask, POST /estimate, ShopMonkey integration."""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from server.estimate_service import run_estimate
from server.finops_service import (
    attribution_breakdown,
    daily_spend_series,
    enforce_daily_budget,
    estimate_usage_cost,
    kpi_summary,
)
from server.openai_client import DEFAULT_MODEL, ask_openai
from server.shopmonkey_client import ShopmonkeyAPIError, ShopmonkeyConfigError
from server.shopmonkey_service import (
    catalog as shopmonkey_catalog,
    connection_status as shopmonkey_status,
    shop_snapshot,
)
from server.schemas import (
    AskRequest,
    AskResponse,
    AttributionRow,
    DailySpendRow,
    EstimateRequest,
    EstimateResponse,
    FinOpsKpiSummary,
    OutcomeReviewRequest,
    OutcomeReviewResponse,
    ShopmonkeyCatalog,
    ShopmonkeyStatus,
    UsageReceipt,
)
from server.usage_repository import initialize_database, record_usage, update_outcome

app = FastAPI(title="AI Eng Bootcamp API")
initialize_database()


def _record_nonbillable_attempt(
    request_id: str,
    body: AskRequest,
    status: str,
) -> None:
    """Record failed or blocked attempts without letting telemetry mask the API error."""
    try:
        record_usage(
            {
                "request_id": request_id,
                "occurred_at": datetime.now(UTC).isoformat(),
                "endpoint": "/ask",
                "provider": "OpenAI",
                "model_id": DEFAULT_MODEL,
                "user_id": body.user_id,
                "business_owner_id": body.business_owner_id,
                "use_case": body.use_case,
                "environment": body.environment,
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_input_tokens": 0,
                "estimated_cost_usd": 0.0,
                "cost_basis": "unavailable_for_nonbillable_attempt",
                "latency_ms": 0,
                "status": status,
                "outcome_status": "pending",
            }
        )
    except Exception:
        pass


@app.get("/")
def root():
    """Landing hint for deployed URL."""
    return {
        "service": "AI Eng Bootcamp API",
        "health": "/health",
        "docs": "/docs",
        "estimate": "POST /estimate",
        "ask": "POST /ask",
        "finops": "GET /finops/kpis",
        "shopmonkey": "GET /shopmonkey/catalog",
    }


@app.get("/health")
def health():
    """Heartbeat check. No OpenAI, no logic — just 'am I running?'"""
    return {"status": "ok"}


@app.post("/estimate", response_model=EstimateResponse)
def estimate(body: EstimateRequest):
    """Estimate model cost for a workload — powers the first Streamlit app."""
    try:
        return run_estimate(body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest):
    """Answer a question using OpenAI."""
    request_id = str(uuid4())
    usage_recorded = False
    try:
        enforce_daily_budget()
        result = ask_openai(body.question)
        estimated_cost = estimate_usage_cost(
            result.input_tokens,
            result.output_tokens,
            result.cached_input_tokens,
        )
        cost_basis = "configured_price_estimate_not_invoice_reconciled"
        record_usage(
            {
                "request_id": request_id,
                "occurred_at": datetime.now(UTC).isoformat(),
                "endpoint": "/ask",
                "provider": "OpenAI",
                "model_id": result.model_id,
                "user_id": body.user_id,
                "business_owner_id": body.business_owner_id,
                "use_case": body.use_case,
                "environment": body.environment,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "cached_input_tokens": result.cached_input_tokens,
                "estimated_cost_usd": estimated_cost,
                "cost_basis": cost_basis,
                "latency_ms": result.latency_ms,
                "status": "success",
                "outcome_status": "pending",
            }
        )
        usage_recorded = True
        return AskResponse(
            answer=result.answer,
            confidence=0.85,
            usage=UsageReceipt(
                request_id=request_id,
                provider="OpenAI",
                model_id=result.model_id,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cached_input_tokens=result.cached_input_tokens,
                estimated_cost_usd=estimated_cost,
                cost_basis=cost_basis,
            ),
        )
    except ValueError as exc:
        if not usage_recorded:
            _record_nonbillable_attempt(request_id, body, "failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        if not usage_recorded:
            _record_nonbillable_attempt(request_id, body, "blocked")
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except Exception as exc:
        if not usage_recorded:
            _record_nonbillable_attempt(request_id, body, "failed")
        error_name = type(exc).__name__
        if error_name == "AuthenticationError":
            raise HTTPException(
                status_code=401,
                detail=(
                    "Invalid OpenAI API key. Use a key from "
                    "https://platform.openai.com/api-keys (starts with sk-proj- or sk-). "
                    "Cursor keys (sk-crsr-) will not work here."
                ),
            ) from exc
        if error_name == "RateLimitError":
            raise HTTPException(
                status_code=402,
                detail=(
                    "OpenAI account has no credits left. Add billing at "
                    "https://platform.openai.com/settings/organization/billing"
                ),
            ) from exc
        raise HTTPException(
            status_code=502,
            detail="Model call failed. Check billing, network, and try again.",
        ) from exc


@app.post(
    "/finops/usage/{request_id}/outcome",
    response_model=OutcomeReviewResponse,
)
def review_outcome(request_id: str, body: OutcomeReviewRequest):
    """Mark an AI output accepted or rejected after human review."""
    if not update_outcome(request_id, body.outcome_status):
        raise HTTPException(status_code=404, detail="Usage event not found.")
    return OutcomeReviewResponse(
        request_id=request_id,
        outcome_status=body.outcome_status,
    )


@app.get("/finops/kpis", response_model=FinOpsKpiSummary)
def finops_kpis(days: int = 30):
    """Headline spend, efficiency, reliability, and outcome KPIs."""
    if days not in {7, 30}:
        raise HTTPException(status_code=422, detail="days must be 7 or 30")
    return kpi_summary(days)


@app.get("/finops/spend/daily", response_model=list[DailySpendRow])
def finops_daily_spend(days: int = 30):
    """Daily spend series including zero-spend calendar days."""
    if days not in {7, 30}:
        raise HTTPException(status_code=422, detail="days must be 7 or 30")
    return daily_spend_series(days)


@app.get("/finops/attribution", response_model=list[AttributionRow])
def finops_attribution(days: int = 30, dimension: str = "business_owner_id"):
    """Spend and accepted outcomes by owner, user, use case, or model."""
    if days not in {7, 30}:
        raise HTTPException(status_code=422, detail="days must be 7 or 30")
    try:
        return attribution_breakdown(days, dimension)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _shopmonkey_http_error(exc: ShopmonkeyConfigError | ShopmonkeyAPIError) -> HTTPException:
    if isinstance(exc, ShopmonkeyConfigError):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=exc.status_code, detail=exc.message)


@app.get("/shopmonkey/catalog", response_model=ShopmonkeyCatalog)
def get_shopmonkey_catalog():
    """Allowed ShopMonkey REST surfaces. Reskin is not allowed."""
    return shopmonkey_catalog()


@app.get("/shopmonkey/status", response_model=ShopmonkeyStatus)
def get_shopmonkey_status():
    """Check whether a ShopMonkey API key is configured and accepted."""
    try:
        return shopmonkey_status()
    except (ShopmonkeyConfigError, ShopmonkeyAPIError) as exc:
        raise _shopmonkey_http_error(exc) from exc


@app.get("/shopmonkey/snapshot")
def get_shopmonkey_snapshot(limit: int = 25):
    """Read-only shop snapshot through the official ShopMonkey API."""
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 100")
    try:
        return shop_snapshot(limit)
    except (ShopmonkeyConfigError, ShopmonkeyAPIError) as exc:
        raise _shopmonkey_http_error(exc) from exc
