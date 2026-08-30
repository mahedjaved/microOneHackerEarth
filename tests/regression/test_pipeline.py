import pytest
import requests


BACKEND_URL = "http://127.0.0.1:8000"


class TestChunkingWorkflow:
    """Test PDF upload and chunking workflow."""

    def test_upload_pdf_returns_200_or_500(self, backend_health, sample_pdf):
        """Verify PDF upload returns success or server error (if Pinecone unavailable)."""
        with open(sample_pdf, "rb") as f:
            files = [("files", ("test_document.pdf", f, "application/pdf"))]
            response = requests.post(f"{BACKEND_URL}/upload_pdfs/", files=files)
        assert response.status_code in [200, 500]

    def test_upload_without_files_returns_422(self, backend_health):
        """Verify upload without files returns validation error."""
        response = requests.post(f"{BACKEND_URL}/upload_pdfs/", files=[])
        assert response.status_code in [400, 422]

    def test_upload_non_pdf_may_error(self, backend_health, tmp_path):
        """Verify non-PDF files may be rejected or cause processing error."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")
        with open(txt_file, "rb") as f:
            files = [("files", ("test.txt", f, "text/plain"))]
            response = requests.post(f"{BACKEND_URL}/upload_pdfs/", files=files)
        assert response.status_code in [400, 422, 500]


class TestRetrievalWorkflow:
    """Test question asking and retrieval workflow."""

    def test_ask_endpoint_accepts_question(self, backend_health):
        """Verify /ask/ endpoint accepts a question."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is aspirin used for?"},
            timeout=30,
        )
        assert response.status_code in [200, 500]
        data = response.json()
        if response.status_code == 200:
            assert "response" in data or "error" in data

    def test_ask_returns_sources_when_successful(self, backend_health):
        """Verify successful response includes sources."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is aspirin used for?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("response"):
                assert isinstance(data.get("sources", []), list)

    def test_ask_empty_question_returns_error(self, backend_health):
        """Verify empty question is rejected."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": ""},
            timeout=10,
        )
        assert response.status_code in [400, 422]

    def test_ask_returns_disclaimer(self, backend_health):
        """Verify response includes medical disclaimer."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is aspirin used for?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("response"):
                assert data.get("disclaimer") is not None


class TestRetrievalRelevance:
    """Test relevance of retrieved content."""

    def test_retrieved_sources_are_non_empty(self, backend_health):
        """Verify returned sources are non-empty strings."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is aspirin used for?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("sources"):
                for source in data["sources"]:
                    assert isinstance(source, str)
                    assert len(source) > 0

    def test_irrelevant_query_triggers_doubt(self, backend_health):
        """Verify completely unrelated query may trigger doubt certificate."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "What is the meaning of life?"},
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            if not data.get("response"):
                assert data.get("doubt_certificate") is not None
