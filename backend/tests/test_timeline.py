import pytest
from app.services.timeline import period_to_sort_key

def test_period_to_sort_key_chronological_order():
    key_2022 = period_to_sort_key("FY2022")
    key_2023 = period_to_sort_key("FY2023")
    key_q1_24 = period_to_sort_key("Q1 FY2024")
    key_fy24 = period_to_sort_key("FY2024")
    key_fy25 = period_to_sort_key("FY2025")

    # Chronology check: 2022 < 2023 < Q1 FY24 < FY24 < FY25
    assert key_2022 < key_2023
    assert key_2023 < key_q1_24
    assert key_q1_24 < key_fy24
    assert key_fy24 < key_fy25

def test_timeline_not_dependent_on_page_order():
    facts = [
        {"id": "f1", "page": 9, "period": "FY2023", "value": "₹80 Cr"},
        {"id": "f2", "page": 2, "period": "FY2024", "value": "₹100 Cr"},
        {"id": "f3", "page": 1, "period": "FY2025", "value": "₹120 Cr"}
    ]
    # Sort strictly by period key, not by page
    sorted_facts = sorted(facts, key=lambda x: period_to_sort_key(x["period"]))
    assert sorted_facts[0]["id"] == "f1"  # Page 9 is FY2023, so it comes first!
    assert sorted_facts[1]["id"] == "f2"  # Page 2 is FY2024
    assert sorted_facts[2]["id"] == "f3"  # Page 1 is FY2025
