"""Week 1 server — /health, POST /ask, POST /estimate."""

from fastapi import FastAPI, HTTPException

from server.estimate_service import run_estimate
from server.openai_client import ask_openai
from server.schemas import AskRequest, AskResponse, EstimateRequest, EstimateResponse

app = FastAPI(title="AI Eng Bootcamp API")


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
