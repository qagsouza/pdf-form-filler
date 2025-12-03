"""
Integration tests for FastAPI web application
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    try:
        from pdf_form_filler.web.app import app

        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI not installed (web extras not installed)")


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_index_page(client):
    """Test index page loads"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.skipif(
    not Path("tests/fixtures/sample_form.pdf").exists(),
    reason="Sample PDF not found",
)
def test_upload_endpoint(client, sample_pdf: Path):
    """Test PDF upload endpoint"""
    with open(sample_pdf, "rb") as f:
        files = {"pdf": ("test.pdf", f, "application/pdf")}
        response = client.post("/upload", files=files)

    assert response.status_code == 200


def test_upload_invalid_file(client, temp_dir: Path):
    """Test uploading non-PDF file"""
    fake_file = temp_dir / "test.txt"
    fake_file.write_text("not a pdf")

    with open(fake_file, "rb") as f:
        files = {"pdf": ("test.txt", f, "text/plain")}
        response = client.post("/upload", files=files)

    assert response.status_code == 400


def test_api_extract_endpoint(client, temp_dir: Path):
    """Test API extract endpoint with mock PDF"""
    # This would need a real PDF for proper testing
    # Skipping for now without fixtures
    pytest.skip("Requires sample PDF fixture")
