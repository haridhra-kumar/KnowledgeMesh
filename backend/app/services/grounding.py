import re
import difflib
from typing import Dict, Any, Tuple
from app.config import settings

def normalize_text_for_grounding(text: str) -> str:
    """Normalize unicode quotes, ligatures, spaces, and punctuation for reliable matching."""
    if not text:
        return ""
    # Standardize ligatures
    ligatures = {
        'ﬁ': 'fi', 'ﬂ': 'fl', 'ﬀ': 'ff', 'ﬃ': 'ffi', 'ﬄ': 'ffl',
        'ﬅ': 'ft', 'ﬆ': 'st'
    }
    for lig, rep in ligatures.items():
        text = text.replace(lig, rep)
    # Remove soft hyphens, zero-width spaces, byte order marks
    text = text.replace('\xad', '').replace('\u200b', '').replace('\ufeff', '')
    # Normalize spaces
    text = text.replace('\xa0', ' ').replace('\u2009', ' ').replace('\u202f', ' ')
    # Standardize quotes
    text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'").replace('`', "'")
    # Standardize dashes
    text = text.replace('—', '-').replace('–', '-').replace('−', '-')
    # Rejoin words broken across line breaks
    text = re.sub(r'(\b[a-zA-Z]{2,})[-]\s*\n\s*([a-zA-Z]{2,}\b)', r'\1\2', text)
    # Collapse multiple whitespaces / newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_for_comparison(text: str) -> str:
    """Further normalize for comparison: unify currency symbols, standardize spacing around punctuation."""
    t = text.lower()
    # Unify currency symbols to ₹
    t = re.sub(r'\b(?:rs\.?|inr)\b\.?\s*|[₹$€£]\s*', '₹', t)
    # Standardize percentage expressions
    t = re.sub(r'\bper\s+cent\b|\bpercent\b', '%', t)
    t = re.sub(r'(\d)\s+%', r'\1%', t)
    # Collapse whitespace
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

class EvidenceGrounder:
    """
    Grounds extracted facts against actual source page text.
    Implements multi-tier verification:
    1. Exact normalized substring match (Score: 1.0)
    2. Comparison-normalized exact match (currency, % formatting) (Score: 1.0)
    3. Contiguous token sequence match (Score: 1.0)
    4. Fast anchor-window fuzzy matching via difflib.SequenceMatcher
    5. Status assignment: VERIFIED (>= 0.85), PARTIAL (0.60-0.84), UNVERIFIED (< 0.60)
    """

    def __init__(
        self,
        verified_threshold: float = settings.grounding_verified_threshold,
        partial_threshold: float = settings.grounding_partial_threshold
    ):
        self.verified_threshold = verified_threshold
        self.partial_threshold = partial_threshold

    def ground_evidence(
        self,
        evidence_quote: str,
        page_text: str
    ) -> Dict[str, Any]:
        normalized_evidence = normalize_text_for_grounding(evidence_quote)
        normalized_page = normalize_text_for_grounding(page_text)

        if not normalized_evidence or not normalized_page:
            return {
                "grounding_status": "UNVERIFIED",
                "grounding_score": 0.0,
                "normalized_evidence": normalized_evidence,
                "matched_snippet": ""
            }

        norm_ev_lower = normalized_evidence.lower()
        norm_page_lower = normalized_page.lower()

        # Level 1a: Exact match (case-insensitive)
        if norm_ev_lower in norm_page_lower:
            start_pos = norm_page_lower.find(norm_ev_lower)
            matched_snippet = normalized_page[start_pos:start_pos + len(normalized_evidence)]
            return {
                "grounding_status": "VERIFIED",
                "grounding_score": 1.0,
                "normalized_evidence": normalized_evidence,
                "matched_snippet": matched_snippet
            }

        # Level 1b: Exact match under comparison normalization (currency / percent / spacing)
        comp_ev = normalize_for_comparison(norm_ev_lower)
        comp_page = normalize_for_comparison(norm_page_lower)

        if comp_ev in comp_page:
            return {
                "grounding_status": "VERIFIED",
                "grounding_score": 1.0,
                "normalized_evidence": normalized_evidence,
                "matched_snippet": normalized_evidence
            }

        # Level 2: Token sequence match (ignoring punctuation differences)
        ev_tokens = [w for w in re.findall(r'[a-z0-9%₹]+', comp_ev) if len(w) > 1]
        page_tokens = [w for w in re.findall(r'[a-z0-9%₹]+', comp_page) if len(w) > 1]

        if not ev_tokens or not page_tokens:
            return {
                "grounding_status": "UNVERIFIED",
                "grounding_score": 0.0,
                "normalized_evidence": normalized_evidence,
                "matched_snippet": ""
            }

        ev_token_str = " ".join(ev_tokens)
        page_token_str = " ".join(page_tokens)

        if ev_token_str in page_token_str:
            return {
                "grounding_status": "VERIFIED",
                "grounding_score": 1.0,
                "normalized_evidence": normalized_evidence,
                "matched_snippet": normalized_evidence
            }

        # Level 3: Fast anchor-based fuzzy matching
        page_words = norm_page_lower.split()
        window_size = len(norm_ev_lower.split())

        anchors = [w for w in ev_tokens if len(w) > 3 or any(c.isdigit() for c in w)]
        if not anchors:
            anchors = ev_tokens

        anchor_indices = []
        for idx, w in enumerate(page_words):
            w_clean = re.sub(r'^[^\w₹]+|[^\w₹]+$', '', w)
            if w_clean in anchors:
                anchor_indices.append(idx)

        if not anchor_indices:
            anchor_indices = list(range(0, len(page_words), max(1, window_size // 2)))

        candidate_starts = set()
        for ai in anchor_indices:
            start = max(0, ai - int(window_size * 0.8))
            candidate_starts.add(start)

        best_score = 0.0
        best_snippet = ""
        for start in sorted(candidate_starts)[:15]:
            end = min(len(page_words), start + int(window_size * 1.2) + 2)
            candidate_str = " ".join(page_words[start:end])
            ratio = difflib.SequenceMatcher(None, norm_ev_lower, candidate_str).ratio()
            if ratio > best_score:
                best_score = ratio
                best_snippet = candidate_str
                if best_score > 0.95:
                    break

        # Level 4: Token set overlap fallback
        ev_token_set = set(ev_tokens)
        page_token_set = set(page_tokens)
        token_overlap = len(ev_token_set.intersection(page_token_set)) / len(ev_token_set) if ev_token_set else 0.0

        if token_overlap > 0.80:
            blended_score = max(best_score, token_overlap * 0.95)
        elif token_overlap > 0.60:
            blended_score = max(best_score, token_overlap * 0.85)
        else:
            blended_score = best_score * token_overlap

        rounded_score = round(min(1.0, blended_score), 4)

        if rounded_score >= self.verified_threshold:
            status = "VERIFIED"
        elif rounded_score >= self.partial_threshold:
            status = "PARTIAL"
        else:
            status = "UNVERIFIED"

        return {
            "grounding_status": status,
            "grounding_score": rounded_score,
            "normalized_evidence": normalized_evidence,
            "matched_snippet": best_snippet
        }
