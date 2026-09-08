import re
from typing import Dict, Any, Optional, Tuple

MULTIPLIERS = {
    "crore": 10_000_000.0,
    "crores": 10_000_000.0,
    "cr": 10_000_000.0,
    "lakh": 100_000.0,
    "lakhs": 100_000.0,
    "lac": 100_000.0,
    "lacs": 100_000.0,
    "billion": 1_000_000_000.0,
    "billions": 1_000_000_000.0,
    "bn": 1_000_000_000.0,
    "b": 1_000_000_000.0,
    "million": 1_000_000.0,
    "millions": 1_000_000.0,
    "mn": 1_000_000.0,
    "m": 1_000_000.0,
    "thousand": 1_000.0,
    "thousands": 1_000.0,
    "k": 1_000.0,
}

CURRENCY_SYMBOLS = {
    "₹": "INR",
    "rs": "INR",
    "rs.": "INR",
    "inr": "INR",
    "$": "USD",
    "usd": "USD",
    "€": "EUR",
    "eur": "EUR",
    "£": "GBP",
    "gbp": "GBP",
    "¥": "JPY",
    "jpy": "JPY",
}

TECHNICAL_UNITS = {
    "liter": "liters",
    "liters": "liters",
    "litre": "liters",
    "litres": "liters",
    "l": "liters",
    "bar": "bar",
    "bars": "bar",
    "psi": "psi",
    "watt": "watts",
    "watts": "watts",
    "w": "watts",
    "kw": "kilowatts",
    "kilowatt": "kilowatts",
    "kg": "kg",
    "kilogram": "kg",
    "kilograms": "kg",
    "g": "grams",
    "gram": "grams",
    "grams": "grams",
    "hz": "hz",
    "volt": "volts",
    "volts": "volts",
    "v": "volts",
    "%": "%",
    "percent": "%",
    "percentage": "%",
}

def normalize_period(period_str: Optional[str]) -> Optional[str]:
    """
    Standardize period representations:
    - 'FY24', 'FY 2024', 'Fiscal 2024' -> 'FY2024'
    - 'Q1 FY24', '1Q FY2024' -> 'Q1 FY2024'
    - '2024' -> 'CY2024'
    """
    if not period_str:
        return None

    clean = str(period_str).strip()

    # Quarter + FY: e.g. Q1 FY24, Q1 FY2024, 1Q FY24
    q_fy_match = re.search(r'(?:Q([1-4])|([1-4])Q)\s*(?:FY|Fiscal)?\s*(?:20)?(\d{2})', clean, re.IGNORECASE)
    if q_fy_match:
        quarter = q_fy_match.group(1) or q_fy_match.group(2)
        year_short = q_fy_match.group(3)
        year = f"20{year_short}" if len(year_short) == 2 else year_short
        return f"Q{quarter} FY{year}"

    # Year range without FY prefix: e.g. 2024-25, 2023-24
    yr_range = re.search(r'\b(20\d{2})-(\d{2})\b', clean)
    if yr_range:
        return f"FY20{yr_range.group(2)}"

    # Fiscal year: e.g. FY24, FY 2024, Fiscal 2024, FY 2023-24
    fy_match = re.search(r'(?:FY|Fiscal\s*Year|Fiscal)\s*(?:20)?(\d{2})(?:-(\d{2}))?', clean, re.IGNORECASE)
    if fy_match:
        y1 = fy_match.group(1)
        y2 = fy_match.group(2)
        if y2:
            return f"FY20{y2}"
        return f"FY20{y1}" if len(y1) == 2 else f"FY{y1}"

    # Calendar Year: e.g. 2024, CY2024
    cy_match = re.search(r'(?:CY\s*)?(20\d{2})', clean, re.IGNORECASE)
    if cy_match:
        return f"CY{cy_match.group(1)}"

    return clean

def normalize_value_and_unit(
    raw_value: str,
    raw_unit: Optional[str] = None,
    raw_currency: Optional[str] = None
) -> Tuple[Optional[float], Optional[str], Optional[str]]:
    """
    Parse numerical value, applying multiplier and standardizing unit & currency.
    Returns (normalized_value, normalized_unit, normalized_currency).
    """
    if not raw_value:
        return None, None, None

    text = str(raw_value).strip().lower()

    # Detect currency using symbols or whole words
    detected_currency = None
    if "₹" in text:
        detected_currency = "INR"
    elif "$" in text:
        detected_currency = "USD"
    elif "€" in text:
        detected_currency = "EUR"
    elif "£" in text:
        detected_currency = "GBP"
    elif "¥" in text:
        detected_currency = "JPY"
    else:
        for sym, curr in CURRENCY_SYMBOLS.items():
            if sym not in ["₹", "$", "€", "£", "¥"]:
                if re.search(rf'\b{re.escape(sym)}\b', text, re.IGNORECASE):
                    detected_currency = curr
                    break

    if not detected_currency and raw_currency:
        clean_curr = raw_currency.strip().upper()
        if clean_curr in ["INR", "USD", "EUR", "GBP", "JPY"]:
            detected_currency = clean_curr

    # Check for percentage
    if "%" in text or (raw_unit and "%" in raw_unit) or "percent" in text or "per cent" in text or (raw_unit and "per cent" in raw_unit):
        pct_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
        if pct_match:
            try:
                num = float(pct_match.group(1).replace(',', ''))
                return num, "%", None
            except ValueError:
                pass

    # Detect multiplier (support separated words "100 million" and attached suffixes "740Mn", "81,415Mn", "2.8Bn", "127Cr")
    multiplier = 1.0
    detected_multiplier_name = None
    for mult_name, factor in MULTIPLIERS.items():
        # Match as word boundary or preceded immediately by a digit
        if re.search(rf'(?:\b|(?<=\d)){re.escape(mult_name)}\b', text):
            multiplier = factor
            detected_multiplier_name = mult_name
            break

    # If multiplier wasn't in value text, check raw_unit
    if multiplier == 1.0 and raw_unit:
        unit_lower = raw_unit.strip().lower()
        if unit_lower in MULTIPLIERS:
            multiplier = MULTIPLIERS[unit_lower]
            detected_multiplier_name = unit_lower

    # Detect technical units
    detected_tech_unit = None
    for tech_k, tech_v in TECHNICAL_UNITS.items():
        if re.search(rf'\b{tech_k}\b', text) or (raw_unit and raw_unit.lower() == tech_k):
            detected_tech_unit = tech_v
            break

    # Extract base number
    num_match = re.search(r'([\d,]+(?:\.\d+)?)', text)
    if not num_match:
        return None, None, detected_currency

    try:
        base_num = float(num_match.group(1).replace(',', ''))
        normalized_num = base_num * multiplier

        if detected_currency:
            norm_unit = detected_currency
        elif detected_tech_unit:
            norm_unit = detected_tech_unit
        elif detected_multiplier_name:
            norm_unit = detected_multiplier_name
        elif raw_unit:
            norm_unit = raw_unit.strip()
        else:
            norm_unit = None

        return normalized_num, norm_unit, detected_currency
    except ValueError:
        return None, None, detected_currency

def normalize_fact_fields(fact_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply deterministic normalization to a validated fact dict.
    Adds 'normalized_value', 'normalized_unit', 'normalized_period'.
    """
    raw_val = fact_dict.get("value", "")
    raw_unit = fact_dict.get("unit")
    raw_currency = fact_dict.get("currency")
    raw_period = fact_dict.get("period")

    norm_val, norm_unit, norm_curr = normalize_value_and_unit(
        raw_val, raw_unit, raw_currency
    )
    norm_period = normalize_period(raw_period)

    updated = dict(fact_dict)
    updated["normalized_value"] = norm_val
    updated["normalized_unit"] = norm_unit
    if norm_curr and not updated.get("currency"):
        updated["currency"] = norm_curr
    if norm_period:
        updated["period"] = norm_period

    return updated
