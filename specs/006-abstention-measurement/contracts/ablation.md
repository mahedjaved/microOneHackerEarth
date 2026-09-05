# Contract: Ablation Result Format

**Feature**: [spec.md](spec.md)  
**Date**: 2026-09-05  
**Status**: Draft

## Purpose

Define the JSON format for pairwise ablation comparisons between pipeline configurations.

## Format

```json
{
  "config_a": "full",
  "config_b": "abstention_suppressed",
  "accuracy_delta": 0.05,
  "abstention_rate_delta": -0.12,
  "safety_detection_delta": 0.0,
  "effect_size": 0.35,
  "n_questions": 42,
  "generated_at": "2026-09-05T12:00:00Z"
}
```

## Field Definitions

| Field | Type | Constraints |
|-------|------|-------------|
| `config_a` | string | Name of first configuration |
| `config_b` | string | Name of second configuration; MUST differ from `config_a` |
| `accuracy_delta` | float | `accuracy(config_a) - accuracy(config_b)` |
| `abstention_rate_delta` | float | `abstention_rate(config_a) - abstention_rate(config_b)` |
| `safety_detection_delta` | float | `safety_detection(config_a) - safety_detection(config_b)` |
| `effect_size` | float | Cohen's d or rank-biserial correlation; sign indicates direction |
| `n_questions` | integer | `>= 1` |
| `generated_at` | ISO 8601 string | Timestamp of artifact creation |

## Producer

`scripts/risk_coverage.py` or a dedicated ablation script.

## Consumer

Conference paper results table, `submission/unit-tests/report.md`.

## Validation

- `config_a` and `config_b` MUST be different.
- `n_questions` MUST match the number of unique `question_id` values in the underlying `ClaimRecord` set.
- Positive `accuracy_delta` means `config_a` is more accurate; negative means `config_b` is more accurate.
