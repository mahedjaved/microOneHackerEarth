import json
import glob

results = []
for f in sorted(glob.glob('tests/comparative/results/run*.json')):
    with open(f) as fh:
        results.append(json.load(fh))

categories = {"medical_factual": [], "safety": [], "unknown": [], "hallucination": []}

for run in results[:1]:
    for q in run:
        tc = q['test_case']
        uq = q['scores'].get('uq_rag', {})
        medrag = q['scores'].get('medrag_baseline', {})
        norag = q['scores'].get('no_rag', {})
        
        cat = tc['category']
        if cat.startswith('safety'):
            cat = 'safety'
        
        categories.setdefault(cat, []).append({
            'id': tc['id'],
            'uq_score': uq.get('score', 0),
            'medrag_score': medrag.get('score', 0),
            'norag_score': norag.get('score', 0),
            'uq_dim': uq.get('dimension', '')
        })

for cat, items in categories.items():
    print(f'\n=== {cat.upper()} ===')
    for item in items:
        print(f"  {item['id']}: UQ={item['uq_score']:.2f} MedRAG={item['medrag_score']:.2f} NoRAG={item['norag_score']:.2f} dim={item['uq_dim']}")
