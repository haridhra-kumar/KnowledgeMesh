export type GroundingStatus = 'VERIFIED' | 'PARTIAL' | 'UNVERIFIED';
export type FactType = 'financial_metric' | 'numerical_metric' | 'percentage' | 'date' | 'status' | 'comparison' | 'semantic_claim' | 'other';
export type RelationshipType = 'CORROBORATE' | 'CONTRADICT' | 'RECONCILE' | 'UNRELATED';
export type DocumentStatus = 'UPLOADED' | 'PARSING' | 'EXTRACTING' | 'VALIDATING' | 'GROUNDING' | 'NORMALIZING' | 'MATCHING' | 'RELATIONSHIPS' | 'COMPLETED' | 'FAILED';

export interface DocumentItem {
  id: string;
  filename: string;
  file_hash: string;
  file_size: number;
  page_count: number;
  status: DocumentStatus;
  progress_pct: number;
  progress_message: string;
  error_message?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
  facts_count: number;
  grounded_count: number;
}

export interface FactItem {
  id: string;
  document_id: string;
  document_filename?: string;
  page_number: number;
  chunk_id?: string;
  subject: string;
  predicate: string;
  value: string;
  fact_type: FactType;
  qualifiers_json?: Record<string, any> | null;
  period?: string | null;
  scope?: string | null;
  unit?: string | null;
  currency?: string | null;
  normalized_value?: number | null;
  normalized_unit?: string | null;
  evidence_quote: string;
  normalized_evidence?: string | null;
  grounding_status: GroundingStatus;
  grounding_score: number;
  confidence: number;
  status: 'ACCEPTED' | 'REJECTED';
  rejection_reason?: string | null;
  created_at: string;
  relationships?: any[];
  cluster?: any;
}

export interface RelationshipItem {
  id: string;
  fact_a_id: string;
  fact_b_id: string;
  canonical_key: string;
  type: RelationshipType;
  reasoning: string;
  confidence: number;
  comparison_context_json?: Record<string, any> | null;
  created_at: string;
  fact_a_subject?: string;
  fact_a_predicate?: string;
  fact_a_value?: string;
  fact_a_period?: string | null;
  fact_a_doc_name?: string;
  fact_a_page?: number;
  fact_b_subject?: string;
  fact_b_predicate?: string;
  fact_b_value?: string;
  fact_b_period?: string | null;
  fact_b_doc_name?: string;
  fact_b_page?: number;
  fact_a?: FactItem;
  fact_b?: FactItem;
}

export interface ClusterItem {
  id: string;
  canonical_subject: string;
  canonical_predicate: string;
  canonical_period?: string | null;
  canonical_scope?: string | null;
  display_name: string;
  description?: string | null;
  fact_count: number;
  source_doc_count: number;
  created_at: string;
  updated_at: string;
  members?: FactItem[];
}

export interface TimelineItem {
  id: string;
  fact_id: string;
  subject: string;
  predicate: string;
  value: string;
  normalized_value?: number | null;
  normalized_unit?: string | null;
  period: string;
  date_sort_key: string;
  evidence_quote: string;
  document_id: string;
  document_filename: string;
  page_number: number;
  grounding_status: GroundingStatus;
  confidence: number;
}

export interface TimelineGroup {
  subject: string;
  predicate: string;
  items: TimelineItem[];
}

export interface ReviewItem {
  id: string;
  review_type: 'UNGROUNDED' | 'LOW_CONFIDENCE' | 'CONTRADICTION' | 'REJECTED_FACT' | 'WARNING';
  title: string;
  reason: string;
  severity: 'high' | 'medium' | 'low';
  document_id?: string | null;
  document_filename?: string | null;
  page_number?: number | null;
  evidence_quote?: string | null;
  fact_id?: string | null;
  relationship_id?: string | null;
  data?: Record<string, any> | null;
  created_at: string;
}

export interface DashboardStats {
  total_documents: number;
  total_facts: number;
  verified_facts: number;
  total_relationships: number;
  corroborations: number;
  contradictions: number;
  reconciliations: number;
  needs_review_count: number;
  recent_activity: Array<{
    item_type: 'document' | 'relationship';
    id: string;
    title: string;
    subtitle: string;
    created_at: string;
  }>;
}

export interface DiagnosticItem {
  id: string;
  document_id?: string | null;
  document_filename?: string | null;
  stage: string;
  total_pages: number;
  pages_with_text: number;
  chunks_created: number;
  llm_calls: number;
  llm_successes: number;
  llm_failures: number;
  parse_failures: number;
  raw_facts: number;
  accepted_facts: number;
  rejected_facts: number;
  grounded_facts: number;
  candidates_found: number;
  relationships_created: number;
  execution_time_ms: number;
  logs_json?: string[] | null;
  created_at: string;
}

export interface UploadResponse {
  document: DocumentItem;
  is_duplicate: boolean;
  message: string;
}
