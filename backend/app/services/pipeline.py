import os
import uuid
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from app.database import get_db_connection, row_to_dict
from app.services.pdf_parser import parse_pdf, PDFParsingError
from app.services.chunker import create_chunks
from app.services.extractor import FactExtractor
from app.services.validator import FactValidator
from app.services.grounding import EvidenceGrounder
from app.services.normalizer import normalize_fact_fields
from app.services.matcher import CandidateMatcher
from app.services.relationship_engine import RelationshipEngine
from app.services.clustering import FactClusterService
from app.services.diagnostics import DiagnosticTracker

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """
    End-to-end asynchronous document processing pipeline.
    Transforms raw PDFs into evidence-grounded, normalized, clustered,
    and cross-document related knowledge facts with strict semantic quality gates.
    """

    def __init__(self):
        self.extractor = FactExtractor()
        self.validator = FactValidator()
        self.grounder = EvidenceGrounder()
        self.matcher = CandidateMatcher(min_candidate_score=0.70)
        self.rel_engine = RelationshipEngine()

    def process_document(self, document_id: str, file_path: str | Path) -> Dict[str, Any]:
        """
        Execute full pipeline for a document incrementally.
        Updates status, progress, facts, candidates, relationships, and diagnostics in SQLite.
        """
        conn = get_db_connection()
        tracker = DiagnosticTracker(document_id)

        def update_doc_status(status: str, progress_pct: int, message: str, error_msg: Optional[str] = None):
            now_str = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                UPDATE documents
                SET status = ?, progress_pct = ?, progress_message = ?, error_message = ?, updated_at = ?
                WHERE id = ?
            """, (status, progress_pct, message, error_msg, now_str, document_id))
            conn.commit()

        try:
            tracker.log(f"Starting ingestion pipeline for document: {document_id}")
            update_doc_status("PARSING", 10, "Extracting text page-by-page from PDF...")
            tracker.set_stage("PARSING")

            # Stage 1: Parse PDF
            pdf_result = parse_pdf(file_path)
            tracker.total_pages = pdf_result["page_count"]
            tracker.pages_with_text = pdf_result["pages_with_text"]
            tracker.log(f"Parsed {tracker.total_pages} pages ({tracker.pages_with_text} with extractable text).")

            conn.execute("""
                UPDATE documents
                SET page_count = ?, metadata_json = ?
                WHERE id = ?
            """, (tracker.total_pages, json.dumps({
                "file_size": pdf_result["file_size"],
                "total_chars": pdf_result["total_chars"],
                "pages_with_text": pdf_result["pages_with_text"]
            }), document_id))
            conn.commit()

            # Stage 2: Chunk text
            tracker.set_stage("CHUNKING")
            chunks = create_chunks(pdf_result["pages"])
            tracker.chunks_created = len(chunks)
            tracker.log(f"Created {tracker.chunks_created} structured chunks across pages.")

            # Stage 3: Extract Facts
            update_doc_status("EXTRACTING", 30, f"Extracting factual claims from {len(chunks)} chunks...")
            tracker.set_stage("EXTRACTING")

            page_text_map = {p["page_number"]: p["text"] for p in pdf_result["pages"]}
            extracted_facts: List[Dict[str, Any]] = []

            for idx, chunk in enumerate(chunks):
                tracker.llm_calls += 1
                extract_res = self.extractor.extract_facts(chunk["text"], chunk["page_number"])
                if extract_res["llm_called"]:
                    if extract_res["success"]:
                        tracker.llm_successes += 1
                    else:
                        tracker.llm_failures += 1

                for raw_f in extract_res["raw_facts"]:
                    tracker.raw_facts += 1
                    raw_f["document_id"] = document_id
                    raw_f["page_number"] = chunk["page_number"]
                    raw_f["chunk_id"] = chunk["chunk_id"]
                    extracted_facts.append(raw_f)

            tracker.log(f"Raw facts extracted: {tracker.raw_facts}")

            # Stage 4: Semantic Validation Gate & Quality Evaluation
            update_doc_status("VALIDATING", 45, f"Validating {len(extracted_facts)} candidate facts...")
            tracker.set_stage("VALIDATING")

            accepted_facts: List[Dict[str, Any]] = []
            now_str = datetime.now(timezone.utc).isoformat()

            for fact in extracted_facts:
                page_text = page_text_map.get(fact["page_number"], "")
                is_valid, reason = self.validator.validate_fact(fact, page_text)

                fact_id = str(uuid.uuid4())
                fact["id"] = fact_id

                if is_valid:
                    tracker.accepted_facts += 1
                    fact["status"] = "ACCEPTED"
                    fact["rejection_reason"] = None
                    accepted_facts.append(fact)
                else:
                    tracker.rejected_facts += 1
                    fact["status"] = "REJECTED"
                    fact["rejection_reason"] = reason
                    # Store rejected facts in database for Review/Diagnostics
                    conn.execute("""
                        INSERT INTO facts (
                            id, document_id, page_number, chunk_id, subject,
                            predicate, value, fact_type, qualifiers_json, period,
                            scope, unit, currency, evidence_quote, grounding_status,
                            grounding_score, confidence, status, rejection_reason, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'UNVERIFIED', 0.0, 0.1, 'REJECTED', ?, ?)
                    """, (
                        fact_id, document_id, fact["page_number"], fact["chunk_id"],
                        fact.get("subject", "Unknown"), fact.get("predicate", "Unknown"),
                        fact.get("value", ""), fact.get("fact_type", "other"),
                        json.dumps(fact.get("qualifiers") or {}), fact.get("period"),
                        fact.get("scope"), fact.get("unit"), fact.get("currency"),
                        fact.get("evidence_quote", ""), reason, now_str
                    ))
            conn.commit()
            tracker.log(f"Facts validated: {tracker.accepted_facts} accepted, {tracker.rejected_facts} rejected.")

            # Stage 5: Evidence Grounding
            update_doc_status("GROUNDING", 60, f"Grounding evidence for {len(accepted_facts)} accepted facts...")
            tracker.set_stage("GROUNDING")

            grounded_facts: List[Dict[str, Any]] = []
            for fact in accepted_facts:
                page_text = page_text_map.get(fact["page_number"], "")
                ground_res = self.grounder.ground_evidence(fact["evidence_quote"], page_text)

                fact["grounding_status"] = ground_res["grounding_status"]
                fact["grounding_score"] = ground_res["grounding_score"]
                fact["normalized_evidence"] = ground_res["normalized_evidence"]

                if ground_res["grounding_status"] in ["VERIFIED", "PARTIAL"]:
                    tracker.grounded_facts += 1

                # Derive confidence from quality score and grounding score
                q_score = fact.get("quality_score", 0.8)
                g_score = ground_res["grounding_score"]
                fact["confidence"] = round(min(0.98, max(0.20, (g_score * 0.55 + q_score * 0.45))), 3)
                grounded_facts.append(fact)

            # Stage 6: Normalization & Fact Storage
            update_doc_status("NORMALIZING", 70, "Normalizing units, currencies, and fiscal periods...")
            tracker.set_stage("NORMALIZING")

            normalized_facts: List[Dict[str, Any]] = []
            for fact in grounded_facts:
                norm_fact = normalize_fact_fields(fact)
                normalized_facts.append(norm_fact)

                # Persist accepted fact into SQLite
                conn.execute("""
                    INSERT INTO facts (
                        id, document_id, page_number, chunk_id, subject,
                        predicate, value, fact_type, qualifiers_json, period,
                        scope, unit, currency, normalized_value, normalized_unit,
                        evidence_quote, normalized_evidence, grounding_status,
                        grounding_score, confidence, status, rejection_reason, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    norm_fact["id"], document_id, norm_fact["page_number"], norm_fact["chunk_id"],
                    norm_fact["subject"], norm_fact["predicate"], norm_fact["value"],
                    norm_fact["fact_type"], json.dumps(norm_fact.get("qualifiers") or {}),
                    norm_fact.get("period"), norm_fact.get("scope"), norm_fact.get("unit"),
                    norm_fact.get("currency"), norm_fact.get("normalized_value"),
                    norm_fact.get("normalized_unit"), norm_fact["evidence_quote"],
                    norm_fact.get("normalized_evidence"), norm_fact["grounding_status"],
                    norm_fact["grounding_score"], norm_fact["confidence"],
                    norm_fact["status"], None, now_str
                ))
            conn.commit()

            # Stage 7: Fact Clustering
            tracker.set_stage("CLUSTERING")
            for f in normalized_facts:
                FactClusterService.cluster_fact(conn, f)
            conn.commit()

            # Stage 8: Candidate Matching & Cross-Document Relationships
            update_doc_status("RELATIONSHIPS", 85, "Matching candidates and generating cross-document relationships...")
            tracker.set_stage("MATCHING_AND_RELATIONSHIPS")

            # Fetch existing accepted facts from other documents
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.*, d.filename as document_filename
                FROM facts f
                JOIN documents d ON f.document_id = d.id
                WHERE f.status = 'ACCEPTED' AND f.document_id != ?
            """, (document_id,))
            other_rows = cursor.fetchall()
            other_facts = [row_to_dict(r) for r in other_rows]

            candidate_pairs = []
            for new_fact in normalized_facts:
                candidates = self.matcher.find_candidates_for_fact(new_fact, other_facts)
                for cand in candidates:
                    candidate_pairs.append(cand)
                    # Persist candidate pair
                    conn.execute("""
                        INSERT OR IGNORE INTO candidate_pairs (id, fact_a_id, fact_b_id, match_reason, match_score, status, created_at)
                        VALUES (?, ?, ?, ?, ?, 'PENDING', ?)
                    """, (str(uuid.uuid4()), cand["fact_a_id"], cand["fact_b_id"], cand["match_reason"], cand["match_score"], now_str))

            tracker.candidates_found = len(candidate_pairs)
            conn.commit()

            # Evaluate relationships for candidate pairs
            fact_lookup = {f["id"]: f for f in normalized_facts}
            for of in other_facts:
                fact_lookup[of["id"]] = of

            for cand in candidate_pairs:
                f_a = fact_lookup.get(cand["fact_a_id"])
                f_b = fact_lookup.get(cand["fact_b_id"])
                if f_a and f_b:
                    rel_result = self.rel_engine.evaluate_relationship(f_a, f_b)
                    # ONLY persist actionable relationships; do NOT persist UNRELATED as visible relationship
                    if rel_result["type"] in ["CORROBORATE", "CONTRADICT", "RECONCILE"]:
                        tracker.relationships_created += 1
                        conn.execute("""
                            INSERT OR REPLACE INTO relationships (
                                id, fact_a_id, fact_b_id, canonical_key, type,
                                reasoning, confidence, comparison_context_json, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            rel_result["id"], rel_result["fact_a_id"], rel_result["fact_b_id"],
                            rel_result["canonical_key"], rel_result["type"], rel_result["reasoning"],
                            rel_result["confidence"], json.dumps(rel_result.get("comparison_context_json") or {}),
                            rel_result["created_at"]
                        ))
            conn.commit()

            # Finalize completion
            tracker.set_stage("COMPLETED")
            tracker.save(conn)

            msg = f"Completed successfully. Facts: {tracker.accepted_facts} accepted, {tracker.grounded_facts} grounded, {tracker.relationships_created} relationships created."
            update_doc_status("COMPLETED", 100, msg)
            tracker.log(msg)

            return {
                "success": True,
                "document_id": document_id,
                "pages": tracker.total_pages,
                "accepted_facts": tracker.accepted_facts,
                "grounded_facts": tracker.grounded_facts,
                "relationships_created": tracker.relationships_created
            }

        except Exception as e:
            logger.exception(f"Pipeline error on document {document_id}: {e}")
            tracker.set_stage("FAILED")
            tracker.log(f"Fatal error: {str(e)}")
            try:
                tracker.save(conn)
            except Exception:
                pass
            update_doc_status("FAILED", 0, "Processing failed", str(e))
            raise e
        finally:
            conn.close()

def run_pipeline_task(document_id: str, file_path: str):
    """Background task wrapper for document ingestion."""
    pipeline = IngestionPipeline()
    try:
        pipeline.process_document(document_id, file_path)
    except Exception as e:
        logger.error(f"Background task failed for document {document_id}: {e}")
