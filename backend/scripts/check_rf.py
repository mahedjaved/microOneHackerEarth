import json
from pathlib import Path
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

DATA_DIR = Path('D:/PROJECTS/CLAUDE_CLI_AGENTS/HACKER_EARTH/HACKATHONS/microOneHackerEarth/data')
splits_path = DATA_DIR / 'training' / 'splits.json'
with open(splits_path, 'r') as f:
    splits = json.load(f)

def get_Xy(data):
    X = np.array([item['features'] for item in data])
    y = np.array([item['label'] for item in data])
    return X, y

X_train, y_train = get_Xy(splits['train'])
X_test, y_test = get_Xy(splits['test'])

print(f"Train shape: {X_train.shape}, Test shape: {X_test.shape}")
print(f"Train labels: {np.unique(y_train, return_counts=True)}")
print(f"Test labels: {np.unique(y_test, return_counts=True)}")

# Train RandomForest
rf = RandomForestClassifier(n_estimators=200, max_depth=None, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)

train_preds = rf.predict(X_train)
test_preds = rf.predict(X_test)

print(f"Train accuracy: {accuracy_score(y_train, train_preds):.3f}")
print(f"Test accuracy: {accuracy_score(y_test, test_preds):.3f}")

# Check feature importances
print(f"Feature importances: {rf.feature_importances_}")

# Check a few predictions
for i in range(10):
    print(f"Test {i}: pred={test_preds[i]}, label={y_test[i]}, features={X_test[i]}")
