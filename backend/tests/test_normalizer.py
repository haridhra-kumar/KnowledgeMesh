import pytest
from app.services.normalizer import (
    normalize_value_and_unit,
    normalize_period,
    normalize_fact_fields
)

def test_currency_scale_equivalence():
    # ₹1,000 crore
    val1, unit1, curr1 = normalize_value_and_unit("₹1,000 crore")
    # ₹10 billion
    val2, unit2, curr2 = normalize_value_and_unit("₹10 billion")

    assert val1 == 10_000_000_000.0
    assert val2 == 10_000_000_000.0
    assert val1 == val2
    assert unit1 == "INR"
    assert unit2 == "INR"

def test_usd_million():
    val, unit, curr = normalize_value_and_unit("$500 million")
    assert val == 500_000_000.0
    assert unit == "USD"
    assert curr == "USD"

def test_percentage_normalization():
    val, unit, curr = normalize_value_and_unit("14.5%")
    assert val == 14.5
    assert unit == "%"
    assert curr is None

def test_technical_units():
    val1, unit1, _ = normalize_value_and_unit("1.8 liters")
    assert val1 == 1.8
    assert unit1 == "liters"

    val2, unit2, _ = normalize_value_and_unit("15 bar")
    assert val2 == 15.0
    assert unit2 == "bar"

def test_period_normalization():
    assert normalize_period("FY24") == "FY2024"
    assert normalize_period("FY 2024") == "FY2024"
    assert normalize_period("Fiscal 2024") == "FY2024"
    assert normalize_period("Q1 FY24") == "Q1 FY2024"
    assert normalize_period("2024") == "CY2024"
