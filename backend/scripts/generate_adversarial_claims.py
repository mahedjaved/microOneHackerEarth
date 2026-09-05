#!/usr/bin/env python3
"""Generate synthetic adversarial claims for perturbation comparison."""

import json
import numpy as np
from pathlib import Path

input_path = Path("data/runs/claims.jsonl")
output_path = Path("data/runs/claims_adversarial.jsonl")

rng = np.random.RandomState(123)

claims = []
with open(input_path) as f:
    for line in f:
        claim = json.loads(line.strip())
        # Adversarial perturbation: slightly lower support_probability
        # to simulate perturbation affecting confidence
        adv_prob = float(np.clip(claim["support_probability"] - rng.uniform(0.05, 0.15), 0.0, 1.0))
        # Adversarial claims are more likely to be incorrect
        adv_correct = bool(rng.random() < (1.0 - adv_prob))
        
        claim["claim_id"] = f"adv-{claim['claim_id']}"
        claim["support_probability"] = round(adv_prob, 4)
        claim["is_correct"] = adv_correct
        claim["perturbation_type"] = "adversarial"
        claim["conformal_set"] = ["SUPPORTED"] if adv_prob >= 0.5 else ["INSUFFICIENT"]
        claims.append(claim)

with open(output_path, "w") as f:
    for claim in claims:
        f.write(json.dumps(claim) + "\n")

print(f"Generated {len(claims)} adversarial claims to {output_path}")
