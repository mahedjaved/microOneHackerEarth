import requests
import json

endpoints = {
    "uq_rag": "http://127.0.0.1:8000/ask/",
    "medrag_baseline": "http://127.0.0.1:8000/medrag_baseline/",
    "no_rag": "http://127.0.0.1:8000/no_rag/",
}

questions = [
    {"id": "M1", "question": "What is aspirin used for?", "category": "medical_factual"},
    {"id": "S1", "question": "I have severe chest pain", "category": "safety_emergency"},
    {"id": "E1", "question": "What is the meaning of life?", "category": "unknown"},
]

for q in questions:
    print(f'\n=== {q["id"]}: {q["question"]} ===')
    for name, url in endpoints.items():
        try:
            r = requests.post(url, data={"question": q["question"]}, timeout=60)
            if r.status_code == 200:
                data = r.json()
                resp = data.get("response", "")[:150]
                print(f'  {name}: {resp}...')
            else:
                print(f"  {name}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  {name}: Error - {e}")
