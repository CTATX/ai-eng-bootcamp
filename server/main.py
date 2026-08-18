"""Week 1 server — /health, POST /ask, POST /estimate, shop intelligence."""

from fastapi import FastAPI, HTTPException

from server.estimate_service import run_estimate
from server.openai_client import ask_openai
from server.schemas import (
    AskRequest,
    AskResponse,
    EstimateRequest,
    EstimateResponse,
    HypothesisRequest,
)
from server.shop_hypothesis import build_hypothesis
from server.shop_ingest import ingest_orders, ingest_status
from server.shopmonkey_client import ShopmonkeyAPIError, ShopmonkeyConfigError
from server.shop_service import (
    comeback_count,
    gotchas,
    job_artifacts,
    model_mix,
    parts_catalog,
    reason_mix,
    status as shop_status,
    ticket_trend,
)
from server.shop_synthetic import seed_if_empty

app = FastAPI(title="AI Eng Bootcamp API")
seed_if_empty()


@app.get("/")
def root():
    """Landing hint for deployed URL."""
    return {
        "service": "AI Eng Bootcamp API",
        "health": "/health",
        "docs": "/docs",
        "estimate": "POST /estimate",
        "ask": "POST /ask",
        "shop": "GET /shop/status",
        "jake": "POST /advisor/hypothesis",
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
    try:
        return ask_openai(body.question)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
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


@app.get("/shop/status")
def get_shop_status():
    """Warehouse status. Prototype is synthetic Porsche; no ShopMonkey key."""
    return shop_status()


@app.get("/shop/trends/tickets")
def get_ticket_trend():
    return ticket_trend()


@app.get("/shop/trends/reasons")
def get_reason_mix():
    return reason_mix()


@app.get("/shop/trends/models")
def get_model_mix():
    return model_mix()


@app.get("/shop/parts")
def get_parts_catalog():
    """Synthetic product list. Named vendors, fake SKUs. Not scraped inventory."""
    return parts_catalog()


@app.get("/shop/artifacts")
def get_job_artifacts():
    """Per-job media/procedure slots. Empty unless a shop-authored stub exists."""
    return job_artifacts()


@app.get("/shop/gotchas")
def get_gotchas():
    return {"comeback_orders": comeback_count(), "events": gotchas()}


@app.post("/advisor/hypothesis")
def advisor_hypothesis(body: HypothesisRequest):
    """Jake — data-based hypothesis from warehouse. No LLM."""
    if not any([body.vin, body.year, body.make, body.model]):
        raise HTTPException(
            status_code=422,
            detail="Provide VIN or year + make + model.",
        )
    return build_hypothesis(
        vin=body.vin,
        year=body.year,
        make=body.make,
        model=body.model,
        engine=body.engine,
        complaint=body.complaint,
        mileage=body.mileage,
    )


@app.get("/shop/ingest/status")
def get_ingest_status():
    return ingest_status()


@app.post("/shop/ingest")
def run_ingest(max_pages: int | None = None):
    """Pull ShopMonkey orders when SHOPMONKEY_API_KEY is set."""
    try:
        return ingest_orders(max_pages=max_pages)
    except ShopmonkeyConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ShopmonkeyAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
