# Contract: Claim Export Format

**Feature**: [spec.md](spec.md)  
**Date**: 2026-09-05  
**Status**: Draft

## Purpose

Define the JSONL format for per-claim records exported from the UQ pipeline for offline abstention analysis.

## Format

Each line in `data/runs/claims.jsonl` is a JSON object representing one claim from one pipeline run.

### Required Fields

```json
{
  "claim_id": "C1",
  "question_id": "M1",
  "support_probability": 0.92,
  "conformal_set": ["SUPPORTED"],
  "is_correct": true,
  "perturbation_type": "clean",
  "pipeline_mode": "full",
  "run_artifact_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Field Definitions

| Field | Type | Constraints |
|-------|------|-------------|
| `claim_id` | string | Non-empty, unique within a run |
| `question_id` | string | Non-empty, matches an entry in the test dataset |
| `support_probability` | float | `[0.0, 1.0]` |
| `conformal_set` | array[string] | Non-empty, each element in `{"SUPPORTED", "REFUTED", "INSUFFICIENT"}` |
| `is_correct` | boolean | Ground-truth label |
| `perturbation_type` | enum | `"clean"` or `"adversarial"` |
| `pipeline_mode` | enum | `"full"` or `"abstention_suppressed"` |
| `run_artifact_id` | string | UUID referencing a run artifact in `data/runs/` |

## Producer

`backend/server/modules/output/answer.py` — `AnswerComposer` or a new `ClaimExporter` module.

## Consumer

`scripts/risk_coverage.py` — reads `data/runs/claims.jsonl` to generate risk-coverage curves and ablation comparisons.

## Validation

- JSONL parser MUST reject malformed lines and report line number.
- `is_correct` MUST be annotated before analysis; if missing, the record MUST be excluded with a warning.
- `perturbation_type` and `pipeline_mode` MUST be populated by the test harness, not by the production pipeline.
