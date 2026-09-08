from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.database import get_db, row_to_dict, rows_to_dicts
from app.schemas.pydantic_models import RelationshipResponse, RelationshipDetailResponse, FactResponse

router = APIRouter(prefix="/relationships", tags=["relationships"])

@router.get("", response_model=List[RelationshipResponse])
def list_relationships(
    type: Optional[str] = Query(None, description="CORROBORATE, CONTRADICT, RECONCILE"),
    min_confidence: Optional[float] = None,
    document_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    List cross-document relationships (Corroboration, Contradiction, Reconciliation).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT
                r.*,
                fa.subject as fact_a_subject, fa.predicate as fact_a_predicate,
                fa.value as fact_a_value, fa.period as fact_a_period,
                fa.page_number as fact_a_page, da.filename as fact_a_doc_name,
                fb.subject as fact_b_subject, fb.predicate as fact_b_predicate,
                fb.value as fact_b_value, fb.period as fact_b_period,
                fb.page_number as fact_b_page, db.filename as fact_b_doc_name
            FROM relationships r
            JOIN facts fa ON r.fact_a_id = fa.id
            JOIN documents da ON fa.document_id = da.id
            JOIN facts fb ON r.fact_b_id = fb.id
            JOIN documents db ON fb.document_id = db.id
            WHERE 1=1
        """
        params = []

        if type:
            query += " AND r.type = ?"
            params.append(type.upper())
        if min_confidence is not None:
            query += " AND r.confidence >= ?"
            params.append(min_confidence)
        if document_id:
            query += " AND (fa.document_id = ? OR fb.document_id = ?)"
            params.extend([document_id, document_id])

        query += " ORDER BY r.confidence DESC, r.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [RelationshipResponse(**row_to_dict(r)) for r in rows]

@router.get("/{relationship_id}", response_model=RelationshipDetailResponse)
def get_relationship_detail(relationship_id: str):
    """
    Get full side-by-side comparison detail between Fact A and Fact B,
    including exact evidence quotes, pages, and contextual explanation.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT
                r.*,
                fa.subject as fact_a_subject, fa.predicate as fact_a_predicate,
                fa.value as fact_a_value, fa.period as fact_a_period,
                fa.page_number as fact_a_page, da.filename as fact_a_doc_name,
                fb.subject as fact_b_subject, fb.predicate as fact_b_predicate,
                fb.value as fact_b_value, fb.period as fact_b_period,
                fb.page_number as fact_b_page, db.filename as fact_b_doc_name
            FROM relationships r
            JOIN facts fa ON r.fact_a_id = fa.id
            JOIN documents da ON fa.document_id = da.id
            JOIN facts fb ON r.fact_b_id = fb.id
            JOIN documents db ON fb.document_id = db.id
            WHERE r.id = ?
        """
        cursor.execute(query, (relationship_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Relationship not found")

        rel_dict = row_to_dict(row)

        # Retrieve full details for Fact A
        cursor.execute("""
            SELECT f.*, d.filename as document_filename
            FROM facts f
            JOIN documents d ON f.document_id = d.id
            WHERE f.id = ?
        """, (rel_dict["fact_a_id"],))
        fa_row = cursor.fetchone()
        rel_dict["fact_a"] = FactResponse(**row_to_dict(fa_row)) if fa_row else None

        # Retrieve full details for Fact B
        cursor.execute("""
            SELECT f.*, d.filename as document_filename
            FROM facts f
            JOIN documents d ON f.document_id = d.id
            WHERE f.id = ?
        """, (rel_dict["fact_b_id"],))
        fb_row = cursor.fetchone()
        rel_dict["fact_b"] = FactResponse(**row_to_dict(fb_row)) if fb_row else None

        return RelationshipDetailResponse(**rel_dict)
