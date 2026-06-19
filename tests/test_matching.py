"""
Owns: known-answer tests for core.matching pure functions.
Must not: perform I/O; must not import adapters.
May import: pytest, core.matching.

not_measured: real barcode scanner device, EAN-14 edge cases beyond listed fixtures,
              non-ASCII barcodes, real network or DB calls.
"""

from core.matching import find_best_match, match_score


def test_exact_match_score_is_1():
    # normalize("widget-a") == normalize("widget-a") → SequenceMatcher → 1.0
    assert match_score("widget-a", "widget-a") == 1.0


def test_ean14_leading_zero_stripped_matches():
    # "01234567890123": 14 digits, starts with '0' → strip → "1234567890123"
    # candidate "1234567890123" → match_score = 1.0 → above threshold
    result, score = find_best_match("01234567890123", ["1234567890123"])
    assert result == "1234567890123"
    assert score == 1.0


def test_strong_match_beats_decoys():
    # normalize("widget-a") vs normalize("widget-a") → 1.0
    # vs normalize("gadget-z") and normalize("other-x") → both < 1.0
    result, score = find_best_match("widget-a", ["gadget-z", "widget-a", "other-x"])
    assert result == "widget-a"
    assert score == 1.0


def test_below_threshold_returns_none():
    # SequenceMatcher(None, "abc", "xyz").ratio() == 0.0 (no common chars)
    # 0.0 < default threshold 0.6 → (None, 0.0)
    result, score = find_best_match("abc", ["xyz"])
    assert result is None
    assert score == 0.0


def test_empty_barcode_returns_none():
    # strip_ean14("") = ""; normalize("") = "" → guard fires → (None, 0.0)
    result, score = find_best_match("", ["widget-a"])
    assert result is None
    assert score == 0.0


def test_empty_candidates_returns_none():
    # no candidates → (None, 0.0) immediately
    result, score = find_best_match("widget-a", [])
    assert result is None
    assert score == 0.0


def test_whitespace_only_barcode_returns_none():
    # strip_ean14("   ") = "   "; normalize("   ") = "" → guard fires → (None, 0.0)
    result, score = find_best_match("   ", ["widget-a"])
    assert result is None
    assert score == 0.0


def test_tied_scores_first_candidate_wins():
    # normalize("aa") = "aa"; normalize("ab") = "ab"; normalize("ba") = "ba"
    # SequenceMatcher("aa","ab").ratio() = 2*1/(2+2) = 0.5  (one 'a' matched)
    # SequenceMatcher("aa","ba").ratio() = 2*1/(2+2) = 0.5  (one 'a' matched)
    # threshold=0.4 so both qualify; strict > means first candidate keeps the win
    result, score = find_best_match("aa", ["ab", "ba"], threshold=0.4)
    assert result == "ab"
    assert score == 0.5
