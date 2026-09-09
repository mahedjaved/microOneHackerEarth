#!/usr/bin/env python3
"""Test the retrained verifier on D1/D4/D6 to check if numeric containment fixes over-abstention.

RESULT: The numeric_containment feature has 0.0 importance in the trained model.
The RandomForest ignores it because the training data doesn't have enough variation
in this feature. This confirms the critic's diagnosis: the verifier needs NLI-based
features, not just additional shallow features.

This script is kept as documentation of the attempted fix and its limitation.
"""

import sys
import numpy as np
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from server.modules.verifier.classifier import ThreeWayVerifier
from server.modules.verifier.calibration import ProbabilityCalibrator
from sentence_transformers import SentenceTransformer

# Load models
models_dir = Path(__file__).parent.parent.parent / "data" / "models"
verifier_path = str(models_dir / "verifier_gp.joblib")
calibrator_path = str(models_dir / "calibrator.joblib")

verifier = ThreeWayVerifier(model_path=verifier_path)
calibrator = ProbabilityCalibrator.load(calibrator_path)

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
verifier.embedding_model = embedding_model

# Test cases from the actual PDF
test_cases = [
    {
        "id": "D1",
        "claim": "The maximum single adult dose is 650mg.",
        "evidence": "The usual dose of aspirin for adults is 325-650 mg every 4 hours as needed.",
        "expected": "SUPPORTED",
        "reason": "650mg is the upper bound of the 325-650mg range stated in the document"
    },
    {
        "id": "D4",
        "claim": "The maximum daily dose is 4,000 mg.",
        "evidence": "Do not exceed 4,000 mg in 24 hours.",
        "expected": "SUPPORTED",
        "reason": "Document explicitly states 4,000mg daily limit"
    },
    {
        "id": "D6",
        "claim": "Aspirin should not be given to children under 16 years old.",
        "evidence": "Aspirin should not be given to children under 16 years old due to the risk of Reye syndrome.",
        "expected": "SUPPORTED",
        "reason": "Verbatim match with document"
    },
]

print("=" * 70)
print("TESTING NUMERIC CONTAINMENT FEATURE — POST-MORTEM")
print("=" * 70)
print()
print("FINDING: numeric_containment feature has 0.0 importance in trained model.")
print("The RandomForest ignores it because training data lacks variation.")
print("This confirms: shallow features cannot fix the entailment gap.")
print()

for case in test_cases:
    result = verifier.predict_text(case["claim"], case["evidence"])
    raw_probs = np.array([[result.probabilities.get("SUPPORTED", 0.0), 
                          result.probabilities.get("REFUTED", 0.0), 
                          result.probabilities.get("INSUFFICIENT", 0.0)]])
    calibrated_probs = calibrator.transform(raw_probs)[0]
    
    prob_dict = {
        "SUPPORTED": float(calibrated_probs[0]),
        "REFUTED": float(calibrated_probs[1]),
        "INSUFFICIENT": float(calibrated_probs[2]),
    }
    
    predicted = max(prob_dict, key=prob_dict.get)
    confidence = prob_dict[predicted]
    
    status = "✅ CORRECT" if predicted == case["expected"] else "❌ WRONG"
    
    print(f"{case['id']}: {case['reason']}")
    print(f"  Claim: {case['claim'][:60]}...")
    print(f"  Evidence: {case['evidence'][:60]}...")
    print(f"  Predicted: {predicted} ({confidence:.3f}) | Expected: {case['expected']} | {status}")
    print()

print("=" * 70)
print("CONCLUSION")
print("=" * 70)
print("The numeric containment feature does not fix the over-abstention problem")
print("because the model cannot learn from it without retraining on specifically")
print("crafted numeric entailment examples. The correct fix is NLI-based verification,")
print("as the critic recommended. This is documented as a post-conference roadmap item.")
