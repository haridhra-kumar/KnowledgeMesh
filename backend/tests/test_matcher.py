import pytest
from app.services.matcher import CandidateMatcher

def test_candidate_matching_identifies_pair():
    matcher = CandidateMatcher(min_candidate_score=0.50)
    fact_a = {
        "id": "fact-1",
        "document_id": "doc-1",
        "subject": "Acme Logistics",
        "predicate": "revenue",
        "period": "FY2024"
    }
    existing_facts = [
        {
            "id": "fact-2",
            "document_id": "doc-2",
            "subject": "Acme Logistics Ltd",
            "predicate": "total revenue",
            "period": "FY2024"
        },
        {
            "id": "fact-3",
            "document_id": "doc-3",
            "subject": "Random Coffee Maker",
            "predicate": "water capacity",
            "period": None
        }
    ]

    candidates = matcher.find_candidates_for_fact(fact_a, existing_facts)
    assert len(candidates) == 1
    cand = candidates[0]
    assert "fact-1" in [cand["fact_a_id"], cand["fact_b_id"]]
    assert "fact-2" in [cand["fact_a_id"], cand["fact_b_id"]]
    assert "subject alignment" in cand["match_reason"]
    assert "metric alignment" in cand["match_reason"]
