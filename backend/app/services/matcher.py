import re
import difflib
from typing import List, Dict, Any, Tuple, Optional, Set

# Non-informative words that must NEVER drive metric matching
METRIC_STOP_WORDS = {
    "increased", "decreased", "increasing", "decreasing", "grew", "growth",
    "declined", "reported", "reporting", "was", "were", "is", "are", "has", "have",
    "doubled", "tripled", "stood", "reaching", "reached", "total", "totaled",
    "rate", "value", "count", "number", "the", "a", "an", "of", "for", "in", "and",
    "by", "at", "to", "with", "from", "our", "their", "its", "as", "per", "on"
}

# Entity stop words that should not drive subject similarity
ENTITY_STOP_WORDS = {
    "the", "a", "an", "ltd", "limited", "inc", "corp", "corporation", "company",
    "group", "holdings", "technologies", "services", "our", "your", "its"
}

# Semantic metric families: facts in different families are mutually incompatible
METRIC_FAMILIES = {
    "REVENUE": {
        "revenue", "total revenue", "gross revenue", "turnover",
        "income from operations", "revenue from contracts with customers",
        "service revenue", "operating revenue", "revenue from services",
        "fy24 revenue from services", "q4 fy24 revenue from services"
    },
    "TAX_REVENUE": {
        "net tax revenue", "net tax revenues", "tax revenue", "tax revenues",
        "gross tax revenue", "direct tax", "indirect tax", "gst revenue",
        "non-tax revenue", "non-tax revenues"
    },
    "SECTORAL_SALES": {
        "passenger vehicle sales", "two-wheeler sales", "three-wheeler sales",
        "commercial vehicle sales", "tractor sales", "auto sales", "vehicle sales"
    },
    "PROFITABILITY": {
        "ebitda", "ebitda profitability", "operating profit", "operating ebitda",
        "operating income", "net profit", "pat", "profit after tax", "net income",
        "profit before tax", "pbt", "loss after tax"
    },
    "MARGINS": {
        "margin", "ebitda margin", "profit margin", "net profit margin",
        "operating margin", "pat margin"
    },
    "PER_SHARE": {
        "loss per share", "earnings per share", "eps", "diluted eps",
        "basic eps", "book value per share"
    },
    "VOLUMES_OPERATIONAL": {
        "express parcels shipped", "parcel volume", "express parcel volume",
        "part truckload tonnage", "truckload tonnage", "tonnage", "shipments",
        "freight volume", "delivery network", "active customers"
    },
    "WORKING_CAPITAL": {
        "nwc days", "net working capital days", "working capital", "cash conversion cycle"
    },
    "MACRO_GDP": {
        "gdp", "real gdp", "gdp growth", "real gdp growth", "economic growth", "gross domestic product", "gross domestic product (gdp) growth"
    },
    "MACRO_INFLATION": {
        "inflation", "cpi inflation", "headline inflation", "core inflation", "consumer price index", "cpi", "retail inflation"
    },
    "MACRO_FISCAL": {
        "fiscal deficit", "gross fiscal deficit", "revenue deficit", "primary deficit"
    },
    "MACRO_POLICY_RATE": {
        "repo rate", "policy repo rate", "policy rate", "reverse repo rate", "standing deposit facility"
    },
    "MACRO_EXTERNAL": {
        "current account deficit", "cad", "forex reserves", "foreign exchange reserves", "trade deficit"
    },
    "SPECIFICATION_PRESSURE": {
        "pump pressure", "operating pressure", "bar pressure", "pressure"
    },
    "SPECIFICATION_CAPACITY": {
        "water tank capacity", "tank capacity", "bean hopper capacity", "capacity"
    },
    "SPECIFICATION_POWER": {
        "power consumption", "wattage", "rated power", "power"
    }
}

def clean_predicate_tokens(predicate: str) -> Set[str]:
    """Extract meaningful, non-generic tokens from a metric predicate."""
    tokens = re.findall(r'\b[a-zA-Z]{2,}\b', predicate.lower())
    return {t for t in tokens if t not in METRIC_STOP_WORDS}

def clean_subject_tokens(subject: str) -> Set[str]:
    """Extract entity tokens, removing legal designations and pronouns."""
    tokens = re.findall(r'\b[a-zA-Z]{2,}\b', subject.lower())
    return {t for t in tokens if t not in ENTITY_STOP_WORDS}

def get_metric_family(predicate: str) -> Optional[str]:
    """Identify which predefined semantic family a metric belongs to, if any."""
    p_clean = predicate.lower().strip()
    # Check specific compound families first
    for family_name in ["SECTORAL_SALES", "TAX_REVENUE"]:
        if any(m in p_clean or re.search(rf'\b{re.escape(m)}\b', p_clean) for m in METRIC_FAMILIES[family_name]):
            return family_name

    for family_name, members in METRIC_FAMILIES.items():
        if family_name in ["SECTORAL_SALES", "TAX_REVENUE"]:
            continue
        if any(m == p_clean or re.search(rf'\b{re.escape(m)}\b', p_clean) for m in members):
            return family_name
    return None

def calculate_predicate_similarity(pred_a: str, pred_b: str) -> float:
    """
    Compute semantic metric similarity.
    Enforces strict rules:
    - If predicates belong to different explicit metric families -> 0.0
    - If predicates belong to the same explicit metric family -> check for modifier conflicts, then 1.0
    - Generic verbs (increased/decreased) have ZERO weight.
    - Remaining core tokens must genuinely overlap.
    """
    fam_a = get_metric_family(pred_a)
    fam_b = get_metric_family(pred_b)

    # If both belong to known families:
    if fam_a and fam_b:
        if fam_a == fam_b:
            tokens_a = clean_predicate_tokens(pred_a)
            tokens_b = clean_predicate_tokens(pred_b)
            conflicts = [
                ({"tax", "taxes"}, {"service", "services", "contracts", "operations"}),
                ({"passenger", "vehicle", "wheeler", "auto"}, {"corporate", "total", "contracts", "services"}),
                ({"headline"}, {"core"}),
                ({"gross"}, {"net"}),
                ({"direct"}, {"indirect"})
            ]
            for set1, set2 in conflicts:
                if (tokens_a.intersection(set1) and tokens_b.intersection(set2)) or \
                   (tokens_a.intersection(set2) and tokens_b.intersection(set1)):
                    return 0.0
            return 1.0
        else:
            # Different families (e.g. PER_SHARE vs VOLUMES_OPERATIONAL) cannot match
            return 0.0

    # Clean tokens after stripping generic verbs and stop words
    tokens_a = clean_predicate_tokens(pred_a)
    tokens_b = clean_predicate_tokens(pred_b)

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    if not intersection:
        return 0.0

    jaccard = len(intersection) / len(tokens_a.union(tokens_b))
    seq_ratio = difflib.SequenceMatcher(None, " ".join(sorted(tokens_a)), " ".join(sorted(tokens_b))).ratio()
    return max(jaccard, seq_ratio)

def calculate_subject_similarity(subj_a: str, subj_b: str) -> float:
    """
    Compute similarity between subjects/entities.
    Requires true entity overlap (e.g. 'Delhivery' in 'Delhivery Limited').
    """
    a = subj_a.lower().strip()
    b = subj_b.lower().strip()
    if a == b:
        return 1.0

    tokens_a = clean_subject_tokens(subj_a)
    tokens_b = clean_subject_tokens(subj_b)

    if not tokens_a or not tokens_b:
        return 0.0

    # Direct token intersection of entity core
    intersection = tokens_a.intersection(tokens_b)
    if intersection:
        # High confidence if primary entity name matches (e.g. "delhivery")
        return len(intersection) / max(len(tokens_a), len(tokens_b))

    # Check substring containment (e.g. "delhivery" inside "delhivery logistics")
    if a in b or b in a:
        return 0.85

    seq_sim = difflib.SequenceMatcher(None, a, b).ratio()
    return seq_sim if seq_sim >= 0.80 else 0.0

class CandidateMatcher:
    """
    High-precision candidate matching layer.
    Prunes the N^2 comparison space so that only semantically compatible
    facts are compared.
    Ensures that generic words ('increased') and incompatible metrics
    ('loss per share' vs 'parcel volume') never generate candidate pairs.
    """

    def __init__(self, min_candidate_score: float = 0.70):
        self.min_candidate_score = min_candidate_score

    def find_candidates_for_fact(
        self,
        new_fact: Dict[str, Any],
        existing_facts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Compare a newly ingested fact against existing facts to produce candidate pairs.
        Only facts from different documents with high semantic compatibility qualify.
        """
        candidates = []
        fact_a_id = new_fact.get("id")
        doc_a_id = new_fact.get("document_id")

        for existing in existing_facts:
            fact_b_id = existing.get("id")
            doc_b_id = existing.get("document_id")

            # Must be from different documents
            if doc_a_id == doc_b_id:
                continue
            if fact_a_id == fact_b_id:
                continue

            match_score, match_reasons = self.evaluate_candidate_pair(new_fact, existing)
            if match_score >= self.min_candidate_score:
                reason_str = " + ".join(match_reasons)
                id_1, id_2 = sorted([fact_a_id, fact_b_id])
                candidates.append({
                    "fact_a_id": id_1,
                    "fact_b_id": id_2,
                    "match_score": round(match_score, 4),
                    "match_reason": reason_str
                })

        return candidates

    def evaluate_candidate_pair(
        self,
        fact_a: Dict[str, Any],
        fact_b: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """
        Evaluate if two facts qualify as candidate relationship pairs.
        Returns (composite_score, list_of_reasons).
        If metrics are incompatible, returns (0.0, []).
        """
        reasons = []

        # -------------------------------------------------------------
        # 1. Fact Type Compatibility
        # -------------------------------------------------------------
        type_a = fact_a.get("fact_type", "other")
        type_b = fact_b.get("fact_type", "other")
        # Incompatible domain types (e.g. device spec vs financial metric)
        if (type_a == "financial_metric" and type_b == "device_specification") or \
           (type_b == "financial_metric" and type_a == "device_specification"):
            return 0.0, []

        # -------------------------------------------------------------
        # 2. Subject Similarity (Entity alignment)
        # -------------------------------------------------------------
        subj_a = fact_a.get("subject", "")
        subj_b = fact_b.get("subject", "")
        subj_score = calculate_subject_similarity(subj_a, subj_b)
        if subj_score < 0.60:
            return 0.0, []
        reasons.append(f"subject alignment ('{subj_a}' ~ '{subj_b}')")

        # -------------------------------------------------------------
        # 3. Predicate / Metric Compatibility (Crucial)
        # -------------------------------------------------------------
        pred_a = fact_a.get("predicate", "")
        pred_b = fact_b.get("predicate", "")
        pred_score = calculate_predicate_similarity(pred_a, pred_b)
        if pred_score < 0.65:
            # Metrics are not in the same family and share no core concept
            return 0.0, []
        reasons.append(f"metric alignment ('{pred_a}' ~ '{pred_b}')")

        # -------------------------------------------------------------
        # 4. Period & Temporal Context
        # -------------------------------------------------------------
        period_a = fact_a.get("period")
        period_b = fact_b.get("period")
        period_score = 0.5
        if period_a and period_b:
            if period_a == period_b:
                period_score = 1.0
                reasons.append(f"identical period ({period_a})")
            elif any(y in period_a and y in period_b for y in ["2022", "2023", "2024", "2025", "2026"]):
                period_score = 0.8
                reasons.append(f"overlapping fiscal timeframe ({period_a} vs {period_b})")
            else:
                period_score = 0.6
                reasons.append(f"comparable reporting periods ({period_a} vs {period_b})")
        elif not period_a and not period_b:
            period_score = 0.7
            reasons.append("unspecified temporal context")
        else:
            period_score = 0.6

        # -------------------------------------------------------------
        # 5. Composite Score
        # -------------------------------------------------------------
        # Weighting: Predicate (50%), Subject (35%), Period (15%)
        composite = (pred_score * 0.50) + (subj_score * 0.35) + (period_score * 0.15)
        return composite, reasons
