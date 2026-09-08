import hashlib
import re
from pathlib import Path
from typing import Dict, Any, List
import fitz  # PyMuPDF

class PDFParsingError(Exception):
    pass

def compute_file_hash(file_path: str | Path) -> str:
    """Compute SHA-256 hash of a file for deduplication."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def is_valid_pdf(file_path: str | Path) -> bool:
    """Check magic bytes to verify file is a valid PDF."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
            return header.startswith(b"%PDF-")
    except Exception:
        return False

def clean_extracted_text(text: str) -> str:
    """Clean common PDF extraction artifacts while preserving layout."""
    if not text:
        return ""
    # Remove soft hyphens and zero-width spaces
    text = text.replace('\xad', '').replace('\u200b', '').replace('\ufeff', '')
    # Normalize non-breaking spaces and thin spaces
    text = text.replace('\xa0', ' ').replace('\u2009', ' ').replace('\u202f', ' ')
    # Rejoin words broken by hyphenation across line breaks: e.g. "com-\npany" -> "company"
    text = re.sub(r'(\b[a-zA-Z]{2,})[-–—]\s*\n\s*([a-zA-Z]{2,}\b)', r'\1\2', text)
    return text

def parse_pdf(file_path: str | Path) -> Dict[str, Any]:
    """
    Extract text page-by-page from a PDF using PyMuPDF.
    Preserves page boundaries and metadata.
    """
    path = Path(file_path)
    if not path.exists():
        raise PDFParsingError(f"File not found: {file_path}")

    if not is_valid_pdf(path):
        raise PDFParsingError(f"File is not a valid PDF: {path.name}")

    file_size = path.stat().st_size
    file_hash = compute_file_hash(path)

    pages: List[Dict[str, Any]] = []
    total_chars = 0
    pages_with_text = 0

    try:
        doc = fitz.open(str(path))
        page_count = len(doc)

        for page_idx in range(page_count):
            page = doc[page_idx]
            page_num = page_idx + 1  # 1-indexed
            raw_text = page.get_text("text") or ""
            text = clean_extracted_text(raw_text)
            text_clean = text.strip()
            char_count = len(text_clean)
            has_text = char_count >= 10

            if has_text:
                pages_with_text += 1
                total_chars += char_count

            pages.append({
                "page_number": page_num,
                "text": text,
                "char_count": char_count,
                "has_text": has_text
            })

        doc.close()
    except Exception as e:
        raise PDFParsingError(f"Error parsing PDF with PyMuPDF: {str(e)}") from e

    return {
        "filename": path.name,
        "file_hash": file_hash,
        "file_size": file_size,
        "page_count": page_count,
        "pages_with_text": pages_with_text,
        "total_chars": total_chars,
        "pages": pages
    }
