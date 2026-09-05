#!/usr/bin/env python3
"""Generate synthetic claims for pilot risk-coverage curve."""

import json
import numpy as np
from pathlib import Path

output_path = Path("data/runs/claims.jsonl")
output_path.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.RandomState(42)

# Generate 50 synthetic claims with varying support_probability and correctness
# Higher support_probability should correlate with is_correct=True
claims = []
for i in range(50):
    # Create a correlation: higher support_probability -> more likely correct
    base_prob = rng.beta(2, 2)  # base probability
    support_probability = float(np.clip(base_prob + rng.normal(0, 0.1), 0.0, 1.0))
    is_correct = bool(rng.random() < support_probability)  # probabilistic correctness
    
    claim = {
        "claim_id": f"synthetic-{i+1}",
        "question_id": f"q-{(i % 10) + 1}",
        "support_probability": round(support_probability, 4),
        "conformal_set": ["SUPPORTED"] if support_probability >= 0.5 else ["INSUFFICIENT"],
        "is_correct": is_correct,
        "perturbation_type": "clean",
        "pipeline_mode": "full",
        "run_artifact_id": f"synthetic-run-{(i % 5) + 1}",
    }
    claims.append(claim)

with open(output_path, "w") as f:
    for claim in claims:
        f.write(json.dumps(claim) + "\n")

print(f"Generated {len(claims)} synthetic claims to {output_path}")
