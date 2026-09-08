import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "sample_documents"

@pytest.fixture(scope="module")
def client():
    init_db()
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_stats_endpoint(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_facts" in data
    assert "verified_facts" in data
    assert "total_relationships" in data

def test_list_documents(client):
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_facts(client):
    response = client.get("/api/facts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_relationships(client):
    response = client.get("/api/relationships")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_list_clusters(client):
    response = client.get("/api/clusters")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_timeline_endpoint(client):
    response = client.get("/api/timeline")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_review_endpoint(client):
    response = client.get("/api/review")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_diagnostics_endpoint(client):
    response = client.get("/api/diagnostics")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_upload_and_duplicate_detection(client, tmp_path):
    # Create a fresh temporary PDF with unique timestamp to test upload & duplicate detection
    import time
    import fitz
    unique_name = f"test_doc_{int(time.time()*1000)}.pdf"
    pdf_path = tmp_path / unique_name
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), f"Unique test document content for upload {unique_name}.")
    doc.save(str(pdf_path))
    doc.close()

    try:
        with open(pdf_path, "rb") as f:
            # First upload: should be new
            res1 = client.post("/api/documents", files={"file": (unique_name, f, "application/pdf")})
            assert res1.status_code == 200
            data1 = res1.json()
            assert "document" in data1
            assert data1["is_duplicate"] is False

        with open(pdf_path, "rb") as f:
            # Second upload with exact same file: should detect duplicate
            res2 = client.post("/api/documents", files={"file": (unique_name, f, "application/pdf")})
            assert res2.status_code == 200
            data2 = res2.json()
            assert data2["is_duplicate"] is True
            assert "already been uploaded" in data2["message"]
    finally:
        if pdf_path.exists():
            pdf_path.unlink()
