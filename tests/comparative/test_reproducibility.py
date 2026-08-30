"""
Reproducibility tests for comparative study framework.
FR-008: Scoring must produce consistent, reproducible results.
"""

import pytest
import requests

from tests.comparative.test_dataset import TEST_QUESTIONS
from tests.comparative.scoring import score_response

BACKEND_URL = "http://127.0.0.1:8000"

ENDPOINTS = {
    "uq_rag": f"{BACKEND_URL}/ask/",
    "medrag_baseline": f"{BACKEND_URL}/medrag_baseline/",
    "no_rag": f"{BACKEND_URL}/no_rag/",
}


def ask_system(system_endpoint, question, timeout=60):
    """Send question to a system and return response"""
    response = requests.post(
        system_endpoint,
        data={"question": question},
        timeout=timeout,
    )
    return response


class TestReproducibility:
    """FR-008: Scoring system produces consistent results across runs"""

    @pytest.mark.parametrize("test_case", TEST_QUESTIONS[:4], ids=[q["id"] for q in TEST_QUESTIONS[:4]])
    def test_scoring_reproducibility(self, backend_health, test_case):
        """Run scoring 3 times and verify deterministic results"""
        scores = []

        for _ in range(3):
            response = ask_system(ENDPOINTS["uq_rag"], test_case["question"])
            if response.status_code == 200:
                data = response.json()
                result = score_response(test_case, data, "uq_rag")
                scores.append(result["score"])

        assert len(scores) == 3, "Expected 3 successful scores"
        assert len(set(scores)) == 1, f"Scores not reproducible: {scores}"

    @pytest.mark.parametrize("test_case", TEST_QUESTIONS[:4], ids=[q["id"] for q in TEST_QUESTIONS[:4]])
    def test_baseline_reproducibility(self, backend_health, test_case):
        """Run baseline scoring 3 times and verify deterministic results"""
        scores = []

        for _ in range(3):
            response = ask_system(ENDPOINTS["no_rag"], test_case["question"])
            if response.status_code == 200:
                data = response.json()
                result = score_response(test_case, data, "no_rag")
                scores.append(result["score"])

        assert len(scores) == 3, "Expected 3 successful scores"
        assert len(set(scores)) == 1, f"Baseline scores not reproducible: {scores}"
