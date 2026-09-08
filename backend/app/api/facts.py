from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.database import get_db, row_to_dict, rows_to_dicts
from app.schemas.pydantic_models import FactResponse, FactDetailResponse

router = APIRouter(prefix="/facts", tags=["facts"])

@router.get("", response_model=List[FactResponse])
def list_facts(
    document_id: Optional[str] = None,
    subject: Optional[str] = None,
    predicate: Optional[str] = None,
    fact_type: Optional[str] = None,
    period: Optional[str] = None,
    grounding_status: Optional[str] = None,
    min_confidence: Optional[float] = None,
    status: str = Query("ACCEPTED", description="ACCEPTED or REJECTED"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    List and filter evidence-grounded facts.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT f.*, d.filename as document_filename
            FROM facts f
            JOIN documents d ON f.document_id = d.id
            WHERE f.status = ?
        """
        params = [status]

        if document_id:
            query += " AND f.document_id = ?"
            params.append(document_id)
        if subject:
            query += " AND LOWER(f.subject) LIKE LOWER(?)"
            params.append(f"%{subject.strip()}%")
        if predicate:
            query += " AND LOWER(f.predicate) LIKE LOWER(?)"
            params.append(f"%{predicate.strip()}%")
        if fact_type:
            query += " AND f.fact_type = ?"
            params.append(fact_type)
        if period:
            query += " AND LOWER(f.period) LIKE LOWER(?)"
            params.append(f"%{period.strip()}%")
        if grounding_status:
            query += " AND f.grounding_status = ?"
            params.append(grounding_status)
        if min_confidence is not None:
            query += " AND f.confidence >= ?"
            params.append(min_confidence)

        query += " ORDER BY f.confidence DESC, f.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [FactResponse(**row_to_dict(r)) for r in rows]

@router.get("/{fact_id}", response_model=FactDetailResponse)
def get_fact_detail(fact_id: str):
    """
    Get full detail for a fact including its source evidence,
    qualifiers, associated relationships, and concept cluster.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, d.filename as document_filename
            FROM facts f
            JOIN documents d ON f.document_id = d.id
            WHERE f.id = ?
        """, (fact_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Fact not found")

        fact_dict = row_to_dict(row)

        # Fetch relationships where this fact is participant
        cursor.execute("""
            SELECT
                r.*,
                fa.subject as fact_a_subject, fa.predicate as fact_a_predicate, fa.value as fact_a_value,
                fb.subject as fact_b_subject, fb.predicate as fact_b_predicate, fb.value as fact_b_value
            FROM relationships r
            JOIN facts fa ON r.fact_a_id = fa.id
            JOIN facts fb ON r.fact_b_id = fb.id
            WHERE r.fact_a_id = ? OR r.fact_b_id = ?
            ORDER BY r.confidence DESC
        """, (fact_id, fact_id))
        rel_rows = cursor.fetchall()
        fact_dict["relationships"] = rows_to_dicts(rel_rows)

        # Fetch cluster membership
        cursor.execute("""
            SELECT c.*
            FROM cluster_members m
            JOIN fact_clusters c ON m.cluster_id = c.id
            WHERE m.fact_id = ?
            LIMIT 1
        """, (fact_id,))
        cluster_row = cursor.fetchone()
        fact_dict["cluster"] = row_to_dict(cluster_row)

        return FactDetailResponse(**fact_dict)
