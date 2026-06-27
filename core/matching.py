"""
Owns: pure barcode/model matching functions (strip, normalize, score, find_best,
      forward-only sequence matcher, PO-level resolver).
Must not: perform any I/O; must not import adapters, services, or read environment variables.
May import: stdlib (difflib, dataclasses, enum).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum


def strip_ean14(barcode: str) -> str:
    """Strip the leading '0' from a 14-digit EAN-14 barcode; return unchanged otherwise."""
    if len(barcode) == 14 and barcode.isdigit() and barcode.startswith("0"):
        return barcode[1:]
    return barcode


def normalize(s: str) -> str:
    """Lowercase, strip leading/trailing whitespace, collapse internal whitespace."""
    return " ".join(s.split()).lower()


def normalize_key(s: str) -> str:
    """Normalize for structural key comparison: lowercase, remove spaces and hyphens.

    Used exclusively by the prefix-collision guard in resolve_model so that
    punctuation variants (e.g. "B36-CL80-SNS-X") collapse to the same key as
    their hyphen-free counterpart ("B36CL80SNSX") before prefix/startswith tests.
    """
    return s.lower().replace("-", "").replace(" ", "")


def match_score(barcode: str, candidate_model: str) -> float:
    """SequenceMatcher ratio on normalized forms of barcode and candidate_model."""
    a = normalize(barcode)
    b = normalize(candidate_model)
    return SequenceMatcher(None, a, b).ratio()


def find_best_match(
    barcode: str,
    candidates: list[str],
    threshold: float = 0.6,
) -> tuple[str | None, float]:
    """Return (best_match, score) or (None, 0.0) if no candidate scores at or above threshold.

    Applies strip_ean14 to barcode before scoring. Ties go to the first
    candidate in the list — deterministic, no random tiebreak.
    """
    if not candidates:
        return None, 0.0

    processed = strip_ean14(barcode)
    if not normalize(processed):
        return None, 0.0

    best_match: str | None = None
    best_score = 0.0
    for candidate in candidates:
        score = match_score(processed, candidate)
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_score < threshold:
        return None, 0.0
    return best_match, best_score


# ── Forward-only sequence matcher ─────────────────────────────────────────────


class MatchStatus(Enum):
    AUTO = "auto"
    NEEDS_INPUT = "needs_input"


@dataclass(frozen=True)
class MatchResult:
    """Typed result from resolve_model — never None.

    AUTO:        exactly one PO model matched; model is set, candidates is empty.
    NEEDS_INPUT: zero or two-or-more matches; model is None, candidates holds every match found.
    """

    status: MatchStatus
    model: str | None
    candidates: list[str] = field(default_factory=list)


def model_matches_barcode(model: str, barcode: str) -> bool:
    """Forward-only subsequence walk: does model appear as an ordered subsequence of barcode?

    Normalizes both to lowercase; otherwise compares characters exactly.
    Advances through the barcode left-to-right, never backtracking. Once a barcode
    position is consumed it is gone — this is what makes near-twin models self-reject
    (see the adversarial twin test in tests/test_sequence_matcher.py).

    Returns False (fail-closed) when either argument is empty.
    """
    if not model or not barcode:
        return False

    model_lower = model.lower()
    barcode_lower = barcode.lower()

    barcode_pos = 0
    for model_char in model_lower:
        # Scan forward for the next needed character; never step back.
        while barcode_pos < len(barcode_lower) and barcode_lower[barcode_pos] != model_char:
            barcode_pos += 1
        if barcode_pos >= len(barcode_lower):
            return False
        barcode_pos += 1  # lock this position and advance past it

    return True


def resolve_model(barcode: str, po_models: list[str]) -> MatchResult:
    """Run model_matches_barcode for every model on the PO and return a typed MatchResult.

    EXACTLY ONE match, not prefix-ambiguous → AUTO(model=..., candidates=[])
    ZERO matches                            → NEEDS_INPUT(model=None, candidates=[])
    TWO OR MORE matches                     → NEEDS_INPUT(model=None, candidates=[all matched])
    ONE match but prefix-ambiguous          → NEEDS_INPUT(model=None, candidates=[matched])

    Prefix-collision guard: before evaluating walk results, normalize every PO model
    with normalize_key (lowercase, strip spaces and hyphens). If any two normalized
    keys share a prefix relationship, the shorter model is marked prefix-ambiguous.
    A single walk-match on a prefix-ambiguous model returns NEEDS_INPUT rather than
    AUTO, preventing auto-bind of a base SKU when the scanned unit is a variant
    whose model differs only in punctuation (e.g. "B36-CL80-SNS-X" vs "B36CL80SNS").

    Never auto-picks when multiple models match. Always returns a MatchResult — never None.
    """
    norm_keys = [normalize_key(m) for m in po_models]
    prefix_ambiguous: set[str] = set()
    for i, m1 in enumerate(po_models):
        for j in range(len(po_models)):
            if i != j and norm_keys[j].startswith(norm_keys[i]) and norm_keys[i] != norm_keys[j]:
                prefix_ambiguous.add(m1)

    matched = [m for m in po_models if model_matches_barcode(m, barcode)]
    if len(matched) == 1 and matched[0] not in prefix_ambiguous:
        return MatchResult(status=MatchStatus.AUTO, model=matched[0], candidates=[])
    return MatchResult(status=MatchStatus.NEEDS_INPUT, model=None, candidates=matched)
