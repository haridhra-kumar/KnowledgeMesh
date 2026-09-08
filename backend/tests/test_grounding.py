import pytest
from app.services.grounding import EvidenceGrounder, normalize_text_for_grounding

def test_normalize_text_for_grounding():
    raw = '“Acme Logistics” reported revenue — of  ₹2,500 crore.'
    norm = normalize_text_for_grounding(raw)
    assert '"Acme Logistics"' in norm
    assert '-' in norm
    assert '  ' not in norm

def test_grounding_exact_match():
    grounder = EvidenceGrounder()
    page_text = "Management Discussion: Acme Logistics reported revenue of ₹2,500 crore in FY2024. Growth was 15%."
    quote = "Acme Logistics reported revenue of ₹2,500 crore in FY2024."
    res = grounder.ground_evidence(quote, page_text)
    assert res["grounding_status"] == "VERIFIED"
    assert res["grounding_score"] == 1.0
    assert "Acme Logistics reported revenue" in res["matched_snippet"]

def test_grounding_fuzzy_match():
    grounder = EvidenceGrounder()
    # Source page has slightly different spacing and hyphenation
    page_text = "Acme  Logistics reported  revenue of ₹2,500  crore in FY-2024."
    quote = "Acme Logistics reported revenue of ₹2,500 crore in FY2024."
    res = grounder.ground_evidence(quote, page_text)
    assert res["grounding_status"] in ["VERIFIED", "PARTIAL"]
    assert res["grounding_score"] >= 0.80

def test_grounding_unverified_unsupported_quote():
    grounder = EvidenceGrounder()
    page_text = "This document describes standard procedural guidelines and employee policies."
    quote = "Delhivery revenue reached ₹10,000 crore in 2030."
    res = grounder.ground_evidence(quote, page_text)
    assert res["grounding_status"] == "UNVERIFIED"
    assert res["grounding_score"] < 0.60
