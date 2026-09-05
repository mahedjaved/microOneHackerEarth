# Contract: Risk-Coverage Artifact Format

**Feature**: [spec.md](spec.md)  
**Date**: 2026-09-05  
**Status**: Draft

## Purpose

Define the JSON format for risk-coverage curve artifacts produced by `scripts/risk_coverage.py`.

## Format

```json
{
  "thresholds": [0.0, 0.02, 0.04, ..., 1.0],
  "coverage": [1.0, 0.98, 0.95, ..., 0.0],
  "risk": [0.35, 0.32, 0.28, ..., null],
  "auc": 0.12,
  "auc_ci_low": 0.08,
  "auc_ci_high": 0.17,
  "n_claims": 42,
  "calibration_brier": 0.08,
  "calibration_ece": 0.05,
  "generated_at": "2026-09-05T12:00:00Z",
  "calibration_warning": null
}
```

## Field Definitions

| Field | Type | Constraints |
|-------|------|-------------|
| `thresholds` | array[float] | Sorted ascending, length N |
| `coverage` | array[float] | Length N, each in `[0.0, 1.0]` |
| `risk` | array[float] | Length N, each in `[0.0, 1.0]` or `null` when no claims are answered |
| `auc` | float | `[0.0, 1.0]`; lower is better |
| `auc_ci_low` | float | `<= auc` |
| `auc_ci_high` | float | `>= auc` |
| `n_claims` | integer | `>= 1` |
| `calibration_brier` | float | `[0.0, 1.0]` or `null` |
| `calibration_ece` | float | `[0.0, 1.0]` or `null` |
| `generated_at` | ISO 8601 string | Timestamp of artifact creation |
| `calibration_warning` | string | Non-null only when `brier_score` or `ece` is `null` |

## Producer

`scripts/risk_coverage.py`

## Consumer

Conference paper figures, `submission/unit-tests/report.md`, HTML report generator.

## Validation

- `thresholds`, `coverage`, and `risk` MUST have equal length.
- `auc_ci_low` <= `auc` <= `auc_ci_high`.
- If `calibration_brier` or `calibration_ece` is `null`, `calibration_warning` MUST explain why (e.g., "calibration set too small for reliable Brier score").
