import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import get_db, row_to_dict, rows_to_dicts
from app.schemas.pydantic_models import DocumentResponse, UploadResponse
from app.services.pdf_parser import compute_file_hash, is_valid_pdf
from app.services.pipeline import IngestionPipeline

router = APIRouter(prefix="/documents", tags=["documents"])
pipeline = IngestionPipeline()

def run_pipeline_task(doc_id: str, file_path: str):
    pipeline.process_document(doc_id, file_path)

@router.post("", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a PDF document.
    Checks file type, calculates SHA-256 hash, detects duplicate uploads,
    and initiates asynchronous background processing.
    """
    settings.ensure_directories()

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents (.pdf) are supported.")

    temp_id = str(uuid.uuid4())
    temp_path = Path(settings.upload_dir) / f"temp_{temp_id}_{file.filename}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    if not is_valid_pdf(temp_path):
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid PDF document.")

    file_size = temp_path.stat().st_size
    file_hash = compute_file_hash(temp_path)

    # Duplicate check by SHA-256 hash
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,))
        existing = cursor.fetchone()

        if existing:
            temp_path.unlink()  # Clean up temp file
            existing_dict = row_to_dict(existing)

            # Count facts
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN grounding_status IN ('VERIFIED', 'PARTIAL') THEN 1 ELSE 0 END) FROM facts WHERE document_id = ?", (existing_dict["id"],))
            counts = cursor.fetchone()
            existing_dict["facts_count"] = counts[0] if counts else 0
            existing_dict["grounded_count"] = counts[1] if counts and counts[1] else 0

            return UploadResponse(
                document=DocumentResponse(**existing_dict),
                is_duplicate=True,
                message=f"Document '{existing_dict['filename']}' has already been uploaded and processed."
            )

        # New Document
        doc_id = str(uuid.uuid4())
        final_filename = f"{doc_id}_{file.filename}"
        final_path = Path(settings.upload_dir) / final_filename
        shutil.move(temp_path, final_path)

        now_str = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO documents (
                id, filename, file_hash, file_size, page_count,
                status, progress_pct, progress_message, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 0, 'UPLOADED', 0, 'Document uploaded, waiting to process...', ?, ?)
        """, (doc_id, file.filename, file_hash, file_size, now_str, now_str))

        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        new_doc = row_to_dict(cursor.fetchone())
        new_doc["facts_count"] = 0
        new_doc["grounded_count"] = 0

    # Start background ingestion
    background_tasks.add_task(run_pipeline_task, doc_id, str(final_path))

    return UploadResponse(
        document=DocumentResponse(**new_doc),
        is_duplicate=False,
        message=f"Document '{file.filename}' uploaded successfully. Processing started in background."
    )

@router.get("", response_model=List[DocumentResponse])
def list_documents():
    """List all documents with processing status and fact metrics."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                d.*,
                COUNT(f.id) as facts_count,
                SUM(CASE WHEN f.grounding_status IN ('VERIFIED', 'PARTIAL') THEN 1 ELSE 0 END) as grounded_count
            FROM documents d
            LEFT JOIN facts f ON d.id = f.document_id AND f.status = 'ACCEPTED'
            GROUP BY d.id
            ORDER BY d.created_at DESC
        """)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = row_to_dict(r)
            d["facts_count"] = d.get("facts_count") or 0
            d["grounded_count"] = d.get("grounded_count") or 0
            result.append(DocumentResponse(**d))
        return result

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str):
    """Get single document details and progress."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                d.*,
                COUNT(f.id) as facts_count,
                SUM(CASE WHEN f.grounding_status IN ('VERIFIED', 'PARTIAL') THEN 1 ELSE 0 END) as grounded_count
            FROM documents d
            LEFT JOIN facts f ON d.id = f.document_id AND f.status = 'ACCEPTED'
            WHERE d.id = ?
            GROUP BY d.id
        """, (document_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        d = row_to_dict(row)
        d["facts_count"] = d.get("facts_count") or 0
        d["grounded_count"] = d.get("grounded_count") or 0
        return DocumentResponse(**d)


@router.delete("")
def delete_all_documents():
    """Delete all documents and reset the entire fact layer."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents")
        cursor.execute("DELETE FROM facts")
        cursor.execute("DELETE FROM relationships")
        cursor.execute("DELETE FROM claim_clusters")
        cursor.execute("DELETE FROM diagnostics")
        return {"success": True, "message": "All documents and knowledge reset successfully."}

@router.delete("/{document_id}")
def delete_document(document_id: str):
    """Delete a document and all cascaded facts and relationships."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename FROM documents WHERE id = ?", (document_id,))
        doc = cursor.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        return {"success": True, "message": f"Document '{doc['filename']}' and all associated knowledge deleted."}


@router.post("/{document_id}/reprocess")
def reprocess_document(document_id: str, background_tasks: BackgroundTasks):
    """Trigger reprocessing of an existing document."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        doc = cursor.fetchone()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Find file path
        pattern = f"{document_id}_*"
        files = list(Path(settings.upload_dir).glob(pattern))
        if not files:
            raise HTTPException(status_code=404, detail="Source PDF file is missing from storage.")

        file_path = str(files[0])
        # Clear existing facts and relationships for this doc
        cursor.execute("DELETE FROM facts WHERE document_id = ?", (document_id,))
        cursor.execute("UPDATE documents SET status = 'UPLOADED', progress_pct = 0, progress_message = 'Reprocessing scheduled...' WHERE id = ?", (document_id,))

    background_tasks.add_task(run_pipeline_task, document_id, file_path)
    return {"success": True, "message": "Reprocessing started in background."}
