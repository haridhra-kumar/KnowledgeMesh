from fastapi import APIRouter
from app.database import get_db, row_to_dict, rows_to_dicts
from app.schemas.pydantic_models import DashboardStats

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("", response_model=DashboardStats)
def get_dashboard_stats():
    """
    Get aggregated system statistics in real time.
    Calculates exact counts of documents, facts, grounding rates,
    and cross-document relationship distributions.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Documents count
        cursor.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]

        # Total accepted facts
        cursor.execute("SELECT COUNT(*) FROM facts WHERE status = 'ACCEPTED'")
        total_facts = cursor.fetchone()[0]

        # Verified facts (grounding >= 0.85)
        cursor.execute("SELECT COUNT(*) FROM facts WHERE status = 'ACCEPTED' AND grounding_status = 'VERIFIED'")
        verified_facts = cursor.fetchone()[0]

        # Relationships by type
        cursor.execute("SELECT COUNT(*) FROM relationships")
        total_relationships = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM relationships WHERE type = 'CORROBORATE'")
        corroborations = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM relationships WHERE type = 'CONTRADICT'")
        contradictions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM relationships WHERE type = 'RECONCILE'")
        reconciliations = cursor.fetchone()[0]

        # Needs review count:
        # Ungrounded facts + Low confidence facts + Contradictions + Rejected facts + Failed docs
        cursor.execute("SELECT COUNT(*) FROM facts WHERE status = 'ACCEPTED' AND (grounding_status = 'UNVERIFIED' OR confidence < 0.60)")
        fact_review_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM facts WHERE status = 'REJECTED'")
        rejected_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM documents WHERE status = 'FAILED'")
        failed_docs_count = cursor.fetchone()[0]

        needs_review = fact_review_count + contradictions + rejected_count + failed_docs_count

        # Recent activity (latest documents and relationships)
        cursor.execute("""
            SELECT 'document' as item_type, id, filename as title, status as subtitle, created_at
            FROM documents
            ORDER BY created_at DESC LIMIT 5
        """)
        recent_docs = [dict(r) for r in cursor.fetchall()]

        cursor.execute("""
            SELECT 'relationship' as item_type, r.id,
                   (r.type || ': ' || fa.subject || ' ' || fa.predicate) as title,
                   r.reasoning as subtitle, r.created_at
            FROM relationships r
            JOIN facts fa ON r.fact_a_id = fa.id
            ORDER BY r.created_at DESC LIMIT 5
        """)
        recent_rels = [dict(r) for r in cursor.fetchall()]

        activity = sorted(recent_docs + recent_rels, key=lambda x: x["created_at"], reverse=True)[:8]

        return DashboardStats(
            total_documents=total_docs,
            total_facts=total_facts,
            verified_facts=verified_facts,
            total_relationships=total_relationships,
            corroborations=corroborations,
            contradictions=contradictions,
            reconciliations=reconciliations,
            needs_review_count=needs_review,
            recent_activity=activity
        )
