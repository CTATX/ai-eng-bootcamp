"""Shop domain vocabulary — abbreviations Jake must not confuse (no LLM).

FACT: these are shop-standard term definitions, not diagnoses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class ComplaintMatchResult:
    """Outcome of matching customer complaint to warehouse service names."""

    matched: bool
    reason: str | None
    score: int
    notes: list[str] = field(default_factory=list)
    clarify: list[dict[str, Any]] = field(default_factory=list)


def _clarify_other_visits(reason_labels: list[str], *, overlap_tokens: list[str] | None = None) -> list[dict[str, Any]]:
    """Past or weakly similar jobs — advisor must clarify; never auto-diagnose."""
    items: list[dict[str, Any]] = []
    for label in reason_labels:
        hits = [t for t in (overlap_tokens or []) if t in label.lower()]
        if overlap_tokens and hits:
            prompt = (
                f"Similar wording only ({', '.join(hits)}) — please clarify with customer; "
                f"not confirmed as '{label}'."
            )
        else:
            prompt = (
                f"Past visit on file: '{label}' — not matched to this complaint; "
                "ask customer if related."
            )
        items.append({"label": label, "tag": "CLARIFY", "prompt": prompt})
    return items[:6]


def resolve_complaint_match(
    complaint: str | None,
    reason_labels: list[str],
) -> ComplaintMatchResult:
    """Hard match gate — no invented diagnosis when score is insufficient."""
    if not complaint or not complaint.strip():
        return ComplaintMatchResult(matched=False, reason=None, score=0)

    if not reason_labels:
        return ComplaintMatchResult(
            matched=False,
            reason=None,
            score=0,
            notes=["No service names in warehouse for this vehicle."],
        )

    concepts = detect_complaint_concepts(complaint)
    if concepts:
        pick, score, notes = best_complaint_reason_match(reason_labels, concepts)
        if pick and score > 0:
            return ComplaintMatchResult(matched=True, reason=pick, score=score, notes=notes)
        return ComplaintMatchResult(
            matched=False,
            reason=None,
            score=score,
            notes=notes,
            clarify=_clarify_other_visits(reason_labels),
        )

    tokens = [t for t in _complaint_tokens(complaint) if len(t) > 2]
    if not tokens:
        return ComplaintMatchResult(
            matched=False,
            reason=None,
            score=0,
            notes=["Complaint has no mappable shop terms."],
            clarify=_clarify_other_visits(reason_labels),
        )

    best_label: str | None = None
    best_hits: list[str] = []
    for label in reason_labels:
        hits = [t for t in tokens if t in label.lower()]
        if len(hits) > len(best_hits):
            best_hits = hits
            best_label = label

    if best_label and best_hits:
        strong = len(best_hits) >= 2 or any(len(h) >= 4 for h in best_hits)
        if strong:
            return ComplaintMatchResult(
                matched=True,
                reason=best_label,
                score=len(best_hits),
                notes=[f"Token match on {', '.join(best_hits)} in '{best_label}'"],
            )
        return ComplaintMatchResult(
            matched=False,
            reason=None,
            score=len(best_hits),
            notes=[f"Weak overlap only ({', '.join(best_hits)}) — clarify required"],
            clarify=_clarify_other_visits(reason_labels, overlap_tokens=best_hits),
        )

    return ComplaintMatchResult(
        matched=False,
        reason=None,
        score=0,
        clarify=_clarify_other_visits(reason_labels),
    )


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
