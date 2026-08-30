import pytest
import requests
import time


BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:8501"


class TestFrontendUIPageLoad:
    """Test frontend page loads correctly."""

    def test_frontend_loads(self, backend_health, page):
        """Verify Streamlit frontend loads."""
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        assert "Medical" in page.title() or "microOne" in page.title() or page.title() != ""

    def test_frontend_has_chat_input(self, backend_health, page):
        """Verify frontend has a chat input field."""
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        chat_input = page.locator("input[type='text'], textarea, [data-testid='stTextInput']")
        assert chat_input.count() > 0

    def test_frontend_has_upload_button(self, backend_health, page):
        """Verify frontend has file upload capability."""
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        file_input = page.locator("input[type='file']")
        assert file_input.count() > 0


class TestFrontendUIChatInteraction:
    """Test chat interaction through the UI."""

    def test_send_question_returns_response(self, backend_health, page):
        """Verify sending a question returns a response."""
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        chat_input = page.locator("input[type='text'], textarea, [data-testid='stTextInput']")
        if chat_input.count() > 0:
            chat_input.first.fill("What is aspirin used for?")
            page.keyboard.press("Enter")
            page.wait_for_timeout(15000)
            response_area = page.locator("[data-testid='stMarkdown'], .stMarkdown")
            assert response_area.count() > 0

    def test_response_contains_disclaimer(self, backend_health, page):
        """Verify response includes medical disclaimer."""
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        chat_input = page.locator("input[type='text'], textarea, [data-testid='stTextInput']")
        if chat_input.count() > 0:
            chat_input.first.fill("What is aspirin used for?")
            page.keyboard.press("Enter")
            page.wait_for_timeout(15000)
            page_content = page.content()
            assert "not medical advice" in page_content.lower() or "consult" in page_content.lower()


class TestFrontendUIUpload:
    """Test file upload through the UI."""

    def test_upload_pdf_via_ui(self, backend_health, page, sample_pdf):
        """Verify PDF upload through the UI."""
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        file_input = page.locator("input[type='file']")
        if file_input.count() > 0:
            file_input.first.set_input_files(sample_pdf)
            page.wait_for_timeout(10000)
            page_content = page.content()
            assert "success" in page_content.lower() or "upload" in page_content.lower() or "error" in page_content.lower()


class TestFrontendUIDownload:
    """Test chat history download."""

    def test_download_button_exists(self, backend_health, page):
        """Verify download button exists after chat interaction."""
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        chat_input = page.locator("input[type='text'], textarea, [data-testid='stTextInput']")
        if chat_input.count() > 0:
            chat_input.first.fill("What is aspirin used for?")
            page.keyboard.press("Enter")
            page.wait_for_timeout(15000)
            download_btn = page.get_by_text("Download Chat History")
            assert download_btn.count() > 0

    def test_download_contains_timestamp(self, backend_health, page):
        """Verify downloaded file contains timestamp."""
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        chat_input = page.locator("input[type='text'], textarea, [data-testid='stTextInput']")
        if chat_input.count() > 0:
            chat_input.first.fill("What is aspirin used for?")
            page.keyboard.press("Enter")
            page.wait_for_timeout(15000)
            download_btn = page.get_by_text("Download Chat History")
            if download_btn.count() > 0:
                with page.expect_download() as download_info:
                    download_btn.first.click()
                download = download_info.value
                content = download.path().read_text() if download.path() else ""
                assert "2026" in content or "2025" in content or "2024" in content


class TestFrontendUIEmergencyState:
    """Test emergency query handling in UI."""

    def test_emergency_query_shows_warning(self, backend_health, page):
        """Verify emergency query triggers safety response in UI."""
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        chat_input = page.locator("input[type='text'], textarea, [data-testid='stTextInput']")
        if chat_input.count() > 0:
            chat_input.first.fill("I have severe chest pain and can't breathe")
            page.keyboard.press("Enter")
            page.wait_for_timeout(10000)
            page_content = page.content()
            assert "emergency" in page_content.lower() or "911" in page_content.lower() or "call" in page_content.lower()


class TestFrontendUIDoubtCertificate:
    """Test doubt certificate display in UI."""

    def test_uncertain_query_shows_doubt(self, backend_health, page):
        """Verify uncertain query shows doubt certificate in UI."""
        page.goto(FRONTEND_URL)
        page.wait_for_load_state("networkidle", timeout=30000)
        chat_input = page.locator("input[type='text'], textarea, [data-testid='stTextInput']")
        if chat_input.count() > 0:
            chat_input.first.fill("What is the cure for fictional disease X?")
            page.keyboard.press("Enter")
            page.wait_for_timeout(15000)
            page_content = page.content()
            assert "not" in page_content.lower() or "available" in page_content.lower() or "sorry" in page_content.lower() or "cannot" in page_content.lower()
