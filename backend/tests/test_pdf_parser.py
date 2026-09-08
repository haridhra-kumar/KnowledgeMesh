import pytest
from pathlib import Path
from app.services.pdf_parser import parse_pdf, compute_file_hash, is_valid_pdf

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "sample_documents"

def test_is_valid_pdf():
    pdf_path = SAMPLE_DIR / "doc1_annual_report_fy24.pdf"
    assert is_valid_pdf(pdf_path) is True

def test_compute_file_hash():
    pdf_path = SAMPLE_DIR / "doc1_annual_report_fy24.pdf"
    h1 = compute_file_hash(pdf_path)
    h2 = compute_file_hash(pdf_path)
    assert len(h1) == 64
    assert h1 == h2

def test_parse_pdf_extracts_pages():
    pdf_path = SAMPLE_DIR / "doc1_annual_report_fy24.pdf"
    res = parse_pdf(pdf_path)
    assert res["page_count"] == 1
    assert res["pages_with_text"] == 1
    assert len(res["pages"]) == 1
    page1 = res["pages"][0]
    assert page1["page_number"] == 1
    assert "Acme Logistics" in page1["text"]
    assert "Rs. 2,500 crore" in page1["text"]

def test_large_pdf_page_count():
    pdf_path = SAMPLE_DIR / "doc7_large_annual_report.pdf"
    res = parse_pdf(pdf_path)
    assert res["page_count"] == 10
    assert res["pages_with_text"] == 10
    # Check that page 2 has expected text
    assert "Executive Summary" in res["pages"][1]["text"]
