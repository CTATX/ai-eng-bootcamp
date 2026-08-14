"""OpenAI call for POST /ask — Step C."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"


@dataclass(frozen=True)
class OpenAICallResult:
    answer: str
    model_id: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    latency_ms: int


def ask_openai(question: str) -> OpenAICallResult:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.startswith("sk-your-key"):
        raise ValueError("OPENAI_API_KEY is missing. Copy .env.example to .env and add your key.")

    client = OpenAI(api_key=api_key)
    started = time.perf_counter()
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
    latency_ms = round((time.perf_counter() - started) * 1000)

    answer = completion.choices[0].message.content or "No answer returned."
    usage = completion.usage
    input_tokens = int(usage.prompt_tokens if usage else 0)
    output_tokens = int(usage.completion_tokens if usage else 0)
    prompt_details = getattr(usage, "prompt_tokens_details", None)
    cached_input_tokens = int(getattr(prompt_details, "cached_tokens", 0) or 0)
    return OpenAICallResult(
        answer=answer.strip(),
        model_id=completion.model or DEFAULT_MODEL,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_input_tokens,
        latency_ms=latency_ms,
    )
