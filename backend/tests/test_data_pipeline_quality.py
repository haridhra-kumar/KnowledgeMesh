import pytest
from app.services.extractor import FactExtractor
from app.services.validator import FactValidator
from app.services.matcher import CandidateMatcher
from app.services.relationship_engine import RelationshipEngine

@pytest.fixture
def extractor():
    # Force heuristic path for deterministic offline test verification
    ext = FactExtractor()
    ext.client = None
    return ext

@pytest.fixture
def matcher():
    return CandidateMatcher(min_candidate_score=0.70)

@pytest.fixture
def rel_engine():
    re = RelationshipEngine()
    re.client = None
    return re

def test_1_revenue_increased_extraction(extractor):
    """
    TEST 1:
    Input: 'Revenue increased to ₹100 crore in FY2024.'
    Expected:
    - subject: Company or valid entity (NOT 'increased')
    - predicate: 'revenue' (NOT 'increased')
    - value: '₹100 crore' (NOT 'increased')
    - period: 'FY2024'
    """
    text = "Revenue increased to ₹100 crore in FY2024."
    res = extractor._heuristic_extract(text, 1)
    assert len(res) > 0, "Should extract at least one financial fact"
    fact = res[0]

    assert fact["subject"].lower() != "increased", f"Subject must not be 'increased', got '{fact['subject']}'"
    assert fact["predicate"].lower() == "revenue", f"Predicate must be 'revenue', got '{fact['predicate']}'"
    assert fact["predicate"].lower() != "increased", "Predicate must not be generic verb 'increased'"
    assert "100" in fact["value"] and "crore" in fact["value"].lower(), f"Value must contain ₹100 crore, got '{fact['value']}'"
    assert fact["value"].lower() != "increased", "Value must not be 'increased'"
    assert fact["period"] in ["FY2024", "FY24"], f"Expected FY2024, got '{fact['period']}'"

    # Must pass semantic validation
    is_valid, reason = FactValidator.validate_fact(fact, text)
    assert is_valid is True, f"Valid claim failed validation: {reason}"

def test_2_parcel_volume_extraction(extractor):
    """
    TEST 2:
    Input: 'Parcel volume increased to 3.29 million.'
    Expected:
    - predicate / metric: 'parcel volume' (NOT 'increased')
    - value: '3.29 million' (NOT 'increased')
    """
    text = "Delhivery parcel volume increased to 3.29 million."
    res = extractor._heuristic_extract(text, 1)
    assert len(res) > 0, "Should extract operational volume fact"
    fact = res[0]

    assert "parcel volume" in fact["predicate"].lower(), f"Expected 'parcel volume', got '{fact['predicate']}'"
    assert fact["predicate"].lower() != "increased", "Predicate must not be 'increased'"
    assert "3.29" in fact["value"] and "million" in fact["value"].lower(), f"Expected '3.29 million', got '{fact['value']}'"
    assert fact["value"].lower() != "increased", "Value must not be 'increased'"

    is_valid, reason = FactValidator.validate_fact(fact, text)
    assert is_valid is True, f"Valid claim failed validation: {reason}"

def test_3_loss_per_share_vs_parcel_volume_is_unrelated(matcher, rel_engine):
    """
    TEST 3:
    Loss per share vs Parcel volume
    Expected:
    - CandidateMatcher rejects candidate pair (score = 0.0)
    - RelationshipEngine classifies as UNRELATED
    """
    fact_a = {
        "id": "fact_lps_1",
        "document_id": "doc_1",
        "subject": "Delhivery",
        "predicate": "loss per share",
        "value": "₹14.09",
        "normalized_value": 14.09,
        "normalized_unit": "INR",
        "period": "FY2023",
        "evidence_quote": "Delhivery reported a loss per share of ₹14.09 in FY2023.",
        "fact_type": "financial_metric"
    }

    fact_b = {
        "id": "fact_vol_2",
        "document_id": "doc_2",
        "subject": "Delhivery",
        "predicate": "parcel volume",
        "value": "3.29 Mn",
        "normalized_value": 3290000.0,
        "normalized_unit": "parcels",
        "period": "FY2019",
        "evidence_quote": "Delhivery handled a parcel volume of 3.29 Mn in FY2019.",
        "fact_type": "numerical_metric"
    }

    score, reasons = matcher.evaluate_candidate_pair(fact_a, fact_b)
    assert score == 0.0, f"CandidateMatcher must reject incompatible metrics, got score: {score}"

    rel = rel_engine.evaluate_relationship(fact_a, fact_b)
    assert rel["type"] == "UNRELATED", f"Expected 'UNRELATED', got '{rel['type']}'"

def test_4_revenue_corroboration(rel_engine):
    """
    TEST 4:
    Revenue FY2024 ₹100 Cr vs Revenue FY2024 ₹100 Cr
    Expected: CORROBORATE
    """
    fact_a = {
        "id": "fact_rev_a",
        "document_id": "doc_1",
        "document_filename": "Annual_Report_FY24.pdf",
        "subject": "Delhivery",
        "predicate": "revenue",
        "value": "₹100 crore",
        "normalized_value": 1000000000.0,
        "normalized_unit": "INR",
        "period": "FY2024",
        "scope": "consolidated",
        "evidence_quote": "Delhivery generated revenue of ₹100 crore in FY2024.",
        "quality_score": 0.95,
        "grounding_score": 0.95
    }

    fact_b = {
        "id": "fact_rev_b",
        "document_id": "doc_2",
        "document_filename": "Investor_Presentation_FY24.pdf",
        "subject": "Delhivery",
        "predicate": "revenue",
        "value": "₹100 Cr",
        "normalized_value": 1000000000.0,
        "normalized_unit": "INR",
        "period": "FY2024",
        "scope": "consolidated",
        "evidence_quote": "Total revenue for FY2024 stood at ₹100 Cr.",
        "quality_score": 0.95,
        "grounding_score": 0.95
    }

    rel = rel_engine.evaluate_relationship(fact_a, fact_b)
    assert rel["type"] == "CORROBORATE", f"Expected 'CORROBORATE', got '{rel['type']}'"
    assert rel["confidence"] >= 0.85, f"Expected high confidence for corroboration, got {rel['confidence']}"

def test_5_revenue_contradiction(rel_engine):
    """
    TEST 5:
    Revenue FY2024 ₹100 Cr vs Revenue FY2024 ₹150 Cr (same period, same scope)
    Expected: CONTRADICT
    """
    fact_a = {
        "id": "fact_rev_100",
        "document_id": "doc_1",
        "document_filename": "Official_Filing.pdf",
        "subject": "Delhivery",
        "predicate": "revenue",
        "value": "₹100 crore",
        "normalized_value": 1000000000.0,
        "normalized_unit": "INR",
        "period": "FY2024",
        "scope": "consolidated",
        "evidence_quote": "Consolidated revenue was ₹100 crore in FY2024.",
        "quality_score": 0.95,
        "grounding_score": 0.95
    }

    fact_b = {
        "id": "fact_rev_150",
        "document_id": "doc_3",
        "document_filename": "Press_Release.pdf",
        "subject": "Delhivery",
        "predicate": "revenue",
        "value": "₹150 crore",
        "normalized_value": 1500000000.0,
        "normalized_unit": "INR",
        "period": "FY2024",
        "scope": "consolidated",
        "evidence_quote": "Consolidated revenue stood at ₹150 crore in FY2024.",
        "quality_score": 0.95,
        "grounding_score": 0.95
    }

    rel = rel_engine.evaluate_relationship(fact_a, fact_b)
    assert rel["type"] == "CONTRADICT", f"Expected 'CONTRADICT', got '{rel['type']}'"
    assert rel["confidence"] >= 0.80, f"Expected high confidence for genuine contradiction, got {rel['confidence']}"

def test_6_revenue_reconciliation(rel_engine):
    """
    TEST 6:
    Revenue FY2024 ₹100 Cr vs Revenue FY2025 ₹150 Cr (different fiscal years)
    Expected: RECONCILE
    """
    fact_a = {
        "id": "fact_rev_2024",
        "document_id": "doc_1",
        "document_filename": "Report_FY24.pdf",
        "subject": "Delhivery",
        "predicate": "revenue",
        "value": "₹100 crore",
        "normalized_value": 1000000000.0,
        "normalized_unit": "INR",
        "period": "FY2024",
        "scope": "consolidated",
        "evidence_quote": "Delhivery revenue in FY2024 reached ₹100 crore.",
        "quality_score": 0.95,
        "grounding_score": 0.95
    }

    fact_b = {
        "id": "fact_rev_2025",
        "document_id": "doc_2",
        "document_filename": "Report_FY25.pdf",
        "subject": "Delhivery",
        "predicate": "revenue",
        "value": "₹150 crore",
        "normalized_value": 1500000000.0,
        "normalized_unit": "INR",
        "period": "FY2025",
        "scope": "consolidated",
        "evidence_quote": "Delhivery revenue in FY2025 grew to ₹150 crore.",
        "quality_score": 0.95,
        "grounding_score": 0.95
    }

    rel = rel_engine.evaluate_relationship(fact_a, fact_b)
    assert rel["type"] == "RECONCILE", f"Expected 'RECONCILE', got '{rel['type']}'"
    assert "different" in rel["reasoning"].lower() or "period" in rel["reasoning"].lower()

def test_7_lone_number_rejected():
    """
    TEST 7:
    '4 FY23' or ungrounded lone digit
    Expected: Rejected by FactValidator or scored as low quality
    """
    bad_fact_1 = {
        "subject": "Delhivery",
        "predicate": "FY24 highlights",
        "value": "4",
        "period": "FY24",
        "evidence_quote": "Delhivery FY24 highlights 4"
    }

    is_valid, reason = FactValidator.validate_fact(bad_fact_1)
    assert is_valid is False, "Lone number '4' must be rejected"
    assert "isolated digit" in reason.lower() or "meaningless" in reason.lower()

    bad_fact_2 = {
        "subject": "increased",
        "predicate": "increased",
        "value": "increased",
        "evidence_quote": "We increased our capacity."
    }
    is_valid_2, reason_2 = FactValidator.validate_fact(bad_fact_2)
    assert is_valid_2 is False, "Generic verb fact must be rejected"

    bad_fact_3 = {
        "subject": "ctor is growing at a rapid pace driven by",
        "predicate": "growth",
        "value": "growing",
        "evidence_quote": "Sector is growing at a rapid pace driven by..."
    }
    is_valid_3, reason_3 = FactValidator.validate_fact(bad_fact_3)
    assert is_valid_3 is False, "Sentence fragment subject must be rejected"
