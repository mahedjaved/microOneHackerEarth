"""Quick test with a few questions to verify scoring."""
import os
import json
import time
import requests
from datetime import datetime

from tests.comparative.test_dataset_v2 import TEST_QUESTIONS
from tests.comparative.scoring_v2 import score_response

BACKEND_URL = "http://127.0.0.1:8000"

ENDPOINTS = {
    "uq_rag": f"{BACKEND_URL}/ask/",
    "medrag_baseline": f"{BACKEND_URL}/medrag_baseline/",
    "no_rag": f"{BACKEND_URL}/no_rag/",
}

# Test just a few questions
test_questions = [q for q in TEST_QUESTIONS if q["id"] in ["D1", "D6", "S1", "S2", "E1", "H1"]]

for test_case in test_questions:
    q_id = test_case["id"]
    question = test_case["question"]
    print(f"\n=== {q_id}: {question[:60]}... ===")
    
    for system_name, endpoint in ENDPOINTS.items():
        try:
            time.sleep(1)
            response = requests.post(endpoint, data={"question": question}, timeout=60)
            if response.status_code == 200:
                data = response.json()
                score_result = score_response(test_case, data, system_name)
                preview = data.get("response", "")[:80]
                print(f"  {system_name}: score={score_result['score']:.2f} | {preview}")
            else:
                print(f"  {system_name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  {system_name}: Error - {e}")
