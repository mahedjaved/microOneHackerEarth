import pytest
import json
import os
import requests
from datetime import datetime

from tests.comparative.test_dataset import TEST_QUESTIONS, ACCURACY_SUITE_IDS, SAFETY_SUITE_IDS
from tests.comparative.scoring import score_response

BACKEND_URL = "http://127.0.0.1:8000"


def ask_system(system_endpoint, question, timeout=60):
    """Send question to a system and return response"""
    response = requests.post(
        system_endpoint,
        data={"question": question},
        timeout=timeout,
    )
    return response


class TestComparativeAnalysis:
    """End-to-end comparative study between RAG systems"""

    ENDPOINTS = {
        "uq_rag": f"{BACKEND_URL}/ask/",
        "medrag_baseline": f"{BACKEND_URL}/medrag_baseline/",
        "no_rag": f"{BACKEND_URL}/no_rag/",
    }

    @pytest.fixture(autouse=True)
    def setup_results_dir(self):
        """Ensure results directory exists"""
        os.makedirs("tests/comparative/results", exist_ok=True)
        yield

    @pytest.mark.parametrize("test_case", TEST_QUESTIONS, ids=[q["id"] for q in TEST_QUESTIONS])
    def test_all_systems(self, backend_health, test_case):
        """Run each question through all three systems and compare"""
        results = {}
        scores = {}

        for system_name, endpoint in self.ENDPOINTS.items():
            # Step 1: API call in its own try/except so a scoring bug
            # can never overwrite a real captured response.
            try:
                response = ask_system(endpoint, test_case["question"])
                response_data = response.json() if response.status_code == 200 else {
                    "error": response.text,
                    "status_code": response.status_code,
                }
                results[system_name] = {
                    "status": response.status_code,
                    "data": response_data,
                    "response_text": response_data.get("response", ""),
                }
            except Exception as e:
                results[system_name] = {"error": str(e)}
                scores[system_name] = {
                    "score": 0, "max_score": 3,
                    "reasons": [f"request failed: {e}"],
                    "errored": True,
                }
                continue

            # Step 2: Scoring in its own try/except so a scoring crash
            # only affects the score, not the captured response.
            if response.status_code == 200:
                try:
                    scores[system_name] = score_response(test_case, response_data, system_name)
                except Exception as e:
                    scores[system_name] = {
                        "score": 0, "max_score": 3,
                        "reasons": [f"scoring failed: {e}"],
                        "errored": True,
                    }
            else:
                scores[system_name] = {
                    "score": 0, "max_score": 3,
                    "reasons": [f"HTTP {response.status_code}"],
                    "errored": True,
                }

        self._save_comparison(test_case, results, scores)

        uq_score = scores.get("uq_rag", {}).get("score", 0)
        medrag_score = scores.get("medrag_baseline", {}).get("score", 0)

        if test_case["category"].startswith("safety_"):
            assert uq_score > medrag_score or uq_score == 3, \
                f"UQ-RAG should handle safety better for: {test_case['question']}"

        if test_case["category"] in ["unknown", "hallucination"]:
            assert uq_score >= 1, \
                f"UQ-RAG should express doubt for unknown/hallucination: {test_case['question']}"

    def _save_comparison(self, test_case, results, scores):
        """Save comparison results for report generation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/comparative/results/{test_case['id']}_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(
                {
                    "test_case": test_case,
                    "results": results,
                    "scores": scores,
                    "timestamp": timestamp,
                },
                f,
                indent=2,
            )

    def test_summary_report(self, backend_health):
        """Generate summary comparison report"""
        all_scores = {"uq_rag": [], "medrag_baseline": [], "no_rag": []}

        for test_case in TEST_QUESTIONS:
            for system_name, endpoint in self.ENDPOINTS.items():
                try:
                    response = ask_system(endpoint, test_case["question"])
                    if response.status_code == 200:
                        data = response.json()
                        score_data = score_response(test_case, data, system_name)
                        all_scores[system_name].append(score_data["score"])
                except Exception:
                    all_scores[system_name].append(0)

        summary = {}
        for system_name, scores_list in all_scores.items():
            avg_score = sum(scores_list) / len(scores_list) if scores_list else 0
            summary[system_name] = {
                "average_score": round(avg_score, 2),
                "total_questions": len(scores_list),
                "scores": scores_list,
            }

        with open("tests/comparative/results/summary.json", "w") as f:
            json.dump(summary, f, indent=2)

        assert summary["uq_rag"]["average_score"] >= summary["no_rag"]["average_score"], \
            "UQ-RAG should outperform or match No-RAG baseline"

        print(f"\n=== COMPARATIVE STUDY SUMMARY ===")
        for system_name, data in summary.items():
            print(f"{system_name}: {data['average_score']:.2f} avg score")
