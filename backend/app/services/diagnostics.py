import uuid
import json
import sqlite3
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class DiagnosticTracker:
    """
    Collects run diagnostics per document and pipeline execution.
    Prevents silent failures and explains zero-fact scenarios.
    """

    def __init__(self, document_id: str):
        self.id = str(uuid.uuid4())
        self.document_id = document_id
        self.stage = "INITIALIZED"
        self.total_pages = 0
        self.pages_with_text = 0
        self.chunks_created = 0
        self.llm_calls = 0
        self.llm_successes = 0
        self.llm_failures = 0
        self.parse_failures = 0
        self.raw_facts = 0
        self.accepted_facts = 0
        self.rejected_facts = 0
        self.grounded_facts = 0
        self.candidates_found = 0
        self.relationships_created = 0
        self.logs: List[str] = []
        self.start_time = time.time()

    def log(self, message: str) -> None:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.logs.append(f"[{ts}] {message}")

    def set_stage(self, stage: str) -> None:
        self.stage = stage
        self.log(f"Entering stage: {stage}")

    def save(self, conn: sqlite3.Connection) -> None:
        execution_time_ms = int((time.time() - self.start_time) * 1000)
        now_str = datetime.now(timezone.utc).isoformat()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO diagnostics (
                id, document_id, stage, total_pages, pages_with_text,
                chunks_created, llm_calls, llm_successes, llm_failures,
                parse_failures, raw_facts, accepted_facts, rejected_facts,
                grounded_facts, candidates_found, relationships_created,
                execution_time_ms, logs_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.id, self.document_id, self.stage, self.total_pages,
            self.pages_with_text, self.chunks_created, self.llm_calls,
            self.llm_successes, self.llm_failures, self.parse_failures,
            self.raw_facts, self.accepted_facts, self.rejected_facts,
            self.grounded_facts, self.candidates_found, self.relationships_created,
            execution_time_ms, json.dumps(self.logs), now_str
        ))
        conn.commit()

    def explain_zero_facts(self) -> str:
        """Provide a human-readable explanation if zero facts were accepted."""
        if self.total_pages == 0:
            return "The PDF contains 0 pages or could not be opened."
        if self.pages_with_text == 0:
            return "No extractable text was found on any page (the document may be a scanned image requiring OCR)."
        if self.raw_facts == 0:
            return "No claims or numerical metrics were identified in the document text by the extractor."
        if self.accepted_facts == 0 and self.rejected_facts > 0:
            return f"All {self.rejected_facts} extracted candidate facts were rejected by the validation layer (e.g. isolated numbers, missing evidence, or malformed claims)."
        return "Extraction finished normally."
