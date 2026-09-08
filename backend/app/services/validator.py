import re
from typing import Dict, Any, Tuple, Optional

# Generic words, verbs, pronouns, and prepositions that MUST NOT appear as standalone subjects, predicates, or values
GENERIC_WORDS = {
    "increased", "decreased", "increasing", "decreasing", "grew", "growth",
    "declined", "reported", "reporting", "was", "were", "is", "are", "has", "have", "had",
    "been", "being", "doubled", "tripled", "improved", "improving", "stood", "reaching",
    "and", "or", "the", "this", "that", "these", "those", "it", "its", "we", "our", "us",
    "their", "they", "them", "you", "your", "he", "she", "his", "her", "but", "then",
    "which", "who", "whom", "whose", "where", "when", "why", "how", "all", "any", "some",
    "few", "more", "most", "other", "into", "from", "for", "with", "by", "at", "to", "on",
    "as", "of", "in", "about", "above", "below", "between", "under", "over", "such", "an", "a"
}

# Verbs that are invalid as standalone predicates unless accompanied by a metric noun
STANDALONE_VERB_PREDICATES = {
    "increased", "decreased", "grew", "doubled", "tripled", "declined", "was", "were",
    "is", "are", "reported", "stood", "improved", "reached", "totaled", "stood at",
    "was reported", "has increased", "has decreased", "is growing", "growing"
}

# Lone number patterns (e.g., footnotes, page headers, isolated table cells without metric)
LONE_NUMBER_PATTERNS = [
    r'^\d+$',                      # Just digits: "4", "23"
    r'^\d+\s*FY\s*\d{2,4}$',       # "4 FY23" without metric
    r'^page\s*\d+$',               # "Page 12"
    r'^[ivxlcdm]+$',               # Roman numerals: "iv", "ix"
    r'^[#*•\-\.]+\s*\d+$',         # Bullet plus digit: "• 4"
    r'^note\s*\d+$',               # "Note 4"
    r'^[,\.\-\s]+$',               # Pure punctuation
]

# Common fragment suffixes that indicate truncated text
FRAGMENT_ENDINGS = (
    " and", " or", " by", " to", " of", " in", " for", " with",
    " driven by", " as of", " due to", " over", " under", " from",
    " that", " which", " including", " such as"
)

# Fragment prefixes that indicate truncated text
FRAGMENT_PREFIXES = (
    "in fiscal ", "for the ", "and ", "or ", "but ", "then ", "which ",
    "as the ", "our ", "we ", "to "
)

def is_meaningless_number(text: str) -> bool:
    clean = text.strip()
    for pattern in LONE_NUMBER_PATTERNS:
        if re.match(pattern, clean, re.IGNORECASE):
            return True
    return False

class FactValidator:
    """
    Strong semantic validation gate for KnowledgeMesh.
    Enforces that every fact represents a meaningful, self-contained,
    interpretable factual claim before entering grounding, matching,
    or relationship generation.
    """

    @staticmethod
    def validate_fact(raw_fact: Dict[str, Any], chunk_text: str = "") -> Tuple[bool, Optional[str]]:
        """
        Validates raw fact dictionary.
        Returns (is_valid: bool, rejection_reason: Optional[str]).
        """
        if not isinstance(raw_fact, dict):
            return False, "Fact is not a valid dictionary object"

        subject = str(raw_fact.get("subject") or "").strip()
        predicate = str(raw_fact.get("predicate") or "").strip()
        value = str(raw_fact.get("value") or "").strip()
        evidence = str(raw_fact.get("evidence_quote") or "").strip()

        # -------------------------------------------------------------
        # 1. Structural Completeness
        # -------------------------------------------------------------
        if not subject:
            return False, "Missing subject / entity"
        if len(subject) < 2:
            return False, f"Subject is too short or ambiguous: '{subject}'"

        if not predicate:
            return False, "Missing predicate / metric"
        if len(predicate) < 2:
            return False, f"Predicate is too short or ambiguous: '{predicate}'"

        if not value:
            return False, "Missing fact value"

        # Check for meaningless numbers early
        if is_meaningless_number(value):
            return False, f"Meaningless number: value '{value}' is an isolated digit or footnote marker without an associated metric"

        if not evidence:
            return False, "Missing evidence quote"
        if len(evidence) < 15:
            return False, f"Evidence quote is too brief to substantiate a claim: '{evidence}'"

        subj_lower = subject.lower().strip()
        pred_lower = predicate.lower().strip()
        val_lower = value.lower().strip()

        # -------------------------------------------------------------
        # 2. Subject Semantic Validation
        # -------------------------------------------------------------
        # Check against generic word blacklist
        if subj_lower in GENERIC_WORDS:
            return False, f"Subject '{subject}' is a generic verb, pronoun, or preposition, not an entity"

        # Check for broken sentence fragments
        if subject[0].islower():
            if subj_lower in ["delhivery", "india", "rbi", "imf", "delonghi"] or subject.startswith(("e-", "i-")):
                subject = subject[0].upper() + subject[1:]
                raw_fact["subject"] = subject
                subj_lower = subject.lower().strip()
            else:
                return False, f"Subject '{subject}' starts with a lowercase letter, indicating an arbitrary sentence fragment"

        for ending in FRAGMENT_ENDINGS:
            if subj_lower.endswith(ending):
                return False, f"Subject '{subject}' ends with dangling connector '{ending.strip()}', indicating a broken fragment"

        for prefix in FRAGMENT_PREFIXES:
            if subj_lower.startswith(prefix):
                return False, f"Subject '{subject}' begins with clause connector '{prefix.strip()}', indicating a broken fragment"

        # Subject cannot be purely punctuation or numbers
        if re.match(r'^[0-9\W_]+$', subject):
            return False, f"Subject '{subject}' contains no valid entity characters"

        # -------------------------------------------------------------
        # 3. Predicate Semantic Validation
        # -------------------------------------------------------------
        # Predicate cannot be a standalone generic verb or conjunction
        if pred_lower in STANDALONE_VERB_PREDICATES or pred_lower in GENERIC_WORDS:
            return False, f"Predicate '{predicate}' is a generic verb or word without an associated metric name"

        if pred_lower in [",", ".", "-", ";", "/", "\\", "&", "+"]:
            return False, f"Predicate '{predicate}' is a punctuation artifact"

        # Predicate cannot be purely numbers or a fiscal year
        if re.match(r'^\d+$', predicate) or re.match(r'^(?:(?:FY|CY|Q[1-4])\s*\d{2,4}[\s,/–-]*)+$', predicate, re.IGNORECASE):
            return False, f"Predicate '{predicate}' is purely a number or period, not a metric"

        # -------------------------------------------------------------
        # 4. Value Semantic Validation
        # -------------------------------------------------------------
        if is_meaningless_number(value):
            return False, f"Value '{value}' is an isolated digit or footnote marker with no associated metric"

        if val_lower in GENERIC_WORDS or val_lower in STANDALONE_VERB_PREDICATES:
            return False, f"Value '{value}' is a generic action word rather than a metric quantity or state"

        if val_lower in [",", ".", "-", ";", ":"]:
            return False, f"Value '{value}' is purely punctuation"

        # -------------------------------------------------------------
        # 5. Semantic Coherence (Subject != Predicate != Value)
        # -------------------------------------------------------------
        if subj_lower == pred_lower:
            return False, f"Subject and predicate are identical ('{subject}'), which does not form a meaningful claim"

        if pred_lower == val_lower and pred_lower not in ["true", "false", "yes", "no"]:
            return False, f"Predicate and value are identical ('{predicate}'), indicating a redundant extraction fragment"

        # -------------------------------------------------------------
        # 6. Quality Score Gate
        # -------------------------------------------------------------
        quality_score = FactValidator.calculate_fact_quality(raw_fact)
        raw_fact["quality_score"] = quality_score
        if quality_score < 0.60:
            return False, f"Fact quality score {quality_score:.2f} is below minimum threshold (0.60)"

        # -------------------------------------------------------------
        # 7. Source Chunk Text Containment Check
        # -------------------------------------------------------------
        if chunk_text:
            clean_chunk = " ".join(chunk_text.lower().split())
            clean_evidence = " ".join(evidence.lower().split())
            ev_words = [w for w in re.findall(r'\w+', clean_evidence) if len(w) > 2]
            if ev_words:
                matching_words = sum(1 for w in ev_words if w in clean_chunk)
                match_ratio = matching_words / len(ev_words)
                if match_ratio < 0.35:
                    return False, "Evidence quote does not sufficiently overlap with source chunk text"

        return True, None

    @staticmethod
    def calculate_fact_quality(fact: Dict[str, Any]) -> float:
        """
        Calculate an internal fact quality score between 0.0 and 1.0.
        Evaluates subject specificity, metric clarity, value structure,
        and evidence completeness.
        """
        subject = str(fact.get("subject") or "").strip()
        predicate = str(fact.get("predicate") or "").strip()
        value = str(fact.get("value") or "").strip()
        evidence = str(fact.get("evidence_quote") or "").strip()
        period = fact.get("period")
        unit = fact.get("unit")
        currency = fact.get("currency")

        # 1. Subject Quality (0.0 to 1.0)
        subj_q = 0.5
        if subject and subject[0].isupper() and len(subject) >= 3:
            subj_q = 0.85
            # Bonus for named entity patterns (e.g. Acme Corp, Delhivery Limited)
            if any(term in subject.lower() for term in ["corp", "inc", "ltd", "limited", "delhivery", "acme", "technologies", "services", "company"]):
                subj_q = 1.0
        if subject.lower() in GENERIC_WORDS or subject[0].islower() if subject else True:
            subj_q = 0.0

        # 2. Predicate Quality (0.0 to 1.0)
        pred_q = 0.5
        metric_keywords = [
            "revenue", "profit", "ebitda", "margin", "income", "sales", "loss",
            "volume", "shipment", "capacity", "pressure", "power", "wattage",
            "retention", "headcount", "employees", "capital", "days", "growth",
            "turnover", "debt", "pat", "eps", "expenditure", "cost",
            "gdp", "inflation", "cpi", "deficit", "repo", "reserves", "rate",
            "export", "import", "trade", "tax", "cad", "receipts", "payments", "production"
        ]
        if any(kw in predicate.lower() for kw in metric_keywords):
            pred_q = 1.0
        elif predicate.lower() in STANDALONE_VERB_PREDICATES:
            pred_q = 0.0
        elif len(predicate) >= 4:
            pred_q = 0.7

        # 3. Value Quality (0.0 to 1.0)
        val_q = 0.5
        has_number = bool(re.search(r'\d', value))
        if has_number:
            if unit or currency or any(c in value for c in ["₹", "$", "€", "£", "%"]):
                val_q = 1.0
            elif len(value.strip()) > 1 and not is_meaningless_number(value):
                val_q = 0.75
            else:
                val_q = 0.2
        elif value.lower() in GENERIC_WORDS:
            val_q = 0.0
        else:
            val_q = 0.6  # Semantic text claim

        # 4. Context Quality (Period / Scope / Unit)
        ctx_q = 0.5
        if period:
            ctx_q += 0.3
        if unit or currency:
            ctx_q += 0.2
        ctx_q = min(1.0, ctx_q)

        # 5. Evidence Completeness
        ev_q = 0.5
        if len(evidence) >= 40:
            ev_q = 1.0
        elif len(evidence) >= 25:
            ev_q = 0.8
        else:
            ev_q = 0.3

        # Weighted blend
        composite = (
            subj_q * 0.30 +
            pred_q * 0.30 +
            val_q * 0.20 +
            ctx_q * 0.10 +
            ev_q * 0.10
        )
        return round(max(0.0, min(1.0, composite)), 3)
