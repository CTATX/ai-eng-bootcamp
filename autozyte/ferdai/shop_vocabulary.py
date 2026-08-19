"""Shop domain vocabulary — abbreviations Jake must not confuse (no LLM).

FACT: these are shop-standard term definitions, not diagnoses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

# Each concept: canonical label, search aliases, and labels that must NOT match.
@dataclass(frozen=True)
class ShopConcept:
    id: str
    canonical: str
    aliases: tuple[str, ...]
    excludes: tuple[str, ...] = ()


SHOP_CONCEPTS: tuple[ShopConcept, ...] = (
    ShopConcept(
        id="aos",
        canonical="Air-oil separator (AOS)",
        aliases=(
            "aos",
            "air oil separator",
            "air-oil separator",
            "oil separator",
            "a-o-s",
        ),
        excludes=("a/c", "air conditioning", "air cond", "hvac", "ac service", "ac recharge"),
    ),
    ShopConcept(
        id="ac",
        canonical="Air conditioning (A/C)",
        aliases=(
            "a/c",
            "a c",
            "ac",
            "air conditioning",
            "air cond",
            "hvac",
            "ac service",
            "ac recharge",
            "no cold air",
        ),
        excludes=("aos", "air oil separator", "oil separator", "a-o-s"),
    ),
    ShopConcept(
        id="oil_leak",
        canonical="Oil leak / consumption",
        aliases=("oil leak", "oil smell", "burning oil", "oil consumption", "smoke"),
        excludes=(),
    ),
    ShopConcept(
        id="brakes",
        canonical="Brake service",
        aliases=("brake", "brakes", "brake noise", "squeal", "grind"),
        excludes=(),
    ),
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def detect_complaint_concepts(complaint: str | None) -> list[ShopConcept]:
    """Which shop concepts appear in the customer complaint."""
    if not complaint or not complaint.strip():
        return []
    text = _normalize(complaint)
    found: list[ShopConcept] = []
    for concept in SHOP_CONCEPTS:
        for alias in concept.aliases:
            alias_norm = _normalize(alias)
            if len(alias_norm) <= 2:
                # Standalone token match for short codes like "ac" — word boundary
                if re.search(rf"\b{re.escape(alias_norm)}\b", text):
                    found.append(concept)
                    break
            elif alias_norm in text:
                found.append(concept)
                break
    return found


def _complaint_tokens(complaint: str | None) -> list[str]:
    if not complaint:
        return []
    tokens = [token for token in re.split(r"[^a-z0-9]+", complaint.lower()) if len(token) > 2]
    for concept in detect_complaint_concepts(complaint):
        for alias in concept.aliases:
            for token in re.split(r"[^a-z0-9]+", alias.lower()):
                if len(token) > 2 and token not in tokens:
                    tokens.append(token)
    return tokens


def score_reason_for_concepts(reason_label: str, concepts: list[ShopConcept]) -> tuple[int, list[str]]:
    """Score how well a warehouse service reason matches complaint concepts.

    Returns (score, notes). Negative score = explicit confusion (e.g. AOS vs A/C).
    """
    if not concepts:
        return 0, []

    label = _normalize(reason_label)
    notes: list[str] = []
    score = 0

    for concept in concepts:
        excluded = any(excl in label for excl in concept.excludes)
        if excluded:
            score -= 10
            notes.append(f"Excluded: '{reason_label}' conflicts with {concept.canonical}")
            continue

        matched_alias: str | None = None
        for alias in concept.aliases:
            alias_norm = _normalize(alias)
            if alias_norm in label or (len(alias_norm) > 2 and alias_norm in label.replace("/", " ")):
                matched_alias = alias
                break
            if alias_norm in {"aos"} and "aos" in label:
                matched_alias = alias
                break

        if matched_alias:
            score += 5
            notes.append(f"Matched {concept.canonical} via '{matched_alias}' in '{reason_label}'")
        else:
            # Partial token overlap (e.g. "oil" in complaint + "oil separator" in label)
            for token in _complaint_tokens(concept.canonical):
                if token in label and token not in {"service", "shop"}:
                    score += 2
                    notes.append(f"Partial match {concept.canonical} on '{token}'")
                    break

    return score, notes


def best_complaint_reason_match(
    reason_labels: list[str],
    concepts: list[ShopConcept],
) -> tuple[str | None, int, list[str]]:
    """Pick best-matching reason for complaint concepts, or None if no honest match."""
    if not concepts or not reason_labels:
        return None, 0, []

    best_label: str | None = None
    best_score = 0
    all_notes: list[str] = []

    for label in reason_labels:
        score, notes = score_reason_for_concepts(label, concepts)
        all_notes.extend(notes)
        if score > best_score:
            best_score = score
            best_label = label

    if best_score <= 0:
        return None, best_score, all_notes
    return best_label, best_score, all_notes


def complaint_interpretation(complaint: str | None) -> dict[str, Any]:
    concepts = detect_complaint_concepts(complaint)
    return {
        "raw": complaint,
        "concepts": [
            {"id": c.id, "canonical": c.canonical, "tag": "FACT"}
            for c in concepts
        ],
        "tag": "FACT" if concepts else "UNKNOWN",
        "note": (
            "Shop vocabulary mapping — not a diagnosis."
            if concepts
            else "No mapped shop terms in complaint."
        ),
    }
