import pytest
from app.services.validator import FactValidator, is_meaningless_number

def test_meaningless_number_detection():
    assert is_meaningless_number("4") is True
    assert is_meaningless_number("4 FY23") is True
    assert is_meaningless_number("Page 12") is True
    assert is_meaningless_number("• 4") is True
    assert is_meaningless_number("₹2,500 crore") is False
    assert is_meaningless_number("15 bar") is False

def test_accept_valid_fact():
    fact = {
        "subject": "Acme Logistics",
        "predicate": "revenue",
        "value": "₹2,500 crore",
        "evidence_quote": "Acme Logistics reported revenue of ₹2,500 crore in FY2024.",
        "fact_type": "financial_metric"
    }
    chunk_text = "Full section: Acme Logistics reported revenue of ₹2,500 crore in FY2024. Operating results were strong."
    is_valid, reason = FactValidator.validate_fact(fact, chunk_text)
    assert is_valid is True
    assert reason is None

def test_reject_meaningless_number_without_metric():
    fact = {
        "subject": "Unknown",
        "predicate": "number",
        "value": "4",
        "evidence_quote": "4 FY23",
        "fact_type": "other"
    }
    chunk_text = "Table appendix: 4 FY23 notes."
    is_valid, reason = FactValidator.validate_fact(fact, chunk_text)
    assert is_valid is False
    assert "Meaningless" in reason or "isolated" in reason

def test_reject_missing_evidence():
    fact = {
        "subject": "Acme Corp",
        "predicate": "revenue",
        "value": "$100M",
        "evidence_quote": "",
        "fact_type": "financial_metric"
    }
    is_valid, reason = FactValidator.validate_fact(fact)
    assert is_valid is False
    assert "Missing evidence" in reason
