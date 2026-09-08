from typing import List, Optional
from fastapi import APIRouter, Query

from app.database import get_db
from app.schemas.pydantic_models import TimelineGroupResponse
from app.services.timeline import TimelineService

router = APIRouter(prefix="/timeline", tags=["timeline"])

@router.get("", response_model=List[TimelineGroupResponse])
def get_timeline(
    subject: Optional[str] = None,
    predicate: Optional[str] = None,
    document_id: Optional[str] = None
):
    """
    Get facts organized chronologically by explicit temporal metadata.
    Does not use PDF page order for chronology.
    """
    with get_db() as conn:
        groups = TimelineService.get_timeline(conn, subject=subject, predicate=predicate, document_id=document_id)
        return [TimelineGroupResponse(**g) for g in groups]
