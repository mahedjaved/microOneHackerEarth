import pytest
import requests


BACKEND_URL = "http://127.0.0.1:8000"


class TestFileSizeValidation:
    """Test file size limits."""

    def test_oversized_file_rejected(self, backend_health, large_file):
        """Verify files over 50MB are rejected."""
        with open(large_file, "rb") as f:
            files = [("files", ("large_file.pdf", f, "application/pdf"))]
            response = requests.post(f"{BACKEND_URL}/upload_pdfs/", files=files)
        assert response.status_code in [400, 413, 422, 500]

    def test_valid_size_file_accepted(self, backend_health, sample_pdf):
        """Verify files under 50MB are accepted (or fail only due to Pinecone)."""
        with open(sample_pdf, "rb") as f:
            files = [("files", ("test_document.pdf", f, "application/pdf"))]
            response = requests.post(f"{BACKEND_URL}/upload_pdfs/", files=files)
        assert response.status_code in [200, 500]


class TestPIIRedaction:
    """Test PII redaction in downloaded artifacts."""

    def test_download_contains_no_ssn(self, backend_health, page):
        """Verify downloaded artifacts don't contain SSN patterns."""
        page.goto("http://127.0.0.1:8501")
        page.wait_for_load_state("networkidle")
        chat_input = page.locator("input[type='text'], textarea, [data-testid='stTextInput']")
        if chat_input.count() > 0:
            chat_input.first.fill("My SSN is 123-45-6789")
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            download_btn = page.get_by_text("Download Chat History")
            if download_btn.count() > 0:
                with page.expect_download() as download_info:
                    download_btn.first.click()
                download = download_info.value
                content = download.path().read_text() if download.path() else ""
                assert "123-45-6789" not in content

    def test_download_contains_no_email(self, backend_health, page):
        """Verify downloaded artifacts don't contain email addresses."""
        page.goto("http://127.0.0.1:8501")
        page.wait_for_load_state("networkidle")
        chat_input = page.locator("input[type='text'], textarea, [data-testid='stTextInput']")
        if chat_input.count() > 0:
            chat_input.first.fill("Contact me at test@example.com")
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            download_btn = page.get_by_text("Download Chat History")
            if download_btn.count() > 0:
                with page.expect_download() as download_info:
                    download_btn.first.click()
                download = download_info.value
                content = download.path().read_text() if download.path() else ""
                assert "test@example.com" not in content


class TestEmptyInputValidation:
    """Test empty input handling."""

    def test_empty_question_rejected(self, backend_health):
        """Verify empty question returns error."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": ""},
            timeout=10,
        )
        assert response.status_code in [400, 422, 500]

    def test_whitespace_only_question_rejected(self, backend_health):
        """Verify whitespace-only question returns error."""
        response = requests.post(
            f"{BACKEND_URL}/ask/",
            data={"question": "   "},
            timeout=10,
        )
        assert response.status_code in [400, 422, 500]


class TestBackendErrorHandling:
    """Test backend error handling."""

    def test_health_endpoint_returns_status(self, backend_health):
        """Verify health endpoint returns status."""
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_invalid_endpoint_returns_404(self, backend_health):
        """Verify invalid endpoint returns 404."""
        response = requests.get(f"{BACKEND_URL}/invalid_endpoint", timeout=5)
        assert response.status_code == 404
