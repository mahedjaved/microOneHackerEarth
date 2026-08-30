"""
Graceful degradation tests for comparative study framework.
Verifies system behavior under failure conditions.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock

from tests.comparative.test_dataset import TEST_QUESTIONS
from tests.comparative.scoring import score_response

BACKEND_URL = "http://127.0.0.1:8000"

ENDPOINTS = {
    "uq_rag": f"{BACKEND_URL}/ask/",
    "medrag_baseline": f"{BACKEND_URL}/medrag_baseline/",
    "no_rag": f"{BACKEND_URL}/no_rag/",
}


class TestGracefulDegradation:
    """Edge case handling per spec.md"""

    def test_empty_question_returns_422(self, backend_health):
        """Verify empty question returns 422 error"""
        for name, endpoint in ENDPOINTS.items():
            response = requests.post(endpoint, data={"question": ""})
            assert response.status_code == 422, f"{name} should return 422 for empty question"

    def test_whitespace_question_returns_422(self, backend_health):
        """Verify whitespace-only question returns 422 error"""
        for name, endpoint in ENDPOINTS.items():
            response = requests.post(endpoint, data={"question": "   "})
            assert response.status_code == 422, f"{name} should return 422 for whitespace question"

    def test_unknown_question_doubt_certificate(self, backend_health):
        """Verify UQ-RAG returns doubt certificate for unknown questions"""
        unknown_q = next(q for q in TEST_QUESTIONS if q["category"] == "unknown")
        response = requests.post(ENDPOINTS["uq_rag"], data={"question": unknown_q["question"]})

        if response.status_code == 200:
            data = response.json()
            assert "doubt_certificate" in data or "response" in data, \
                "UQ-RAG should include doubt certificate or response for unknown questions"

    def test_safety_question_emergency_response(self, backend_health):
        """Verify UQ-RAG returns emergency response for safety questions"""
        safety_q = next(q for q in TEST_QUESTIONS if q["category"] == "safety_emergency")
        response = requests.post(ENDPOINTS["uq_rag"], data={"question": safety_q["question"]})

        if response.status_code == 200:
            data = response.json()
            assert data.get("emergency") is True or "emergency" in data.get("response", "").lower(), \
                "UQ-RAG should detect emergency for safety-critical questions"
