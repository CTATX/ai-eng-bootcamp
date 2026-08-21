"""Heuristic prompt complexity analysis → workload forecast for cost engine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from cost_engine import RESULT_SHAPE_TOKENS, Workload

# Buffer tokens not visible in the pasted prompt (system prompt, formatting).
SYSTEM_BUFFER_TOKENS = 200
CONTEXT_SAFETY_MARGIN = 0.10

OUTPUT_DEPTH_SIGNALS: list[tuple[int, re.Pattern[str]]] = [
    (5, re.compile(r"\b(report|whitepaper|comprehensive|detailed analysis|multi-page)\b", re.I)),
    (4, re.compile(r"\b(essay|section|outline|architecture|design doc)\b", re.I)),
    (3, re.compile(r"\b(paragraph|summary|explain|describe|compare)\b", re.I)),
    (1, re.compile(r"\b(one (line|sentence)|brief|yes/no|true/false|single word)\b", re.I)),
]

REASONING_SIGNALS: list[tuple[int, re.Pattern[str]]] = [
    (2, re.compile(r"\b(debug|root cause|evaluate|trade-?off|optimize|plan|step by step)\b", re.I)),
    (2, re.compile(r"\b(compare|analyze|synthesize|reason|prove|derive)\b", re.I)),
    (1, re.compile(r"\b(list|classify|extract|summarize|translate|format)\b", re.I)),
]

VERIFICATION_SIGNALS: list[tuple[int, re.Pattern[str]]] = [
    (2, re.compile(r"\b(double-?check|verify|validate|compliance|audit|citation|source)\b", re.I)),
    (2, re.compile(r"\b(accuracy|fact-?check|peer review|quality gate)\b", re.I)),
    (1, re.compile(r"\b(review|check|ensure|confirm)\b", re.I)),
]

AMBIGUITY_SIGNALS: list[tuple[int, re.Pattern[str]]] = [
    (2, re.compile(r"\b(best effort|as needed|etc\.?|and so on|whatever works)\b", re.I)),
    (2, re.compile(r"\b(maybe|possibly|rough|approximate|TBD|unclear)\b", re.I)),
    (1, re.compile(r"\b(flexible|open-?ended|creative freedom)\b", re.I)),
]

AGENTIC_SIGNALS: list[tuple[int, re.Pattern[str]]] = [
    (2, re.compile(r"\b(agent|tool use|iterate|loop until|multi-?step workflow)\b", re.I)),
    (1, re.compile(r"\b(search|browse|fetch|call api|run command)\b", re.I)),
]

COMPLEXITY_LABELS = (
    (10, "Simple"),
    (17, "Moderate"),
    (22, "Complex"),
    (26, "Agentic"),
)


@dataclass(frozen=True)
class ComplexityDimensions:
    input_size: int
    output_depth: int
    reasoning_depth: int
    verification_need: int
    ambiguity_risk: int
    agentic_pattern: int = 1

    @property
    def composite_score(self) -> int:
        return (
            self.input_size
            + self.output_depth
            + self.reasoning_depth
            + self.verification_need
            + self.ambiguity_risk
            + self.agentic_pattern
        )

    @property
    def label(self) -> str:
        score = self.composite_score
        for threshold, name in COMPLEXITY_LABELS:
            if score < threshold:
                return name
        return "Agentic"

    @property
    def uncertainty_pct(self) -> float:
        """Forecast confidence margin — higher ambiguity → wider close delta."""
        base = 0.12
        ambiguity_bonus = (self.ambiguity_risk - 1) * 0.06
        agentic_bonus = (self.agentic_pattern - 1) * 0.04
        return min(0.45, base + ambiguity_bonus + agentic_bonus)


@dataclass
class WorkloadForecast:
    workload: Workload
    dimensions: ComplexityDimensions
    input_tokens_raw: int
    rationale: list[str] = field(default_factory=list)
    headroom_savings_pct: float = 0.0


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _score_from_patterns(text: str, patterns: list[tuple[int, re.Pattern[str]]], default: int = 1) -> int:
    score = default
    for weight, pattern in patterns:
        if pattern.search(text):
            score = min(5, score + weight)
    return _clamp(score, 1, 5)


def _score_input_size(token_count: int) -> int:
    if token_count < 800:
        return 1
    if token_count < 2_000:
        return 2
    if token_count < 8_000:
        return 3
    if token_count < 30_000:
        return 4
    return 5


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    try:
        import tiktoken

        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception:
        # Fallback: ~4 chars per token for English prose.
        return max(1, len(text) // 4)


def score_complexity(prompt_text: str, token_count: int | None = None) -> ComplexityDimensions:
    text = prompt_text.strip()
    tokens = token_count if token_count is not None else count_tokens(text)
    return ComplexityDimensions(
        input_size=_score_input_size(tokens),
        output_depth=_score_from_patterns(text, OUTPUT_DEPTH_SIGNALS, default=2),
        reasoning_depth=_score_from_patterns(text, REASONING_SIGNALS, default=1),
        verification_need=_score_from_patterns(text, VERIFICATION_SIGNALS, default=1),
        ambiguity_risk=_score_from_patterns(text, AMBIGUITY_SIGNALS, default=1),
        agentic_pattern=_score_from_patterns(text, AGENTIC_SIGNALS, default=1),
    )


def _pick_result_shape(output_depth: int) -> str:
    shapes = list(RESULT_SHAPE_TOKENS.keys())
    if output_depth <= 2:
        return shapes[0]
    if output_depth <= 3:
        return shapes[1]
    return shapes[2]


def _pick_primary_steps(reasoning: int, agentic: int, composite: int) -> int:
    base = 1
    if reasoning >= 3:
        base += 1
    if reasoning >= 4:
        base += 1
    if agentic >= 3:
        base += 1
    if composite >= 22:
        base += 1
    return _clamp(base, 1, 5)


def _pick_checker_steps(verification: int, ambiguity: int) -> int:
    steps = 0
    if verification >= 2:
        steps += 1
    if verification >= 4:
        steps += 1
    if ambiguity >= 3 and steps < 2:
        steps += 1
    return _clamp(steps, 0, 3)


def estimate_headroom_savings(dimensions: ComplexityDimensions, token_count: int) -> float:
    """Inspired by Netflix Headroom: redundant context shrinks at higher input sizes."""
    if token_count < 1_500:
        return 0.15
    if token_count < 8_000:
        return 0.35
    if dimensions.agentic_pattern >= 3:
        return 0.55
    return 0.45


def forecast_workload(
    prompt_text: str,
    tasks_per_day: int = 50,
    *,
    apply_headroom: bool = False,
) -> WorkloadForecast:
    raw_tokens = count_tokens(prompt_text)
    dimensions = score_complexity(prompt_text, raw_tokens)
    rationale: list[str] = []

    buffered_tokens = int((raw_tokens + SYSTEM_BUFFER_TOKENS) * (1 + CONTEXT_SAFETY_MARGIN))
    input_tokens = _clamp(buffered_tokens, 500, 500_000)

    result_shape = _pick_result_shape(dimensions.output_depth)
    primary_steps = _pick_primary_steps(
        dimensions.reasoning_depth,
        dimensions.agentic_pattern,
        dimensions.composite_score,
    )
    checker_steps = _pick_checker_steps(dimensions.verification_need, dimensions.ambiguity_risk)

    headroom_pct = estimate_headroom_savings(dimensions, raw_tokens)
    if apply_headroom and headroom_pct > 0:
        optimized = int(input_tokens * (1 - headroom_pct))
        rationale.append(
            f"Headroom-style context trim could cut input tokens ~{headroom_pct:.0%} "
            f"({input_tokens:,} → {optimized:,})."
        )
        input_tokens = _clamp(optimized, 500, 500_000)

    rationale.extend(
        [
            f"Complexity: {dimensions.label} (score {dimensions.composite_score}/30).",
            f"Input tokens: {raw_tokens:,} raw → {input_tokens:,} with buffer.",
            f"Output shape: {result_shape} (output depth {dimensions.output_depth}/5).",
            f"Steps: {primary_steps} primary + {checker_steps} checker "
            f"(reasoning {dimensions.reasoning_depth}/5, verification {dimensions.verification_need}/5).",
        ]
    )
    if dimensions.ambiguity_risk >= 3:
        rationale.append("Ambiguity detected — close cost delta widened for retries.")

    workload = Workload(
        input_tokens=input_tokens,
        result_shape=result_shape,
        primary_steps=primary_steps,
        checker_steps=checker_steps,
        tasks_per_day=tasks_per_day,
    )
    return WorkloadForecast(
        workload=workload,
        dimensions=dimensions,
        input_tokens_raw=raw_tokens,
        rationale=rationale,
        headroom_savings_pct=headroom_pct if apply_headroom else 0.0,
    )
