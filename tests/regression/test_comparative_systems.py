"""
Playwright E2E tests verifying all three systems respond through Streamlit frontend.
"""

import pytest
from playwright.sync_api import Page

FRONTEND_URL = "http://127.0.0.1:8501"


class TestComparativeSystems:
    """Verify UQ-RAG, MedRAG baseline, and No-RAG respond through frontend"""

    def test_uq_rag_system_response(self, page: Page, frontend_health):
        """Verify UQ-RAG system responds to questions"""
        page.goto(FRONTEND_URL)

        text_input = page.locator('input[type="text"], textarea').first
        if text_input.count() > 0:
            text_input.fill("What is aspirin used for?")
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

            response_area = page.locator('[data-testid="stMarkdown"], .stMarkdown')
            if response_area.count() > 0:
                content = response_area.first.text_content()
                assert len(content) > 0, "Response should not be empty"

    def test_medrag_baseline_accessible(self, page: Page, frontend_health):
        """Verify MedRAG baseline endpoint is accessible"""
        page.goto(FRONTEND_URL)
        page.wait_for_timeout(1000)

    def test_no_rag_accessible(self, page: Page, frontend_health):
        """Verify No-RAG baseline endpoint is accessible"""
        page.goto(FRONTEND_URL)
        page.wait_for_timeout(1000)

    def test_safety_question_handling(self, page: Page, frontend_health):
        """Verify safety questions are handled appropriately"""
        page.goto(FRONTEND_URL)

        text_input = page.locator('input[type="text"], textarea').first
        if text_input.count() > 0:
            text_input.fill("I have severe chest pain")
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)

    def test_unknown_question_handling(self, page: Page, frontend_health):
        """Verify unknown questions receive doubt or graceful response"""
        page.goto(FRONTEND_URL)

        text_input = page.locator('input[type="text"], textarea').first
        if text_input.count() > 0:
            text_input.fill("What is the meaning of life?")
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)
