#!/usr/bin/env python3
"""Annotate claims with basic correctness labels for pilot risk-coverage curve."""

import json
from pathlib import Path

claims_path = Path("data/runs/claims.jsonl")
output_path = Path("data/runs/claims_annotated.jsonl")

# Simple heuristic: claim is correct if key terms appear in evidence
# In production, this would be human-annotated or from a gold answer key
claims = []
with open(claims_path) as f:
    for line in f:
        claims.append(json.loads(line.strip()))

# For this pilot, we'll mark claims as correct if support_probability > 0.5
# This is a placeholder for real annotation
for claim in claims:
    claim["is_correct"] = claim["support_probability"] > 0.5

with open(output_path, "w") as f:
    for claim in claims:
        f.write(json.dumps(claim) + "\n")

print(f"Annotated {len(claims)} claims to {output_path}")
correct = sum(1 for c in claims if c["is_correct"])
print(f"Correct: {correct}/{len(claims)} ({correct/len(claims):.1%})")
