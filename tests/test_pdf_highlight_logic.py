"""
Tests for the PDF text-highlighting match logic (mirrors the TypeScript implementation).

The frontend uses overlapScore() to decide whether a PDF text item should be
highlighted. These tests verify the normalisation and matching rules in Python,
acting as a specification that the TypeScript implementation must satisfy.
"""

import re


def norm(s: str) -> str:
    """Mirror of the TypeScript norm() function."""
    s = s.lower()
    s = s.replace("‘", "'").replace("’", "'")   # curly single quotes
    s = s.replace("“", "'").replace("”", "'")   # curly double quotes
    s = re.sub(r"[\s\-–—]+", " ", s)            # dashes/whitespace → space
    s = re.sub(r"[^\w\s]", "", s)                          # strip punctuation
    return s.strip()


def overlap_score(item_str: str, quote_norm: str) -> float:
    """Mirror of the TypeScript overlapScore() function."""
    n_item = norm(item_str)
    if not n_item or len(n_item) < 3:
        return 0.0
    if quote_norm and quote_norm in n_item or n_item in quote_norm:
        return 1.0
    tokens = [t for t in n_item.split() if len(t) > 3]
    if not tokens:
        return 0.0
    matched = [t for t in tokens if t in quote_norm]
    return len(matched) / len(tokens)


# ── normalisation ─────────────────────────────────────────────────────────────

def test_norm_lowercases():
    assert norm("Annual Turnover") == "annual turnover"


def test_norm_collapses_whitespace():
    assert norm("INR  7.5   Crore") == "inr 75 crore"


def test_norm_strips_punctuation():
    assert norm("Rs. 5,00,000/-") == "rs 500000"


def test_norm_handles_curly_quotes():
    assert norm("“GST”") == "gst"


def test_norm_collapses_dashes():
    assert norm("2022-23") == "2022 23"


# ── strong match (score = 1.0) ────────────────────────────────────────────────

def test_exact_match_scores_1():
    quote = norm("The bidder has completed 5 similar projects in the last 3 years")
    assert overlap_score("The bidder has completed", quote) == 1.0


def test_substring_of_quote_scores_1():
    quote = norm("Annual turnover of INR 7.5 crore for FY 2022-23")
    assert overlap_score("INR 7.5 crore", quote) == 1.0


def test_case_insensitive_match():
    quote = norm("GST Registration Number: 27AABCU9603R1ZX")
    assert overlap_score("gst registration number", quote) == 1.0


# ── partial match (score >= 0.6) ─────────────────────────────────────────────

def test_partial_word_overlap():
    quote = norm("The bidder has completed similar construction projects")
    score = overlap_score("bidder completed construction", quote)
    assert score >= 0.6


def test_partial_match_below_threshold():
    quote = norm("Annual turnover of INR 7.5 crore")
    # "xyz abc def" — none of these words appear in quote
    score = overlap_score("xyz abc def ghi", quote)
    assert score < 0.6


# ── no match ─────────────────────────────────────────────────────────────────

def test_unrelated_text_scores_0():
    quote = norm("Annual turnover of INR 7.5 crore")
    assert overlap_score("Page 1 of 12", quote) == 0.0


def test_short_item_scores_0():
    quote = norm("Annual turnover of INR 7.5 crore")
    assert overlap_score("of", quote) == 0.0  # len < 3 after norm


def test_empty_item_scores_0():
    assert overlap_score("", "annual turnover") == 0.0


def test_no_quote_scores_0():
    assert overlap_score("some text", "") == 0.0


# ── scanned document case ─────────────────────────────────────────────────────

def test_scanned_pdf_no_text_items():
    """
    Scanned PDFs produce no text items — the text layer is empty.
    overlapScore is never called; frontend shows "scanned page" fallback.
    Verify the norm function handles empty input gracefully.
    """
    assert norm("") == ""
    assert overlap_score("", norm("any evidence quote")) == 0.0
