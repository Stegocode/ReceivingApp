"""
Owns: pure barcode/model matching functions (strip, normalize, score, find_best).
Must not: perform any I/O; must not import adapters, services, or read environment variables.
May import: stdlib (difflib).
"""

from difflib import SequenceMatcher


def strip_ean14(barcode: str) -> str:
    """Strip the leading '0' from a 14-digit EAN-14 barcode; return unchanged otherwise."""
    if len(barcode) == 14 and barcode.isdigit() and barcode.startswith("0"):
        return barcode[1:]
    return barcode


def normalize(s: str) -> str:
    """Lowercase, strip leading/trailing whitespace, collapse internal whitespace."""
    return " ".join(s.split()).lower()


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
