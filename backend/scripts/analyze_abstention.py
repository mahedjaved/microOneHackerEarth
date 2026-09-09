import json
from pathlib import Path

results_path = Path(__file__).parent.parent.parent / 'tests' / 'comparative' / 'results' / 'run1_20260904_061404.json'
with open(results_path) as f:
    data = json.load(f)

print('=== ALL ABSTENTION CASES ===')
print('Cases where UQ-RAG score < 1.0')
print()

for entry in data:
    tc = entry['test_case']
    scores = entry.get('scores') or {}
    
    uq_score_data = scores.get('uq_rag') or {}
    med_score_data = scores.get('medrag_baseline') or {}
    
    if not uq_score_data or not med_score_data:
        continue
    
    uq_score = uq_score_data.get('score', 'N/A')
    med_score = med_score_data.get('score', 'N/A')
    
    if isinstance(uq_score, (int, float)) and uq_score < 1.0:
        print(f"\n{tc['id']}: {tc['question'][:60]}...")
        print(f"  Category: {tc['category']}")
        print(f"  UQ-RAG: {uq_score}")
        print(f"  MedRAG: {med_score}")
        
        uq_api = uq_score_data.get('api_response') or {}
        med_api = med_score_data.get('api_response') or {}
        
        uq_text = uq_api.get('response') or (uq_api.get('doubt_certificate') or {}).get('message', 'N/A')
        med_text = med_api.get('response', 'N/A')
        
        print(f"  UQ-RAG: {str(uq_text)[:120]}...")
        print(f"  MedRAG: {str(med_text)[:120]}...")
