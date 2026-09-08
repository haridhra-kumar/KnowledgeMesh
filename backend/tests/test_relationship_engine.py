import pytest
from app.services.relationship_engine import RelationshipEngine, canonical_relationship_key

def test_canonical_key_symmetry():
    key1 = canonical_relationship_key("fact-abc", "fact-xyz")
    key2 = canonical_relationship_key("fact-xyz", "fact-abc")
    assert key1 == key2
    assert key1 == "fact-abc__fact-xyz"

def test_corroboration_evaluation():
    engine = RelationshipEngine()
    fact_a = {
        "id": "fa1",
        "subject": "Acme Logistics",
        "predicate": "revenue",
        "value": "₹2,500 crore",
        "normalized_value": 25_000_000_000.0,
        "normalized_unit": "INR",
        "period": "FY2024",
        "scope": None,
        "document_filename": "Annual Report.pdf",
        "page_number": 1,
        "grounding_score": 1.0,
        "evidence_quote": "Revenue for FY2024 was ₹2,500 crore."
    }
    fact_b = {
        "id": "fb1",
        "subject": "Acme Logistics",
        "predicate": "revenue",
        "value": "₹2,500 crore",
        "normalized_value": 25_000_000_000.0,
        "normalized_unit": "INR",
        "period": "FY2024",
        "scope": None,
        "document_filename": "Investor Presentation.pdf",
        "page_number": 1,
        "grounding_score": 1.0,
        "evidence_quote": "In FY2024, Acme Logistics recorded revenue of ₹2,500 crore."
    }
    rel = engine.evaluate_relationship(fact_a, fact_b)
    assert rel["type"] == "CORROBORATE"
    assert rel["confidence"] > 0.8
    assert "substantiate" in rel["reasoning"] or "corroborat" in rel["reasoning"]

def test_contradiction_evaluation():
    engine = RelationshipEngine()
    fact_a = {
        "id": "fa1",
        "subject": "Acme Logistics",
        "predicate": "revenue",
        "value": "₹2,500 crore",
        "normalized_value": 25_000_000_000.0,
        "normalized_unit": "INR",
        "period": "FY2024",
        "scope": None,
        "document_filename": "Annual Report.pdf",
        "page_number": 1,
        "evidence_quote": "Acme Logistics reported revenue of ₹2,500 crore in FY2024."
    }
    fact_b = {
        "id": "fb2",
        "subject": "Acme Logistics",
        "predicate": "revenue",
        "value": "₹3,200 crore",
        "normalized_value": 32_000_000_000.0,
        "normalized_unit": "INR",
        "period": "FY2024",
        "scope": None,
        "document_filename": "Press Release.pdf",
        "page_number": 1,
        "evidence_quote": "Acme Logistics announced revenue of ₹3,200 crore in FY2024."
    }
    rel = engine.evaluate_relationship(fact_a, fact_b)
    assert rel["type"] == "CONTRADICT"
    assert "contradiction" in rel["reasoning"].lower() or "conflict" in rel["reasoning"].lower()

def test_reconciliation_different_periods():
    engine = RelationshipEngine()
    fact_a = {
        "id": "fa1",
        "subject": "Acme Logistics",
        "predicate": "revenue",
        "value": "₹2,500 crore",
        "normalized_value": 25_000_000_000.0,
        "normalized_unit": "INR",
        "period": "FY2024",
        "scope": None,
        "document_filename": "Annual Report.pdf",
        "page_number": 1,
        "evidence_quote": "Acme Logistics reported revenue of ₹2,500 crore in FY2024."
    }
    fact_b = {
        "id": "fb3",
        "subject": "Acme Logistics",
        "predicate": "revenue",
        "value": "₹650 crore",
        "normalized_value": 6_500_000_000.0,
        "normalized_unit": "INR",
        "period": "Q1 FY2024",
        "scope": None,
        "document_filename": "Quarterly Statement.pdf",
        "page_number": 1,
        "evidence_quote": "Acme Logistics recorded revenue of ₹650 crore in Q1 FY2024."
    }
    rel = engine.evaluate_relationship(fact_a, fact_b)
    assert rel["type"] == "RECONCILE"
    assert "period" in rel["reasoning"].lower() or "temporal" in rel["reasoning"].lower()
