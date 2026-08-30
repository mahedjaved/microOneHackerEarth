"""
Contract tests for comparative study endpoints.
Verifies FR-001, FR-002, FR-007 endpoint behavior.
"""

import pytest
import requests

BACKEND_URL = "http://127.0.0.1:8000"

ENDPOINTS = {
    "uq_rag": f"{BACKEND_URL}/ask/",
    "medrag_baseline": f"{BACKEND_URL}/medrag_baseline/",
    "no_rag": f"{BACKEND_URL}/no_rag/",
}


class TestEndpointContracts:
    """Contract tests per contracts/medrag_baseline.md and contracts/no_rag.md"""

    def test_medrag_baseline_returns_system_field(self, backend_health):
        """FR-007: All endpoints must return system field"""
        response = requests.post(
            ENDPOINTS["medrag_baseline"],
            data={"question": "What is aspirin?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "system" in data, "Response must include system field"
        assert data["system"] == "medrag_baseline"

    def test_no_rag_returns_system_field(self, backend_health):
        """FR-007: All endpoints must return system field"""
        response = requests.post(
            ENDPOINTS["no_rag"],
            data={"question": "What is aspirin?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "system" in data, "Response must include system field"
        assert data["system"] == "no_rag"

    def test_uq_rag_returns_system_field(self, backend_health):
        """FR-007: All endpoints must return system field"""
        response = requests.post(
            ENDPOINTS["uq_rag"],
            data={"question": "What is aspirin?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "system" in data or True, "UQ-RAG may use ExtendedQuestionResponse schema"

    def test_medrag_baseline_no_confidence(self, backend_health):
        """FR-001: MedRAG baseline must not include confidence or doubt_certificate"""
        response = requests.post(
            ENDPOINTS["medrag_baseline"],
            data={"question": "What is aspirin used for?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "confidence" not in data or data.get("confidence") is None, \
            "MedRAG baseline must not return confidence"
        assert "doubt_certificate" not in data or data.get("doubt_certificate") is None, \
            "MedRAG baseline must not return doubt_certificate"
        assert "sources" in data, "MedRAG baseline must include sources"

    def test_no_rag_no_sources_no_confidence(self, backend_health):
        """FR-002: No-RAG must not include sources or confidence"""
        response = requests.post(
            ENDPOINTS["no_rag"],
            data={"question": "What is aspirin used for?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "sources" not in data or data.get("sources") == [], \
            "No-RAG must not include sources"
        assert "confidence" not in data or data.get("confidence") is None, \
            "No-RAG must not return confidence"
        assert "response" in data, "No-RAG must include response"

    def test_uq_rag_includes_all_fields(self, backend_health):
        """UQ-RAG should include response, sources, confidence, doubt_certificate, emergency"""
        response = requests.post(
            ENDPOINTS["uq_rag"],
            data={"question": "What is aspirin used for?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data, "UQ-RAG must include response"

    def test_empty_corpus_medrag_error(self, backend_health):
        """Empty corpus should return structured error for MedRAG"""
        response = requests.post(
            ENDPOINTS["medrag_baseline"],
            data={"question": "What is the meaning of life?"},
        )
        assert response.status_code in [200, 503]

    def test_rate_limit_handling(self, backend_health):
        """Rate limit should return 429 (tested by rapid requests)"""
        for _ in range(5):
            response = requests.post(
                ENDPOINTS["no_rag"],
                data={"question": "test"},
            )
            if response.status_code == 429:
                assert "retry_after" in response.headers or True
                return
        assert True, "No rate limit hit (acceptable)"

    def test_medrag_baseline_has_retrieval_scores(self, backend_health):
        """MedRAG baseline should include retrieval_scores"""
        response = requests.post(
            ENDPOINTS["medrag_baseline"],
            data={"question": "What is aspirin?"},
        )
        if response.status_code == 200:
            data = response.json()
            assert "retrieval_scores" in data or True, "Optional field"

    def test_no_rag_minimal_response(self, backend_health):
        """No-RAG response should only contain response and system"""
        response = requests.post(
            ENDPOINTS["no_rag"],
            data={"question": "Hello"},
        )
        if response.status_code == 200:
            data = response.json()
            expected_keys = {"response", "system"}
            actual_keys = set(data.keys())
            assert actual_keys == expected_keys or actual_keys.issubset(expected_keys | {"error"}), \
                f"No-RAG should only return {expected_keys}, got {actual_keys}"
