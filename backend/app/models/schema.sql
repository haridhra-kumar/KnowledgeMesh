-- KnowledgeMesh SQLite Database Schema

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'UPLOADED',
    progress_pct INTEGER NOT NULL DEFAULT 0,
    progress_message TEXT NOT NULL DEFAULT 'Document uploaded',
    error_message TEXT,
    duplicate_of TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_hash ON documents(file_hash);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    chunk_id TEXT,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    value TEXT NOT NULL,
    fact_type TEXT NOT NULL DEFAULT 'semantic_claim',
    qualifiers_json TEXT,
    period TEXT,
    scope TEXT,
    unit TEXT,
    currency TEXT,
    normalized_value REAL,
    normalized_unit TEXT,
    evidence_quote TEXT NOT NULL,
    normalized_evidence TEXT,
    grounding_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
    grounding_score REAL NOT NULL DEFAULT 0.0,
    confidence REAL NOT NULL DEFAULT 0.5,
    status TEXT NOT NULL DEFAULT 'ACCEPTED',
    rejection_reason TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_facts_doc_id ON facts(document_id);
CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(subject);
CREATE INDEX IF NOT EXISTS idx_facts_predicate ON facts(predicate);
CREATE INDEX IF NOT EXISTS idx_facts_grounding ON facts(grounding_status);
CREATE INDEX IF NOT EXISTS idx_facts_status ON facts(status);
CREATE INDEX IF NOT EXISTS idx_facts_period ON facts(period);

CREATE TABLE IF NOT EXISTS candidate_pairs (
    id TEXT PRIMARY KEY,
    fact_a_id TEXT NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    fact_b_id TEXT NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    match_reason TEXT NOT NULL,
    match_score REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'PENDING',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_candidate_pairs_ab ON candidate_pairs(fact_a_id, fact_b_id);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    fact_a_id TEXT NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    fact_b_id TEXT NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    canonical_key TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.5,
    comparison_context_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(type);
CREATE INDEX IF NOT EXISTS idx_relationships_canonical ON relationships(canonical_key);
CREATE INDEX IF NOT EXISTS idx_relationships_fact_a ON relationships(fact_a_id);
CREATE INDEX IF NOT EXISTS idx_relationships_fact_b ON relationships(fact_b_id);

CREATE TABLE IF NOT EXISTS fact_clusters (
    id TEXT PRIMARY KEY,
    canonical_subject TEXT NOT NULL,
    canonical_predicate TEXT NOT NULL,
    canonical_period TEXT,
    canonical_scope TEXT,
    display_name TEXT NOT NULL,
    description TEXT,
    fact_count INTEGER NOT NULL DEFAULT 0,
    source_doc_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_clusters_subject_pred ON fact_clusters(canonical_subject, canonical_predicate);

CREATE TABLE IF NOT EXISTS cluster_members (
    cluster_id TEXT NOT NULL REFERENCES fact_clusters(id) ON DELETE CASCADE,
    fact_id TEXT NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    similarity_score REAL NOT NULL DEFAULT 1.0,
    added_at TEXT NOT NULL,
    PRIMARY KEY (cluster_id, fact_id)
);

CREATE TABLE IF NOT EXISTS diagnostics (
    id TEXT PRIMARY KEY,
    document_id TEXT REFERENCES documents(id) ON DELETE CASCADE,
    stage TEXT NOT NULL,
    total_pages INTEGER DEFAULT 0,
    pages_with_text INTEGER DEFAULT 0,
    chunks_created INTEGER DEFAULT 0,
    llm_calls INTEGER DEFAULT 0,
    llm_successes INTEGER DEFAULT 0,
    llm_failures INTEGER DEFAULT 0,
    parse_failures INTEGER DEFAULT 0,
    raw_facts INTEGER DEFAULT 0,
    accepted_facts INTEGER DEFAULT 0,
    rejected_facts INTEGER DEFAULT 0,
    grounded_facts INTEGER DEFAULT 0,
    candidates_found INTEGER DEFAULT 0,
    relationships_created INTEGER DEFAULT 0,
    execution_time_ms INTEGER DEFAULT 0,
    logs_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_diagnostics_doc ON diagnostics(document_id);
