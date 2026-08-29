import json
from pathlib import Path
import numpy as np

DATA_DIR = Path('D:/PROJECTS/CLAUDE_CLI_AGENTS/HACKER_EARTH/HACKATHONS/microOneHackerEarth/data')
splits_path = DATA_DIR / 'training' / 'splits.json'
with open(splits_path, 'r') as f:
    splits = json.load(f)

for split_name in ['train', 'calib', 'val', 'test']:
    data = splits[split_name]
    labels = [item['label'] for item in data]
    print(f'{split_name}: total={len(labels)}, SUPPORTED={labels.count("SUPPORTED")}, INSUFFICIENT={labels.count("INSUFFICIENT")}')
