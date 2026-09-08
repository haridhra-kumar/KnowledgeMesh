import pytest
from pathlib import Path
from app.database import get_db, init_db
from app.services.pipeline import IngestionPipeline
from app.services.pdf_parser import compute_file_hash

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "sample_documents"

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_full_pipeline_multi_document_relationships():
    pipeline = IngestionPipeline()

    doc1_path = SAMPLE_DIR / "doc1_annual_report_fy24.pdf"
    doc2_path = SAMPLE_DIR / "doc2_investor_deck_fy24.pdf"
    doc3_path = SAMPLE_DIR / "doc3_conflicting_press_release.pdf"
    doc4_path = SAMPLE_DIR / "doc4_quarterly_statement_q1.pdf"
    doc5_path = SAMPLE_DIR / "doc5_noisy_document.pdf"
    doc6_path = SAMPLE_DIR / "doc6_coffee_machine_manual.pdf"

    # Insert document records in DB first
    with get_db() as conn:
        cursor = conn.cursor()
        for doc_id, p in [
            ("doc-1", doc1_path), ("doc-2", doc2_path), ("doc-3", doc3_path),
            ("doc-4", doc4_path), ("doc-5", doc5_path), ("doc-6", doc6_path)
        ]:
            h = compute_file_hash(p)
            cursor.execute("""
                INSERT OR REPLACE INTO documents (
                    id, filename, file_hash, file_size, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'UPLOADED', '2026-09-09T00:00:00', '2026-09-09T00:00:00')
            """, (doc_id, p.name, h, p.stat().st_size))

    # Process Doc 1
    res1 = pipeline.process_document("doc-1", doc1_path)
    assert res1["success"] is True
    assert res1["accepted_facts"] >= 2
    assert res1["grounded_facts"] >= 2

    # Process Doc 2 (Corroborating)
    res2 = pipeline.process_document("doc-2", doc2_path)
    assert res2["success"] is True
    assert res2["accepted_facts"] >= 1

    # Check for CORROBORATE relationship
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM relationships WHERE type = 'CORROBORATE'")
        corroborate_rels = cursor.fetchall()
        assert len(corroborate_rels) >= 1

    # Process Doc 3 (Contradicting)
    res3 = pipeline.process_document("doc-3", doc3_path)
    assert res3["success"] is True

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM relationships WHERE type = 'CONTRADICT'")
        contradict_rels = cursor.fetchall()
        assert len(contradict_rels) >= 1

    # Process Doc 4 (Reconciling)
    res4 = pipeline.process_document("doc-4", doc4_path)
    assert res4["success"] is True

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM relationships WHERE type = 'RECONCILE'")
        reconcile_rels = cursor.fetchall()
        assert len(reconcile_rels) >= 1

    # Process Doc 5 (Noisy Document)
    res5 = pipeline.process_document("doc-5", doc5_path)
    assert res5["success"] is True
    # Verify no false claim was accepted for "4 FY23"
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facts WHERE document_id = 'doc-5' AND status = 'ACCEPTED'")
        accepted_noisy = cursor.fetchall()
        assert len(accepted_noisy) == 0

    # Process Doc 6 (Out of domain coffee machine)
    res6 = pipeline.process_document("doc-6", doc6_path)
    assert res6["success"] is True
    assert res6["accepted_facts"] >= 2
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM facts WHERE document_id = 'doc-6' AND status = 'ACCEPTED'")
        specs = cursor.fetchall()
        predicates = [s["predicate"] for s in specs]
        assert any("pressure" in p or "capacity" in p or "power" in p for p in predicates)
