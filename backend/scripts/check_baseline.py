import json
from pathlib import Path
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score

DATA_DIR = Path('D:/PROJECTS/CLAUDE_CLI_AGENTS/HACKER_EARTH/HACKATHONS/microOneHackerEarth/data')
splits_path = DATA_DIR / 'training' / 'splits.json'
with open(splits_path, 'r') as f:
    splits = json.load(f)

def extract_cosine_sim(item):
    claim_emb = np.array(item['features'][:384])
    evidence_emb = np.array(item['features'][384:768])
    return float(np.dot(claim_emb, evidence_emb) / (np.linalg.norm(claim_emb) * np.linalg.norm(evidence_emb)))

for split_name in ['train', 'calib', 'val', 'test']:
    data = splits[split_name]
    X = np.array([extract_cosine_sim(item) for item in data]).reshape(-1, 1)
    y = np.array([item['label'] for item in data])
    
    if split_name == 'train':
        model = LogisticRegression()
        model.fit(X, y)
        calib_model = CalibratedClassifierCV(model, method='isotonic', cv=3)
        calib_model.fit(X, y)
    
    if split_name == 'test':
        preds = calib_model.predict(X)
        acc = accuracy_score(y, preds)
        probs = calib_model.predict_proba(X)
        print(f'{split_name}: accuracy={acc:.3f}')
        print(f'  Sample probs: {probs[:5]}')
        print(f'  Sample preds: {preds[:5]}')
        print(f'  Sample labels: {y[:5]}')
