"""AutoZyte API — shop history, Jake briefing (FerdAI), ShopMonkey ingest."""

from fastapi import FastAPI, HTTPException

from ferdai.hypothesis import build_hypothesis
from server.schemas import HypothesisRequest
from shop.ingest import ensure_vehicle_for_vin, ingest_orders, ingest_status
from shop.service import (
    comeback_count,
    gotchas,
    job_artifacts,
    model_mix,
    parts_catalog,
    reason_mix,
    status as shop_status,
    ticket_trend,
)
from shop.shopmonkey_client import (
    ShopmonkeyAPIError,
    ShopmonkeyConfigError,
    api_key_configured,
)
from shop.synthetic import seed_if_empty

app = FastAPI(title="AutoZyte API")
seed_if_empty()


@app.get("/")
def root():
    return {
        "service": "AutoZyte",
        "health": "/health",
        "docs": "/docs",
        "shop": "GET /shop/status",
        "advisor": "POST /advisor/hypothesis",
        "powered_by": "FerdAI",
    }


@app.get("/health")
def health():
    return {"status": "ok", "product": "AutoZyte"}


@app.get("/shop/status")
def get_shop_status():
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
    return parts_catalog()


@app.get("/shop/artifacts")
def get_job_artifacts():
    return job_artifacts()


@app.get("/shop/gotchas")
def get_gotchas():
    return {"comeback_orders": comeback_count(), "events": gotchas()}


@app.post("/advisor/hypothesis")
def advisor_hypothesis(body: HypothesisRequest):
    """Advisor briefing — FerdAI hypothesis engine (no LLM in P2)."""
    if not any([body.vin, body.year, body.make, body.model]):
        raise HTTPException(
            status_code=422,
            detail="Provide VIN or year + make + model.",
        )
    if body.vin and api_key_configured():
        ensure_vehicle_for_vin(body.vin.strip())
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
    try:
        return ingest_orders(max_pages=max_pages)
    except ShopmonkeyConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ShopmonkeyAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
