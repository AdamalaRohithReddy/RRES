"""Unit tests for TextCleaner."""
from src.ingestion.cleaner import TextCleaner


def test_clean_text_normalizes_whitespace():
    raw = "The   scheme    provides     financial   assistance."
    expected = "The scheme provides financial assistance."
    assert TextCleaner.clean(raw) == expected


def test_clean_text_preserves_paragraphs():
    raw = "Paragraph one with official text.\n\n\n\nParagraph two with eligibility rules."
    expected = "Paragraph one with official text.\n\nParagraph two with eligibility rules."
    assert TextCleaner.clean(raw) == expected


def test_clean_text_preserves_numbers_currency_and_percentages():
    raw = "Under APY, monthly pension of Rs. 1,000 to ₹ 5,000 is given at age 60. Return of 8.5% is projected."
    cleaned = TextCleaner.clean(raw)
    assert "Rs. 1,000" in cleaned
    assert "₹ 5,000" in cleaned
    assert "60" in cleaned
    assert "8.5%" in cleaned


def test_clean_text_preserves_government_terms():
    raw = "Eligible citizens must link Aadhaar with DBT-enabled Savings Bank Account for PM-KISAN & APY."
    cleaned = TextCleaner.clean(raw)
    assert "Aadhaar" in cleaned
    assert "DBT-enabled" in cleaned
    assert "PM-KISAN" in cleaned
    assert "APY" in cleaned


def test_clean_text_fixes_hyphenation():
    raw = "The citizen must fulfill the eligi-\nbility criteria before enrolling."
    cleaned = TextCleaner.clean(raw)
    assert "eligibility" in cleaned
