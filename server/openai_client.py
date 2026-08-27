"""OpenAI call for POST /ask — Step C."""

from __future__ import annotations

import os
from datetime import date

from dotenv import load_dotenv
from openai import OpenAI

from server.schemas import AskResponse

load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"
# gpt-4o-mini rough catalog rates ($ / 1M tokens) for local spend guard only
_INPUT_PER_M = 0.15
_OUTPUT_PER_M = 0.60
_HARD_MAX_TOKENS = 500

_spend_day: date | None = None
_spend_usd: float = 0.0


def _ask_max_tokens() -> int:
    raw = int(os.getenv("ASK_MAX_TOKENS", "300"))
    return max(1, min(raw, _HARD_MAX_TOKENS))


def _ask_max_usd() -> float:
    return float(os.getenv("ASK_MAX_USD", "1.0"))


def _reset_daily_if_needed() -> None:
    global _spend_day, _spend_usd
    today = date.today()
    if _spend_day != today:
        _spend_day = today
        _spend_usd = 0.0


def _estimate_call_usd(question: str, max_tokens: int) -> float:
    input_tokens = max(1, len(question) // 4 + 40)
    return (input_tokens * _INPUT_PER_M + max_tokens * _OUTPUT_PER_M) / 1_000_000


def ask_openai(question: str) -> AskResponse:
    global _spend_usd

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-your-key"):
        raise ValueError("OPENAI_API_KEY is missing. Copy .env.example to .env and add your key.")

    max_tokens = _ask_max_tokens()
    ask_max_usd = _ask_max_usd()
    _reset_daily_if_needed()
    predicted = _estimate_call_usd(question, max_tokens)
    if _spend_usd + predicted > ask_max_usd:
        raise ValueError(
            f"ASK daily spend guard reached (ASK_MAX_USD={ask_max_usd}). "
            "Raise ASK_MAX_USD in .env or wait until tomorrow. "
            "Platform OpenAI billing limits are separate (dashboard)."
        )

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
        max_tokens=max_tokens,
    )

    usage = completion.usage
    if usage is not None:
        actual = (usage.prompt_tokens * _INPUT_PER_M + usage.completion_tokens * _OUTPUT_PER_M) / 1_000_000
    else:
        actual = predicted
    _spend_usd += actual

    answer = completion.choices[0].message.content or "No answer returned."
    return AskResponse(answer=answer.strip(), confidence=0.85)
