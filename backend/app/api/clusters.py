from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.database import get_db, row_to_dict, rows_to_dicts
from app.schemas.pydantic_models import ClusterResponse, ClusterDetailResponse, FactResponse

router = APIRouter(prefix="/clusters", tags=["clusters"])

@router.get("", response_model=List[ClusterResponse])
def list_clusters(
    subject: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """List fact concept clusters."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM fact_clusters WHERE 1=1"
        params = []
        if subject:
            query += " AND LOWER(canonical_subject) LIKE LOWER(?)"
            params.append(f"%{subject.strip()}%")

        query += " ORDER BY fact_count DESC, updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [ClusterResponse(**row_to_dict(r)) for r in rows]

@router.get("/{cluster_id}", response_model=ClusterDetailResponse)
def get_cluster_detail(cluster_id: str):
    """Get concept cluster details and all its member facts across documents."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM fact_clusters WHERE id = ?", (cluster_id,))
        cluster_row = cursor.fetchone()
        if not cluster_row:
            raise HTTPException(status_code=404, detail="Cluster not found")

        cluster_dict = row_to_dict(cluster_row)

        cursor.execute("""
            SELECT f.*, d.filename as document_filename
            FROM cluster_members m
            JOIN facts f ON m.fact_id = f.id
            JOIN documents d ON f.document_id = d.id
            WHERE m.cluster_id = ?
            ORDER BY f.period ASC, f.confidence DESC
        """, (cluster_id,))
        member_rows = cursor.fetchall()
        cluster_dict["members"] = [FactResponse(**row_to_dict(r)) for r in member_rows]

        return ClusterDetailResponse(**cluster_dict)
