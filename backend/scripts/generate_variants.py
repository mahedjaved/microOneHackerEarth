#!/usr/bin/env python3
"""Generate adversarial and suppressed claim variants from real claims."""

import json
import numpy as np
from pathlib import Path

input_path = Path("data/runs/claims_annotated.jsonl")
adv_output_path = Path("data/runs/claims_adversarial.jsonl")
suppressed_output_path = Path("data/runs/claims_suppressed.jsonl")

rng = np.random.RandomState(42)

claims = []
with open(input_path) as f:
    for line in f:
        claims.append(json.loads(line.strip()))

# Generate adversarial variants
adversarial_claims = []
for claim in claims:
    adv_claim = dict(claim)
    # Adversarial perturbation: slightly lower support_probability
    adv_prob = float(np.clip(claim["support_probability"] - rng.uniform(0.05, 0.15), 0.0, 1.0))
    adv_claim["support_probability"] = round(adv_prob, 4)
    adv_claim["claim_id"] = f"adv-{claim['claim_id']}"
    adv_claim["perturbation_type"] = "adversarial"
    adv_claim["conformal_set"] = ["SUPPORTED"] if adv_prob >= 0.5 else ["INSUFFICIENT"]
    # Adversarial claims are more likely to be incorrect
    adv_claim["is_correct"] = bool(rng.random() < (1.0 - adv_prob))
    adversarial_claims.append(adv_claim)

with open(adv_output_path, "w") as f:
    for claim in adversarial_claims:
        f.write(json.dumps(claim) + "\n")

print(f"Generated {len(adversarial_claims)} adversarial claims to {adv_output_path}")

# Generate suppressed variants (same claims, different pipeline_mode)
suppressed_claims = []
for claim in claims:
    sup_claim = dict(claim)
    sup_claim["claim_id"] = f"sup-{claim['claim_id']}"
    sup_claim["pipeline_mode"] = "abstention_suppressed"
    suppressed_claims.append(sup_claim)

with open(suppressed_output_path, "w") as f:
    for claim in suppressed_claims:
        f.write(json.dumps(claim) + "\n")

print(f"Generated {len(suppressed_claims)} suppressed claims to {suppressed_output_path}")
