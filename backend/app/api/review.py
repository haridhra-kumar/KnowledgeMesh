from typing import List, Optional
from fastapi import APIRouter

from app.database import get_db, row_to_dict
from app.schemas.pydantic_models import ReviewItemResponse

router = APIRouter(prefix="/review", tags=["review"])

@router.get("", response_model=List[ReviewItemResponse])
def get_review_items(
    severity: Optional[str] = None,
    review_type: Optional[str] = None
):
    """
    Get all items needing human review:
    - Genuine contradictions across documents (High / Medium based on confidence)
    - Ungrounded or weakly grounded facts (Medium / Low)
    - Low-confidence extractions (Low)
    - Rejected extraction noise like isolated numbers (Low)
    - Documents with processing failures (High)
    """
    items: List[ReviewItemResponse] = []

    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Contradictions (High if high confidence, Medium if lower)
        cursor.execute("""
            SELECT
                r.*,
                fa.subject as fact_a_subject, fa.predicate as fact_a_predicate,
                fa.value as fact_a_value, fa.evidence_quote as fact_a_evidence,
                da.filename as doc_a_name, fa.page_number as fact_a_page,
                fb.value as fact_b_value, fb.evidence_quote as fact_b_evidence,
                db.filename as doc_b_name, fb.page_number as fact_b_page
            FROM relationships r
            JOIN facts fa ON r.fact_a_id = fa.id
            JOIN documents da ON fa.document_id = da.id
            JOIN facts fb ON r.fact_b_id = fb.id
            JOIN documents db ON fb.document_id = db.id
            WHERE r.type = 'CONTRADICT'
            ORDER BY r.created_at DESC
        """)
        contradictions = cursor.fetchall()
        for c in contradictions:
            c_dict = row_to_dict(c)
            contra_sev = "high" if c_dict.get("confidence", 0) >= 0.85 else "medium"
            items.append(ReviewItemResponse(
                id=f"rev_contra_{c_dict['id']}",
                review_type="CONTRADICTION",
                title=f"Direct Contradiction: {c_dict['fact_a_subject']} {c_dict['fact_a_predicate']}",
                reason=c_dict["reasoning"],
                severity=contra_sev,
                document_id=None,
                document_filename=f"{c_dict['doc_a_name']} vs {c_dict['doc_b_name']}",
                page_number=c_dict['fact_a_page'],
                evidence_quote=f"Doc A: \"{c_dict['fact_a_evidence']}\" vs Doc B: \"{c_dict['fact_b_evidence']}\"",
                relationship_id=c_dict["id"],
                data=c_dict,
                created_at=c_dict["created_at"]
            ))

        # 2. Rejected Noisy Extractions (e.g. "4 FY23") -> Low Severity
        cursor.execute("""
            SELECT f.*, d.filename as document_filename
            FROM facts f
            JOIN documents d ON f.document_id = d.id
            WHERE f.status = 'REJECTED'
            ORDER BY f.created_at DESC
            LIMIT 50
        """)
        rejected = cursor.fetchall()
        for r in rejected:
            r_dict = row_to_dict(r)
            items.append(ReviewItemResponse(
                id=f"rev_rej_{r_dict['id']}",
                review_type="REJECTED_FACT",
                title=f"Rejected Extraction: '{r_dict['subject']} - {r_dict['predicate']}'",
                reason=r_dict["rejection_reason"] or "Semantic validation rejected noise or isolated numerical fragment.",
                severity="low",
                document_id=r_dict["document_id"],
                document_filename=r_dict["document_filename"],
                page_number=r_dict["page_number"],
                evidence_quote=r_dict["evidence_quote"],
                fact_id=r_dict["id"],
                data=r_dict,
                created_at=r_dict["created_at"]
            ))

        # 3. Weakly Grounded / Unverified Facts -> Medium/Low Severity
        cursor.execute("""
            SELECT f.*, d.filename as document_filename
            FROM facts f
            JOIN documents d ON f.document_id = d.id
            WHERE f.status = 'ACCEPTED' AND (f.grounding_status = 'UNVERIFIED' OR f.grounding_score < 0.70)
            ORDER BY f.grounding_score ASC
            LIMIT 50
        """)
        ungrounded = cursor.fetchall()
        for u in ungrounded:
            u_dict = row_to_dict(u)
            g_sev = "medium" if (u_dict["grounding_score"] or 0) < 0.50 else "low"
            items.append(ReviewItemResponse(
                id=f"rev_ground_{u_dict['id']}",
                review_type="UNGROUNDED",
                title=f"Weak Evidence Grounding ({int((u_dict['grounding_score'] or 0) * 100)}%): {u_dict['subject']} {u_dict['predicate']}",
                reason="The claim could not be fully matched to verbatim source page text. Review source wording.",
                severity=g_sev,
                document_id=u_dict["document_id"],
                document_filename=u_dict["document_filename"],
                page_number=u_dict["page_number"],
                evidence_quote=u_dict["evidence_quote"],
                fact_id=u_dict["id"],
                data=u_dict,
                created_at=u_dict["created_at"]
            ))

        # 4. Low Confidence Facts (< 0.60) -> Low Severity
        cursor.execute("""
            SELECT f.*, d.filename as document_filename
            FROM facts f
            JOIN documents d ON f.document_id = d.id
            WHERE f.status = 'ACCEPTED' AND f.confidence < 0.60 AND f.grounding_status != 'UNVERIFIED'
            ORDER BY f.confidence ASC
            LIMIT 30
        """)
        low_conf = cursor.fetchall()
        for lc in low_conf:
            lc_dict = row_to_dict(lc)
            items.append(ReviewItemResponse(
                id=f"rev_conf_{lc_dict['id']}",
                review_type="LOW_CONFIDENCE",
                title=f"Low Confidence Claim ({int(lc_dict['confidence'] * 100)}%): {lc_dict['subject']} {lc_dict['predicate']}",
                reason="Claim has weak qualifiers or low semantic clarity.",
                severity="low",
                document_id=lc_dict["document_id"],
                document_filename=lc_dict["document_filename"],
                page_number=lc_dict["page_number"],
                evidence_quote=lc_dict["evidence_quote"],
                fact_id=lc_dict["id"],
                data=lc_dict,
                created_at=lc_dict["created_at"]
            ))

        # 5. Failed Documents -> High Severity
        cursor.execute("""
            SELECT * FROM documents WHERE status = 'FAILED'
            ORDER BY updated_at DESC
        """)
        failed_docs = cursor.fetchall()
        for fd in failed_docs:
            fd_dict = row_to_dict(fd)
            items.append(ReviewItemResponse(
                id=f"rev_doc_{fd_dict['id']}",
                review_type="WARNING",
                title=f"Document Ingestion Failed: {fd_dict['filename']}",
                reason=fd_dict["error_message"] or "Fatal error during document parsing or extraction.",
                severity="high",
                document_id=fd_dict["id"],
                document_filename=fd_dict["filename"],
                page_number=None,
                evidence_quote=None,
                data=fd_dict,
                created_at=fd_dict["updated_at"]
            ))

    # Apply optional filters
    if severity:
        items = [i for i in items if i.severity == severity.lower()]
    if review_type:
        items = [i for i in items if i.review_type == review_type.upper()]

    return items
