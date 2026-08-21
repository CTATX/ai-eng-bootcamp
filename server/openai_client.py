"""OpenAI call for POST /ask and optional prompt complexity classification."""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from server.schemas import AskResponse

load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"
CLASSIFIER_MAX_INPUT_CHARS = 4_000
_classification_cache: dict[str, dict[str, Any]] = {}


def _api_key_available() -> bool:
    api_key = os.getenv("OPENAI_API_KEY")
    return bool(api_key and not api_key.startswith("sk-your-key"))


def _cache_key(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def ask_openai(question: str) -> AskResponse:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-your-key"):
        raise ValueError("OPENAI_API_KEY is missing. Copy .env.example to .env and add your key.")

    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful tutor for an AI engineering bootcamp. Answer clearly and briefly.",
            },
            {"role": "user", "content": question},
        ],
        max_tokens=300,
    )

    answer = completion.choices[0].message.content or "No answer returned."
    return AskResponse(answer=answer.strip(), confidence=0.85)


def classify_prompt_complexity(prompt_text: str) -> dict[str, Any] | None:
    """LLM classifier for prompt complexity. Returns None if no API key."""
    if not _api_key_available():
        return None

    trimmed = prompt_text.strip()[:CLASSIFIER_MAX_INPUT_CHARS]
    key = _cache_key(trimmed)
    if key in _classification_cache:
        return _classification_cache[key]

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    completion = client.chat.completions.create(
        model=DEFAULT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify prompt complexity for cost forecasting. "
                    "Return JSON with integer fields 1-5: input_size, output_depth, "
                    "reasoning_depth, verification_need, ambiguity_risk, agentic_pattern; "
                    "primary_steps (1-5), checker_steps (0-3); "
                    'result_shape one of "short", "paragraph", "report"; '
                    "confidence (0.0-1.0)."
                ),
            },
            {"role": "user", "content": trimmed},
        ],
        max_tokens=300,
        temperature=0,
    )

    raw = completion.choices[0].message.content or "{}"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        payload = json.loads(match.group(0)) if match else {}

    _classification_cache[key] = payload
    return payload
