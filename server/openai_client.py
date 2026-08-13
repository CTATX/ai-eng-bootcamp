"""OpenAI call for POST /ask — Step C."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

from server.schemas import AskResponse

load_dotenv()

DEFAULT_MODEL = "gpt-4o-mini"


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
