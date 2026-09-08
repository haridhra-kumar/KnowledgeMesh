"""
Reprocess Knowledge Base Script for KnowledgeMesh.

Cleans out legacy/corrupted facts and relationships, registers starter datasets,
and runs them through the overhauled semantic pipeline with strict validation,
grounding, and metric-family candidate matching.
"""

import sys
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import uuid

# Ensure backend directory is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import Settings
from app.database import get_db, init_db
from app.services.pipeline import IngestionPipeline
from app.services.pdf_parser import compute_file_hash, is_valid_pdf

def reprocess():
    settings = Settings()
    settings.ensure_directories()
    init_db()

    print("=" * 70)
    print("KNOWLEDGEMESH: REPROCESSING KNOWLEDGE BASE")
    print("=" * 70)

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 1. Clear corrupted / derived data tables
    print("\n[Step 1] Wiping corrupted facts, relationships, and clusters...")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM relationships")
        cursor.execute("DELETE FROM candidate_pairs")
        cursor.execute("DELETE FROM cluster_members")
        cursor.execute("DELETE FROM fact_clusters")
        cursor.execute("DELETE FROM diagnostics")
        cursor.execute("DELETE FROM facts")
        # Remove dummy test documents
        cursor.execute("DELETE FROM documents WHERE filename LIKE 'test_doc_%'")
        conn.commit()
    print("✓ Cleared all derived tables.")

    # 2. Gather starter documents
    starter_dirs = [
        PROJECT_ROOT / "sample_documents",
        PROJECT_ROOT / "starter-datasets" / "delhivery",
        PROJECT_ROOT / "starter-datasets" / "india-macroeconomy"
    ]

    docs_to_process = []

    for s_dir in starter_dirs:
        if not s_dir.exists():
            continue
        for pdf_path in sorted(s_dir.glob("*.pdf")):
            if not is_valid_pdf(pdf_path):
                continue
            
            # Destination path in uploads
            dest_name = f"{pdf_path.stem}_{compute_file_hash(pdf_path)[:8]}.pdf"
            dest_path = upload_dir / dest_name
            if not dest_path.exists():
                shutil.copy2(pdf_path, dest_path)

            file_hash = compute_file_hash(dest_path)
            file_size = dest_path.stat().st_size

            # Check if document record already exists
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM documents WHERE file_hash = ?", (file_hash,))
                row = cursor.fetchone()
                if row:
                    doc_id = row[0]
                    cursor.execute("""
                        UPDATE documents
                        SET status = 'UPLOADED', progress_pct = 0, error_message = NULL, updated_at = ?
                        WHERE id = ?
                    """, (datetime.now(timezone.utc).isoformat(), doc_id))
                else:
                    doc_id = str(uuid.uuid4())
                    now_str = datetime.now(timezone.utc).isoformat()
                    cursor.execute("""
                        INSERT INTO documents (
                            id, filename, file_hash, file_size, status,
                            progress_pct, progress_message, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, 'UPLOADED', 0, 'Ready for reprocessing', ?, ?)
                    """, (doc_id, pdf_path.name, file_hash, file_size, now_str, now_str))
                conn.commit()

            docs_to_process.append((doc_id, pdf_path.name, dest_path))

    print(f"\n[Step 2] Registered {len(docs_to_process)} starter documents for reprocessing:")
    for d_id, name, p in docs_to_process:
        print(f"  - [{d_id[:8]}...] {name} ({p.stat().st_size / 1024:.1f} KB)")

    # 3. Process each document through IngestionPipeline
    pipeline = IngestionPipeline()
    print("\n[Step 3] Processing documents through upgraded semantic pipeline...")

    for idx, (doc_id, name, p) in enumerate(docs_to_process, 1):
        print(f"\n--> Processing ({idx}/{len(docs_to_process)}): {name} ...")
        t_start = datetime.now()
        res = pipeline.process_document(doc_id, p)
        t_elapsed = (datetime.now() - t_start).total_seconds()
        print(f"    Status: {'SUCCESS' if res['success'] else 'FAILED'} in {t_elapsed:.2f}s")
        print(f"    Raw: {res.get('raw_facts', 0)} | Accepted: {res.get('accepted_facts', 0)} | Grounded: {res.get('grounded_facts', 0)} | Candidates: {res.get('candidate_pairs', 0)}")

    # 4. Post-processing Sanity Audit
    print("\n" + "=" * 70)
    print("SANITY AUDIT & VERIFICATION QUERIES")
    print("=" * 70)

    with get_db() as conn:
        cursor = conn.cursor()

        # Check total counts
        cursor.execute("SELECT count(*) FROM facts WHERE status = 'ACCEPTED'")
        total_accepted = cursor.fetchone()[0]

        cursor.execute("SELECT count(*) FROM facts WHERE status = 'REJECTED'")
        total_rejected = cursor.fetchone()[0]

        cursor.execute("SELECT count(*) FROM relationships")
        total_relationships = cursor.fetchone()[0]

        cursor.execute("SELECT count(*) FROM fact_clusters")
        total_clusters = cursor.fetchone()[0]

        print(f"\nKnowledge Layer Summary:")
        print(f"  Accepted Facts: {total_accepted}")
        print(f"  Rejected Facts (Filtered Noise): {total_rejected}")
        print(f"  Fact Clusters: {total_clusters}")
        print(f"  Cross-Document Relationships: {total_relationships}")

        # Failure Mode Check 1: Any verb or fragment facts accepted?
        cursor.execute("""
            SELECT count(*) FROM facts
            WHERE status = 'ACCEPTED'
              AND (
                LOWER(predicate) IN ('increased', 'decreased', 'grew', 'fell', 'rose', 'doubled', 'tripled', 'was', 'is', 'total', 'the')
                OR LOWER(value) IN ('increased', 'decreased', 'grew', 'fell', 'rose', ',', '.')
                OR LOWER(subject) IN ('we have', 'that has', 'our', 'we', 'the', 'this revenue', 'and total')
              )
        """)
        bad_facts_count = cursor.fetchone()[0]
        print(f"\n[Audit 1] Contaminated verb/fragment facts in ACCEPTED status: {bad_facts_count} (Expected: 0)")
        if bad_facts_count == 0:
            print("  ✓ PASS: Zero contaminated verb/fragment facts found!")
        else:
            print("  ✗ FAIL: Contaminated facts detected!")

        # Failure Mode Check 2: Any relationships comparing 'increased' vs 'increased'?
        cursor.execute("""
            SELECT count(*) FROM relationships r
            JOIN facts f1 ON r.fact_a_id = f1.id
            JOIN facts f2 ON r.fact_b_id = f2.id
            WHERE LOWER(f1.predicate) = LOWER(f2.predicate)
              AND LOWER(f1.predicate) IN ('increased', 'decreased', 'grew', 'fell', 'rose')
        """)
        bad_rels_count = cursor.fetchone()[0]
        print(f"\n[Audit 2] 'increased' vs 'increased' relationships: {bad_rels_count} (Expected: 0)")
        if bad_rels_count == 0:
            print("  ✓ PASS: Zero spurious verb-matching relationships found!")
        else:
            print("  ✗ FAIL: Spurious verb-matching relationships detected!")

        # Failure Mode Check 3: Any UNRELATED pairs stored in relationships?
        cursor.execute("SELECT count(*) FROM relationships WHERE type = 'UNRELATED'")
        unrelated_count = cursor.fetchone()[0]
        print(f"\n[Audit 3] UNRELATED relationships stored: {unrelated_count} (Expected: 0)")
        if unrelated_count == 0:
            print("  ✓ PASS: UNRELATED pairs correctly excluded from visible relationships!")
        else:
            print("  ✗ FAIL: UNRELATED pairs found in relationships table!")

        # Sample 15 Accepted Facts
        print("\n" + "-" * 70)
        print("SAMPLE ACCEPTED FACTS (High-Quality Claims)")
        print("-" * 70)
        cursor.execute("""
            SELECT f.subject, f.predicate, f.value, f.period, f.grounding_status, f.confidence, d.filename
            FROM facts f
            JOIN documents d ON f.document_id = d.id
            WHERE f.status = 'ACCEPTED'
            ORDER BY f.confidence DESC
            LIMIT 15
        """)
        for r in cursor.fetchall():
            subj, pred, val, period, g_status, conf, doc = r
            period_str = f" [{period}]" if period else ""
            print(f"  • {subj} | {pred}: {val}{period_str} (Grounding: {g_status}, Conf: {conf:.2f}) -- {doc}")

        # Sample Relationships
        print("\n" + "-" * 70)
        print("SAMPLE CROSS-DOCUMENT RELATIONSHIPS")
        print("-" * 70)
        cursor.execute("""
            SELECT f1.subject, f1.predicate, f1.value as v1, f2.value as v2, r.type, r.confidence, r.reasoning
            FROM relationships r
            JOIN facts f1 ON r.fact_a_id = f1.id
            JOIN facts f2 ON r.fact_b_id = f2.id
            LIMIT 10
        """)
        rels = cursor.fetchall()
        if not rels:
            print("  (No relationships formed among the current set of facts)")
        else:
            for r in rels:
                subj, pred, v1, v2, r_type, conf, reasoning = r
                short_reason = reasoning[:85] + "..." if len(reasoning) > 85 else reasoning
                print(f"  • [{r_type}] ({conf:.2f}) {subj} - {pred}: '{v1}' vs '{v2}'")
                print(f"    Reasoning: {short_reason}")

    print("\n" + "=" * 70)
    print("REPROCESSING COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    reprocess()
