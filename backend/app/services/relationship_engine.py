import os
import json
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.config import settings
from app.services.prompts import (
    RELATIONSHIP_REASONING_SYSTEM_PROMPT,
    RELATIONSHIP_REASONING_USER_PROMPT
)
from app.services.extractor import clean_json_response
from app.services.matcher import calculate_predicate_similarity, calculate_subject_similarity
from app.services.validator import GENERIC_WORDS, STANDALONE_VERB_PREDICATES

logger = logging.getLogger(__name__)

def canonical_relationship_key(fact_a_id: str, fact_b_id: str) -> str:
    """Generate deterministic canonical key regardless of argument order."""
    ids = sorted([str(fact_a_id), str(fact_b_id)])
    return f"{ids[0]}__{ids[1]}"

class RelationshipEngine:
    """
    Evaluates relationships between candidate facts.
    Categorizes into: CORROBORATE, CONTRADICT, RECONCILE, UNRELATED.
    Ensures that UNRELATED is a first-class result and that generic verbs
    or incompatible metrics never produce false corroborations.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.groq_api_key or os.environ.get("GROQ_API_KEY", "")
        self.model = model or settings.groq_model
        self.client = None
        self.llm_calls_remaining = settings.max_relationship_llm_calls
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key, timeout=settings.groq_timeout, max_retries=0)
            except Exception as e:
                logger.warning(f"Could not initialize Groq client for relationships: {e}")

    def evaluate_relationship(
        self,
        fact_a: Dict[str, Any],
        fact_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Determine relationship between two candidate facts.
        Uses deterministic semantic validation and Groq LLM reasoning when configured.
        """
        canonical_key = canonical_relationship_key(fact_a["id"], fact_b["id"])

        # Run deterministic evaluation first
        rule_result = self._rule_based_evaluate(fact_a, fact_b)

        # If rule result is already UNRELATED, don't bother calling LLM
        if rule_result["type"] == "UNRELATED":
            return rule_result

        # If Groq is available and we still have LLM budget, enhance with LLM reasoning
        if self.client and self.llm_calls_remaining > 0:
            try:
                doc_a_name = fact_a.get("document_filename") or "Document A"
                doc_b_name = fact_b.get("document_filename") or "Document B"

                prompt = RELATIONSHIP_REASONING_USER_PROMPT.format(
                    fact_a_subject=fact_a.get("subject", ""),
                    fact_a_predicate=fact_a.get("predicate", ""),
                    fact_a_value=fact_a.get("value", ""),
                    fact_a_norm_value=fact_a.get("normalized_value", "N/A"),
                    fact_a_norm_unit=fact_a.get("normalized_unit", "N/A"),
                    fact_a_period=fact_a.get("period", "Unspecified"),
                    fact_a_scope=fact_a.get("scope", "Unspecified"),
                    fact_a_unit=fact_a.get("unit", "N/A"),
                    fact_a_currency=fact_a.get("currency", "N/A"),
                    fact_a_doc=doc_a_name,
                    fact_a_page=fact_a.get("page_number", 1),
                    fact_a_evidence=fact_a.get("evidence_quote", ""),
                    fact_b_subject=fact_b.get("subject", ""),
                    fact_b_predicate=fact_b.get("predicate", ""),
                    fact_b_value=fact_b.get("value", ""),
                    fact_b_norm_value=fact_b.get("normalized_value", "N/A"),
                    fact_b_norm_unit=fact_b.get("normalized_unit", "N/A"),
                    fact_b_period=fact_b.get("period", "Unspecified"),
                    fact_b_scope=fact_b.get("scope", "Unspecified"),
                    fact_b_unit=fact_b.get("unit", "N/A"),
                    fact_b_currency=fact_b.get("currency", "N/A"),
                    fact_b_doc=doc_b_name,
                    fact_b_page=fact_b.get("page_number", 1),
                    fact_b_evidence=fact_b.get("evidence_quote", "")
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": RELATIONSHIP_REASONING_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=1000
                )
                raw_content = response.choices[0].message.content or "{}"
                self.llm_calls_remaining -= 1
                cleaned = clean_json_response(raw_content)
                parsed = json.loads(cleaned)

                rel_type = parsed.get("relationship_type", rule_result["type"]).upper()
                if rel_type not in ["CORROBORATE", "CONTRADICT", "RECONCILE", "UNRELATED"]:
                    rel_type = rule_result["type"]

                # If LLM classified as UNRELATED, respect it
                if rel_type == "UNRELATED":
                    return {
                        "id": str(uuid.uuid4()),
                        "fact_a_id": fact_a["id"],
                        "fact_b_id": fact_b["id"],
                        "canonical_key": canonical_key,
                        "type": "UNRELATED",
                        "reasoning": parsed.get("reasoning") or "The facts do not describe the same underlying claim or measurement context.",
                        "confidence": 0.50,
                        "comparison_context_json": {},
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }

                # Confidence should be scaled by rule-based fact quality
                llm_conf = float(parsed.get("confidence", 0.85))
                rule_conf = rule_result["confidence"]
                composite_conf = round(min(0.98, max(0.40, (llm_conf * 0.40) + (rule_conf * 0.60))), 3)

                reasoning = parsed.get("reasoning") or rule_result["reasoning"]
                context = parsed.get("comparison_context") or rule_result["comparison_context_json"]

                return {
                    "id": str(uuid.uuid4()),
                    "fact_a_id": fact_a["id"],
                    "fact_b_id": fact_b["id"],
                    "canonical_key": canonical_key,
                    "type": rel_type,
                    "reasoning": reasoning,
                    "confidence": composite_conf,
                    "comparison_context_json": context,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            except Exception as e:
                logger.warning(f"LLM relationship reasoning failed, using rule-based reasoning: {e}")
                err_str = str(e).lower()
                if any(k in err_str for k in ["connection", "timeout", "unauthorized", "api_key", "rate", "429", "limit"]):
                    self.client = None
                return rule_result

        return rule_result

    def _rule_based_evaluate(
        self,
        fact_a: Dict[str, Any],
        fact_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deterministic contextual relationship evaluation.
        Distinguishes:
        - UNRELATED: Incompatible metric, entity, or domain.
        - CORROBORATE: Same entity + same metric + same period/scope + matching values.
        - RECONCILE: Same entity + same metric + different period/scope/unit explaining the difference.
        - CONTRADICT: Same entity + same metric + same period + same scope + genuinely conflicting values.
        """
        canonical_key = canonical_relationship_key(fact_a["id"], fact_b["id"])

        subj_a = str(fact_a.get("subject") or "").strip()
        subj_b = str(fact_b.get("subject") or "").strip()
        pred_a = str(fact_a.get("predicate") or "").strip().lower()
        pred_b = str(fact_b.get("predicate") or "").strip().lower()

        val_a = str(fact_a.get("value") or "").strip()
        val_b = str(fact_b.get("value") or "").strip()
        norm_val_a = fact_a.get("normalized_value")
        norm_val_b = fact_b.get("normalized_value")
        norm_unit_a = fact_a.get("normalized_unit")
        norm_unit_b = fact_b.get("normalized_unit")

        period_a = fact_a.get("period")
        period_b = fact_b.get("period")
        scope_a = fact_a.get("scope")
        scope_b = fact_b.get("scope")

        doc_a_name = fact_a.get("document_filename") or "Document A"
        doc_b_name = fact_b.get("document_filename") or "Document B"

        # -------------------------------------------------------------
        # 1. Compatibility Check (Must be about the same concept)
        # -------------------------------------------------------------
        # Disallow standalone verbs
        if pred_a in STANDALONE_VERB_PREDICATES or pred_b in STANDALONE_VERB_PREDICATES or \
           val_a.lower() in GENERIC_WORDS or val_b.lower() in GENERIC_WORDS:
            return {
                "id": str(uuid.uuid4()),
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "canonical_key": canonical_key,
                "type": "UNRELATED",
                "reasoning": "Facts contain generic action verbs or non-metric attributes and cannot be compared.",
                "confidence": 0.20,
                "comparison_context_json": {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        pred_sim = calculate_predicate_similarity(pred_a, pred_b)
        if pred_sim < 0.65:
            return {
                "id": str(uuid.uuid4()),
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "canonical_key": canonical_key,
                "type": "UNRELATED",
                "reasoning": f"Metrics '{pred_a}' and '{pred_b}' represent distinct, incompatible categories.",
                "confidence": 0.30,
                "comparison_context_json": {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        subj_sim = calculate_subject_similarity(subj_a, subj_b)
        if subj_sim < 0.60:
            return {
                "id": str(uuid.uuid4()),
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "canonical_key": canonical_key,
                "type": "UNRELATED",
                "reasoning": f"Entities '{subj_a}' and '{subj_b}' do not refer to the same organization or subject.",
                "confidence": 0.30,
                "comparison_context_json": {},
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        # Quality scoring
        q_a = fact_a.get("quality_score", 0.85)
        q_b = fact_b.get("quality_score", 0.85)
        g_a = fact_a.get("grounding_score", 0.9)
        g_b = fact_b.get("grounding_score", 0.9)
        base_confidence = min(0.98, max(0.50, (q_a * q_b * g_a * g_b) ** 0.5))

        # Context comparisons
        same_period = (period_a == period_b) and (period_a is not None)
        different_period = (period_a != period_b) and (period_a is not None) and (period_b is not None)
        same_scope = (scope_a == scope_b) and (scope_a is not None)
        different_scope = (scope_a != scope_b) and (scope_a is not None) and (scope_b is not None)
        different_units = (norm_unit_a != norm_unit_b) and (norm_unit_a is not None) and (norm_unit_b is not None)

        # Value comparison
        values_match = False
        if norm_val_a is not None and norm_val_b is not None:
            if norm_val_a != 0:
                rel_diff = abs(norm_val_a - norm_val_b) / abs(norm_val_a)
                values_match = rel_diff < 0.015 and (norm_unit_a == norm_unit_b or not different_units)
            else:
                values_match = (norm_val_b == 0)
        else:
            # String value match (only if not generic filler)
            values_match = (val_a.lower() == val_b.lower()) and (val_a.lower() not in GENERIC_WORDS)

        # -------------------------------------------------------------
        # 2. Corroboration: Identical claim across sources
        # -------------------------------------------------------------
        if values_match and not different_period and not different_scope and not different_units:
            period_str = f" for {period_a}" if period_a else ""
            scope_str = f" ({scope_a})" if scope_a else ""
            return {
                "id": str(uuid.uuid4()),
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "canonical_key": canonical_key,
                "type": "CORROBORATE",
                "reasoning": f"Both documents ({doc_a_name} and {doc_b_name}) independently corroborate {subj_a}'s {pred_a} of {val_a}{period_str}{scope_str}.",
                "confidence": round(base_confidence * 0.98, 3),
                "comparison_context_json": {
                    "matching_metric": pred_a,
                    "matching_value": str(norm_val_a if norm_val_a is not None else val_a),
                    "period": period_a,
                    "scope": scope_a
                },
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        # -------------------------------------------------------------
        # 3. Contextual Reconciliation: Difference explained by metadata
        # -------------------------------------------------------------
        if different_period:
            period_a_str = str(period_a)
            period_b_str = str(period_b)
            if ("q" in period_a_str.lower() and "q" not in period_b_str.lower()) or \
               ("q" in period_b_str.lower() and "q" not in period_a_str.lower()):
                explanation = f"Apparent contradiction reconciled: '{doc_a_name}' reports for quarterly period {period_a} ({val_a}) while '{doc_b_name}' reports for full-year {period_b} ({val_b})."
            else:
                explanation = f"Apparent numerical variance reconciled: reported values represent different fiscal time horizons ({period_a} with {val_a} vs {period_b} with {val_b})."

            return {
                "id": str(uuid.uuid4()),
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "canonical_key": canonical_key,
                "type": "RECONCILE",
                "reasoning": explanation,
                "confidence": round(base_confidence * 0.94, 3),
                "comparison_context_json": {
                    "reconciling_factor": "temporal_difference",
                    "period_a": period_a,
                    "period_b": period_b
                },
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        if different_scope:
            return {
                "id": str(uuid.uuid4()),
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "canonical_key": canonical_key,
                "type": "RECONCILE",
                "reasoning": f"Reported values for {pred_a} differ due to reporting scope: '{doc_a_name}' reports {scope_a} ({val_a}) whereas '{doc_b_name}' reports {scope_b} ({val_b}).",
                "confidence": round(base_confidence * 0.92, 3),
                "comparison_context_json": {
                    "reconciling_factor": "scope_difference",
                    "scope_a": scope_a,
                    "scope_b": scope_b
                },
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        if different_units:
            return {
                "id": str(uuid.uuid4()),
                "fact_a_id": fact_a["id"],
                "fact_b_id": fact_b["id"],
                "canonical_key": canonical_key,
                "type": "RECONCILE",
                "reasoning": f"Both documents measure {pred_a}, but report in different unit/currency scales ({norm_unit_a or val_a} vs {norm_unit_b or val_b}).",
                "confidence": round(base_confidence * 0.90, 3),
                "comparison_context_json": {
                    "reconciling_factor": "unit_difference",
                    "unit_a": norm_unit_a,
                    "unit_b": norm_unit_b
                },
                "created_at": datetime.now(timezone.utc).isoformat()
            }

        # -------------------------------------------------------------
        # 4. Genuine Contradiction: Incompatible values without contextual explanation
        # -------------------------------------------------------------
        if not values_match and (same_period or (not period_a and not period_b)):
            if pred_sim >= 0.85:
                period_note = f"for {period_a}" if period_a else "for the same timeframe"
                return {
                    "id": str(uuid.uuid4()),
                    "fact_a_id": fact_a["id"],
                    "fact_b_id": fact_b["id"],
                    "canonical_key": canonical_key,
                    "type": "CONTRADICT",
                    "reasoning": f"Direct contradiction detected for {subj_a} - {pred_a} {period_note}: '{doc_a_name}' reports {val_a} whereas '{doc_b_name}' reports {val_b}. With matching reporting periods and scopes, these figures represent genuinely conflicting claims.",
                    "confidence": round(base_confidence * 0.92, 3),
                    "comparison_context_json": {
                        "conflict": True,
                        "value_a": val_a,
                        "value_b": val_b,
                        "period": period_a
                    },
                    "created_at": datetime.now(timezone.utc).isoformat()
                }

        # -------------------------------------------------------------
        # 5. Default Unrelated
        # -------------------------------------------------------------
        return {
            "id": str(uuid.uuid4()),
            "fact_a_id": fact_a["id"],
            "fact_b_id": fact_b["id"],
            "canonical_key": canonical_key,
            "type": "UNRELATED",
            "reasoning": f"The facts do not describe comparable claims ({pred_a} vs {pred_b}).",
            "confidence": 0.40,
            "comparison_context_json": {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
