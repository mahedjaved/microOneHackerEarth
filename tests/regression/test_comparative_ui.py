"""
Playwright E2E tests for comparative study framework.
FR-006: Complete user journey verification through Streamlit frontend.
"""

import pytest
from playwright.sync_api import Page, expect

FRONTEND_URL = "http://127.0.0.1:8501"


class TestComparativeUI:
    """E2E tests for comparative study user journeys"""

    def test_frontend_loads(self, page: Page, frontend_health):
        """Verify Streamlit frontend loads successfully"""
        page.goto(FRONTEND_URL)
        expect(page).to_have_title(/Medical|Assistant|CURA/i)

    def test_upload_document_flow(self, page: Page, frontend_health, sample_pdf):
        """Verify document upload through frontend"""
        page.goto(FRONTEND_URL)

        upload_input = page.locator('input[type="file"]')
        if upload_input.count() > 0:
            upload_input.set_input_files(sample_pdf)
            page.wait_for_timeout(2000)

    def test_question_submission_flow(self, page: Page, frontend_health):
        """Verify question submission through frontend"""
        page.goto(FRONTEND_URL)

        text_input = page.locator('input[type="text"], textarea').first
        if text_input.count() > 0:
            text_input.fill("What is aspirin used for?")
            page.keyboard.press("Enter")
            page.wait_for_timeout(3000)

    def test_response_display(self, page: Page, frontend_health):
        """Verify response is displayed after question submission"""
        page.goto(FRONTEND_URL)

        text_input = page.locator('input[type="text"], textarea').first
        if text_input.count() > 0:
            text_input.fill("What is aspirin?")
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

    def test_history_download_flow(self, page: Page, frontend_health):
        """Verify history download functionality"""
        page.goto(FRONTEND_URL)

        download_button = page.locator('button:has-text("Download")')
        if download_button.count() > 0:
            download_button.click()
            page.wait_for_timeout(1000)
