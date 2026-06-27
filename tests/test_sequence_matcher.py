"""
Owns: adversarial known-answer tests for model_matches_barcode and resolve_model.
Must not: perform I/O; must not import adapters.
May import: pytest, core.matching.

not_measured: non-ASCII / Unicode characters in barcodes; barcodes > 200 characters;
              concurrent calls to resolve_model; locale-dependent case folding.

Mutation targets (mutmut must kill every one of these mutants):
  - Forward-only property: a mutant that resets barcode_pos on each model character
    will find '7' behind the locked position in test_critical_twin_forward_only_rejects.
  - Character equality: a mutant replacing `!=` with `<` in the inner scan loop
    fails test_exact_barcode_matches_itself (correct char skipped).
  - Exactly-one branch: a mutant replacing `len(matched) == 1` with `len(matched) >= 1`
    would auto-pick from the ambiguous set in test_resolve_ambiguous_two_or_more_is_needs_input.
  - Empty-input guard: a mutant dropping `if not model or not barcode` allows empty
    model "" to match any barcode in test_empty_model_returns_false.
"""

from __future__ import annotations

from core.matching import MatchResult, MatchStatus, model_matches_barcode, resolve_model

# ── model_matches_barcode — happy path ───────────────────────────────────────


def test_junk_prefix_matches() -> None:
    # Barcode "12z SHX78CM5N": junk prefix '1','2','z',' ' is skipped; walk finds
    # S,H,X,7,8,C,M,5,N in order after the prefix.
    assert model_matches_barcode("SHX78CM5N", "12z SHX78CM5N") is True


def test_junk_split_mid_model_matches() -> None:
    # Barcode "shx78 bpy3 cm50n": vendor junk tokens 'bpy3' are interleaved mid-model.
    # Positions: s(0)h(1)x(2)7(3)8(4) (5)b(6)p(7)y(8)3(9) (10)c(11)m(12)5(13)0(14)n(15)
    # Walk for "SHX78CM5N": S→s(0) H→h(1) X→x(2) 7→7(3) 8→8(4) C→(skip 5..10)→c(11)
    #   M→m(12) 5→5(13) N→(skip 0)→n(15) — all consumed forward, no backtrack.
    assert model_matches_barcode("SHX78CM5N", "shx78 bpy3 cm50n") is True


def test_exact_barcode_matches_itself() -> None:
    assert model_matches_barcode("SHX78CM5N", "SHX78CM5N") is True


def test_case_insensitive_match() -> None:
    assert model_matches_barcode("shx78cm5n", "SHX78CM5N") is True
    assert model_matches_barcode("SHX78CM5N", "shx78cm5n") is True


def test_model_as_prefix_of_barcode_matches() -> None:
    # Model is shorter; trailing barcode characters are irrelevant.
    assert model_matches_barcode("ABC", "ABCXYZ") is True


# ── model_matches_barcode — THE CRITICAL TWIN TEST ───────────────────────────


def test_critical_twin_forward_only_rejects_wrong_twin() -> None:
    """THE CORE SAFETY PROOF — forward-only walk must reject the near-twin model.

    Barcode:  "shx78 bpy3 cm50n"
    Positions: s(0) h(1) x(2) 7(3) 8(4) ' '(5) b(6) p(7) y(8) 3(9) ' '(10)
               c(11) m(12) 5(13) 0(14) n(15)

    Walk for model "SHP78CM5N" (wrong twin, X→P mismatch):
      's' → found at pos 0; advance to pos 1
      'h' → found at pos 1; advance to pos 2
      'p' → scan from pos 2: x(no) 7(no) 8(no) ' '(no) b(no) p(YES) at pos 7; advance to pos 8
      '7' → scan from pos 8: y(no) 3(no) ' '(no) c(no) m(no) 5(no) 0(no) n(no) → EXHAUSTED

    The '7' was at position 3, which is now behind the locked position (pos 8).
    Forward-only prevents backtracking: those positions are gone → return False.

    A mutant that resets barcode_pos for each model character (allowing backtracking)
    would find '7' at position 3 and continue — that mutant must be killed by this test.
    A mutant that replaces `!= model_char` with `< model_char` in the scan loop would
    skip over the correct character — that mutant is also killed by this test.
    """
    assert model_matches_barcode("SHP78CM5N", "shx78 bpy3 cm50n") is False


# ── model_matches_barcode — twin self-match / cross-match ────────────────────


def test_twin_matches_itself_not_sibling_clean_barcode() -> None:
    # With a clean barcode (no junk), each twin matches only itself, not the other.
    assert model_matches_barcode("SHX78CM5N", "SHX78CM5N") is True
    assert model_matches_barcode("SHP78CM5N", "SHP78CM5N") is True
    assert model_matches_barcode("SHX78CM5N", "SHP78CM5N") is False
    assert model_matches_barcode("SHP78CM5N", "SHX78CM5N") is False


# ── model_matches_barcode — fail-closed edge cases ───────────────────────────


def test_empty_model_returns_false() -> None:
    # Fail-closed: an empty model string must never accidentally match anything.
    assert model_matches_barcode("", "SHX78CM5N") is False


def test_empty_barcode_returns_false() -> None:
    # Fail-closed: a non-empty model cannot be found in an empty barcode.
    assert model_matches_barcode("SHX78CM5N", "") is False


def test_both_empty_returns_false() -> None:
    assert model_matches_barcode("", "") is False


def test_model_longer_than_barcode_returns_false() -> None:
    # Cannot fit more model characters than there are barcode characters.
    assert model_matches_barcode("ABCDEFGH", "AB") is False


def test_model_equal_length_wrong_order_returns_false() -> None:
    # Barcode "ACB": A(0) C(1) B(2). Model "ABC":
    #   A→A(0); B→C(no)→B(YES)(2); C→exhausted(3) → False.
    assert model_matches_barcode("ABC", "ACB") is False


def test_model_equal_length_exact_returns_true() -> None:
    assert model_matches_barcode("ABC", "ABC") is True


# ── resolve_model ─────────────────────────────────────────────────────────────


def test_resolve_exactly_one_match_is_auto() -> None:
    # Clean barcode "SHX78CM5N": SHX model matches (exact), SHP does not (X≠P, no P in barcode).
    result = resolve_model("SHX78CM5N", ["SHX78CM5N", "SHP78CM5N"])
    assert result.status is MatchStatus.AUTO
    assert result.model == "SHX78CM5N"
    assert result.candidates == []


def test_resolve_zero_matches_is_needs_input_empty_candidates() -> None:
    # Barcode "ZZZZZZZ" shares no subsequence structure with either PO model.
    result = resolve_model("ZZZZZZZ", ["SHX78CM5N", "SHP78CM5N"])
    assert result.status is MatchStatus.NEEDS_INPUT
    assert result.model is None
    assert result.candidates == []


def test_resolve_ambiguous_two_or_more_is_needs_input_with_candidates() -> None:
    """A pathological barcode that completes BOTH twin walks → NEEDS_INPUT with both candidates.

    Barcode "SHXP78CM5N": S(0) H(1) X(2) P(3) 7(4) 8(5) C(6) M(7) 5(8) N(9)

    Walk for SHX78CM5N: S(0) H(1) X(2) 7(4) 8(5) C(6) M(7) 5(8) N(9) → True
      (P at pos 3 is skipped while scanning for '7')
    Walk for SHP78CM5N: S(0) H(1) P(3) 7(4) 8(5) C(6) M(7) 5(8) N(9) → True
      (X at pos 2 is skipped while scanning for 'P')

    Both models consume their characters in order → ambiguous.
    resolve_model must NOT auto-pick; it must return NEEDS_INPUT with both candidates.

    A mutant replacing `len(matched) == 1` with `len(matched) >= 1` would auto-pick
    SHX78CM5N (first match) — this test kills that mutant.
    """
    result = resolve_model("SHXP78CM5N", ["SHX78CM5N", "SHP78CM5N"])
    assert result.status is MatchStatus.NEEDS_INPUT
    assert result.model is None
    assert sorted(result.candidates) == ["SHP78CM5N", "SHX78CM5N"]


def test_resolve_empty_po_models_is_needs_input() -> None:
    result = resolve_model("SHX78CM5N", [])
    assert result.status is MatchStatus.NEEDS_INPUT
    assert result.model is None
    assert result.candidates == []


def test_resolve_always_returns_match_result_never_none() -> None:
    # resolve_model must never return None — always a typed MatchResult.
    result = resolve_model("anything", [])
    assert isinstance(result, MatchResult)


def test_resolve_single_model_on_po_that_matches_is_auto() -> None:
    # Single model on PO and barcode matches it → AUTO.
    result = resolve_model("SHX78CM5N", ["SHX78CM5N"])
    assert result.status is MatchStatus.AUTO
    assert result.model == "SHX78CM5N"


def test_resolve_single_model_on_po_that_does_not_match_is_needs_input() -> None:
    result = resolve_model("ZZZZZZZ", ["SHX78CM5N"])
    assert result.status is MatchStatus.NEEDS_INPUT
    assert result.model is None
    assert result.candidates == []
