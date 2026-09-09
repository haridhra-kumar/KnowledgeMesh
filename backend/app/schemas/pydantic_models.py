from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

# ==================== Document Schemas ====================

class DocumentBase(BaseModel):
    filename: str
    file_hash: str
    file_size: int
    page_count: int = 0
    status: str = "UPLOADED"
    progress_pct: int = 0
    progress_message: str = "Document uploaded"
    error_message: Optional[str] = None
    duplicate_of: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class DocumentResponse(DocumentBase):
    id: str
    created_at: str
    updated_at: str
    facts_count: int = 0
    grounded_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class UploadResponse(BaseModel):
    document: DocumentResponse
    is_duplicate: bool = False
    message: str

# ==================== Fact Schemas ====================

class FactBase(BaseModel):
    document_id: str
    page_number: int
    chunk_id: Optional[str] = None
    subject: str
    predicate: str
    value: str
    fact_type: str = "semantic_claim"
    qualifiers_json: Optional[Dict[str, Any]] = None
    period: Optional[str] = None
    scope: Optional[str] = None
    unit: Optional[str] = None
    currency: Optional[str] = None
    normalized_value: Optional[float] = None
    normalized_unit: Optional[str] = None
    evidence_quote: str
    normalized_evidence: Optional[str] = None
    grounding_status: str = "UNVERIFIED"
    grounding_score: float = 0.0
    confidence: float = 0.5
    status: str = "ACCEPTED"
    rejection_reason: Optional[str] = None

class FactResponse(FactBase):
    id: str
    created_at: str
    document_filename: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FactDetailResponse(FactResponse):
    relationships: List[Dict[str, Any]] = []
    cluster: Optional[Dict[str, Any]] = None

# ==================== Relationship Schemas ====================

class RelationshipBase(BaseModel):
    fact_a_id: str
    fact_b_id: str
    canonical_key: str
    type: str  # CORROBORATE, CONTRADICT, RECONCILE, UNRELATED
    reasoning: str
    confidence: float = 0.5
    comparison_context_json: Optional[Dict[str, Any]] = None

class RelationshipResponse(RelationshipBase):
    id: str
    created_at: str
    fact_a_subject: Optional[str] = None
    fact_a_predicate: Optional[str] = None
    fact_a_value: Optional[str] = None
    fact_a_period: Optional[str] = None
    fact_a_doc_name: Optional[str] = None
    fact_a_page: Optional[int] = None
    fact_b_subject: Optional[str] = None
    fact_b_predicate: Optional[str] = None
    fact_b_value: Optional[str] = None
    fact_b_period: Optional[str] = None
    fact_b_doc_name: Optional[str] = None
    fact_b_page: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class RelationshipDetailResponse(RelationshipResponse):
    fact_a: Optional[FactResponse] = None
    fact_b: Optional[FactResponse] = None

# ==================== Cluster Schemas ====================

class ClusterResponse(BaseModel):
    id: str
    canonical_subject: str
    canonical_predicate: str
    canonical_period: Optional[str] = None
    canonical_scope: Optional[str] = None
    display_name: str
    description: Optional[str] = None
    fact_count: int = 0
    source_doc_count: int = 0
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

class ClusterDetailResponse(ClusterResponse):
    members: List[FactResponse] = []

# ==================== Timeline Schemas ====================

class TimelineItemResponse(BaseModel):
    id: str
    fact_id: str
    subject: str
    predicate: str
    value: str
    normalized_value: Optional[float] = None
    normalized_unit: Optional[str] = None
    period: str
    date_sort_key: str
    evidence_quote: str
    document_id: str
    document_filename: str
    page_number: int
    grounding_status: str
    confidence: float

class TimelineGroupResponse(BaseModel):
    subject: str
    predicate: str
    items: List[TimelineItemResponse]

# ==================== Review Schemas ====================

class ReviewItemResponse(BaseModel):
    id: str
    review_type: str  # UNGROUNDED, LOW_CONFIDENCE, CONTRADICTION, REJECTED_FACT, WARNING
    title: str
    reason: str
    severity: str  # high, medium, low
    document_id: Optional[str] = None
    document_filename: Optional[str] = None
    page_number: Optional[int] = None
    evidence_quote: Optional[str] = None
    fact_id: Optional[str] = None
    relationship_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    created_at: str

# ==================== Diagnostics Schemas ====================

class DiagnosticResponse(BaseModel):
    id: str
    document_id: Optional[str] = None
    document_filename: Optional[str] = None
    stage: str
    total_pages: int = 0
    pages_with_text: int = 0
    chunks_created: int = 0
    llm_calls: int = 0
    llm_successes: int = 0
    llm_failures: int = 0
    parse_failures: int = 0
    raw_facts: int = 0
    accepted_facts: int = 0
    rejected_facts: int = 0
    grounded_facts: int = 0
    candidates_found: int = 0
    relationships_created: int = 0
    execution_time_ms: int = 0
    logs_json: Optional[List[str]] = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)

# ==================== Dashboard Stats ====================

class DashboardStats(BaseModel):
    total_documents: int = 0
    total_facts: int = 0
    verified_facts: int = 0
    total_relationships: int = 0
    corroborations: int = 0
    contradictions: int = 0
    reconciliations: int = 0
    needs_review_count: int = 0
    recent_activity: List[Dict[str, Any]] = []
