import json
from pathlib import Path
import numpy as np

DATA_DIR = Path('D:/PROJECTS/CLAUDE_CLI_AGENTS/HACKER_EARTH/HACKATHONS/microOneHackerEarth/data')
splits_path = DATA_DIR / 'training' / 'splits.json'
with open(splits_path, 'r') as f:
    splits = json.load(f)

for split_name in ['train', 'test']:
    data = splits[split_name]
    sims = {'SUPPORTED': [], 'INSUFFICIENT': []}
    for item in data:
        claim_emb = np.array(item['features'][:384])
        evidence_emb = np.array(item['features'][384:768])
        sim = float(np.dot(claim_emb, evidence_emb) / (np.linalg.norm(claim_emb) * np.linalg.norm(evidence_emb)))
        sims[item['label']].append(sim)
    
    print(f'\n{split_name} split:')
    for label, values in sims.items():
        if values:
            print(f'  {label}: mean={np.mean(values):.3f}, std={np.std(values):.3f}, min={np.min(values):.3f}, max={np.max(values):.3f}')
