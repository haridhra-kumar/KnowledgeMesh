from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.database import get_db, row_to_dict
from app.schemas.pydantic_models import DiagnosticResponse

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

@router.get("", response_model=List[DiagnosticResponse])
def list_diagnostics(
    document_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100)
):
    """
    Get pipeline execution diagnostics and telemetry.
    Helps developers and users inspect extraction, parsing, and grounding details.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT dg.*, d.filename as document_filename
            FROM diagnostics dg
            LEFT JOIN documents d ON dg.document_id = d.id
            WHERE 1=1
        """
        params = []
        if document_id:
            query += " AND dg.document_id = ?"
            params.append(document_id)

        query += " ORDER BY dg.created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [DiagnosticResponse(**row_to_dict(r)) for r in rows]

@router.get("/{document_id}", response_model=DiagnosticResponse)
def get_document_diagnostic(document_id: str):
    """Get the latest diagnostics run for a specific document."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dg.*, d.filename as document_filename
            FROM diagnostics dg
            LEFT JOIN documents d ON dg.document_id = d.id
            WHERE dg.document_id = ?
            ORDER BY dg.created_at DESC
            LIMIT 1
        """, (document_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No diagnostics found for this document")
        return DiagnosticResponse(**row_to_dict(row))
