"""
Run all tests and generate results for the comparative study.
"""
import os
import json
import requests
from datetime import datetime

from tests.comparative.test_dataset import TEST_QUESTIONS, ACCURACY_SUITE_IDS, SAFETY_SUITE_IDS
from tests.comparative.scoring import score_response

BACKEND_URL = "http://127.0.0.1:8000"

ENDPOINTS = {
    "uq_rag": f"{BACKEND_URL}/ask/",
    "medrag_baseline": f"{BACKEND_URL}/medrag_baseline/",
    "no_rag": f"{BACKEND_URL}/no_rag/",
}


def ask_system(endpoint, question, timeout=60):
    response = requests.post(endpoint, data={"question": question}, timeout=timeout)
    return response


def run_comparison():
    os.makedirs("tests/comparative/results", exist_ok=True)

    for test_case in TEST_QUESTIONS:
        q_id = test_case["id"]
        question = test_case["question"]
        print(f"Testing {q_id}: {question[:50]}...")

        results = {}
        scores = {}

        for system_name, endpoint in ENDPOINTS.items():
            try:
                response = ask_system(endpoint, question)
                if response.status_code == 200:
                    data = response.json()
                    results[system_name] = {"status": 200, "data": data}
                    scores[system_name] = score_response(test_case, data, system_name)
                else:
                    results[system_name] = {"status": response.status_code, "error": response.text}
                    scores[system_name] = {"score": 0, "max_score": 3, "reasons": [f"HTTP {response.status_code}"]}
            except Exception as e:
                results[system_name] = {"error": str(e)}
                scores[system_name] = {"score": 0, "max_score": 3, "reasons": [str(e)]}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"tests/comparative/results/{q_id}_{timestamp}.json"

        with open(result_file, "w") as f:
            json.dump({
                "test_case": test_case,
                "results": results,
                "scores": scores,
                "timestamp": timestamp,
            }, f, indent=2)

        print(f"  Scored: UQ={scores.get('uq_rag', {}).get('score', 'N/A')}, MedRAG={scores.get('medrag_baseline', {}).get('score', 'N/A')}, NoRAG={scores.get('no_rag', {}).get('score', 'N/A')}")

    print("\nAll tests complete!")


if __name__ == "__main__":
    run_comparison()
