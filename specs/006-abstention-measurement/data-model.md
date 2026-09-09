# Data Model: abstention-measurement

**Feature**: [spec.md](spec.md)  
**Date**: 2026-09-05  
**Status**: Draft

## Entities

### ClaimRecord

A per-claim evidence packet exported from a single pipeline run.

| Field | Type | Description |
|-------|------|-------------|
| `claim_id` | string | Stable identifier within a run (e.g., `C1`, `C2`) |
| `question_id` | string | Links to test dataset entry (e.g., `M1`, `S2`, `A3`) |
| `support_probability` | float | Post-calibration probability assigned to `SUPPORTED` by the verifier |
| `conformal_set` | list[string] | Labels retained by conformal predictor at declared coverage target |
| `is_correct` | bool | Ground-truth correctness label (human-annotated or gold answer key) |
| `perturbation_type` | enum | `clean` or `adversarial` — indicates whether the question was perturbed |
| `pipeline_mode` | enum | `full` or `abstention_suppressed` — indicates which pipeline configuration produced this claim |
| `run_artifact_id` | string | Links to full trajectory artifact in `data/runs/` |

**Validation rules**:
- `support_probability` MUST be in `[0.0, 1.0]`
- `conformal_set` MUST be non-empty and contain only valid labels (`SUPPORTED`, `REFUTED`, `INSUFFICIENT`)
- `perturbation_type` and `pipeline_mode` MUST be one of the declared enum values
- `run_artifact_id` MUST reference an existing run artifact

**State transitions**: N/A — this is an immutable export record.

---

### RiskCoverageArtifact

A curve export containing the results of sweeping the abstention threshold.

| Field | Type | Description |
|-------|------|-------------|
| `thresholds` | list[float] | Sorted confidence thresholds from 0.0 to 1.0 |
| `coverage` | list[float] | Fraction of claims answered at each threshold |
| `risk` | list[float] | Error rate among answered claims at each threshold |
| `auc` | float | Area under the risk-coverage curve (lower is better) |
| `auc_ci_low` | float | Bootstrap 95% CI lower bound |
| `auc_ci_high` | float | Bootstrap 95% CI upper bound |
| `n_claims` | int | Number of claims used to compute the curve |
| `calibration_brier` | float | Brier score of the verifier on the calibration set |
| `calibration_ece` | float | Expected Calibration Error of the verifier |
| `generated_at` | ISO 8601 string | Timestamp of artifact generation |

**Validation rules**:
- `thresholds`, `coverage`, and `risk` MUST have equal length
- `auc` MUST be in `[0.0, 1.0]`
- `auc_ci_low` <= `auc` <= `auc_ci_high`
- `n_claims` MUST be >= 30 for conference-ready artifacts
- `calibration_brier` and `calibration_ece` MUST be present; if verifier is uncalibrated, both MUST be `null` and the artifact MUST include a warning

**State transitions**: N/A — this is a computed export.

---

### AblationResult

A pairwise comparison between two pipeline configurations on the same question set.

| Field | Type | Description |
|-------|------|-------------|
| `config_a` | string | Name of first configuration (e.g., `full`) |
| `config_b` | string | Name of second configuration (e.g., `abstention_suppressed`) |
| `accuracy_delta` | float | `accuracy(config_a) - accuracy(config_b)` |
| `abstention_rate_delta` | float | `abstention_rate(config_a) - abstention_rate(config_b)` |
| `safety_detection_delta` | float | `safety_detection(config_a) - safety_detection(config_b)` |
| `effect_size` | float | Cohen's d or rank-biserial correlation |
| `n_questions` | int | Number of questions in the comparison |
| `generated_at` | ISO 8601 string | Timestamp of artifact generation |

**Validation rules**:
- `config_a` and `config_b` MUST be different
- `n_questions` MUST be >= 30 for conference-ready artifacts
- `effect_size` MUST be reported with sign indicating direction

**State transitions**: N/A — this is a computed comparison.

---

### CalibrationArtifact

Versioned metadata recording the calibration state of the verifier.

| Field | Type | Description |
|-------|------|-------------|
| `calibration_id` | string | Unique identifier (e.g., `calibration-v1`) |
| `verifier_model` | string | Model identifier (e.g., `random-forest-v1`) |
| `calibrator_type` | string | Calibration method (e.g., `isotonic`) |
| `conformal_method` | string | Conformal method (e.g., `LAC`) |
| `alpha` | float | Target miscoverage rate (e.g., `0.10`) |
| `feature_schema_version` | string | Schema version for feature vector |
| `corpus_family` | string | Corpus identifier (e.g., `mirage-pubmed`) |
| `quantile` | float | Saved conformal quantile |
| `brier_score` | float | Brier score on calibration set (or `null` if unavailable) |
| `ece` | float | Expected Calibration Error (or `null` if unavailable) |
| `sample_size` | int | Number of examples in calibration set |
| `generated_at` | ISO 8601 string | Timestamp of artifact creation |

**Validation rules**:
- `alpha` MUST be in `(0.0, 1.0)`
- `quantile` MUST be in `[0.0, 1.0]`
- `sample_size` MUST be > 0
- If `brier_score` or `ece` is `null`, the artifact MUST include a `calibration_warning` field explaining why

**State transitions**: N/A — this is a versioned metadata record.

---

## Entity Relationships

```text
ClaimRecord ──► CalibrationArtifact  (via calibration_id / verifier_model)
ClaimRecord ──► RiskCoverageArtifact (aggregated into)
ClaimRecord ──► AblationResult       (grouped by pipeline_mode)
ClaimRecord ──► RunArtifact          (via run_artifact_id)
```

- A `CalibrationArtifact` is produced once during verifier training and referenced by all `ClaimRecord`s generated under that calibration.
- A `RiskCoverageArtifact` is computed from a set of `ClaimRecord`s sharing the same `calibration_id` and `perturbation_type`.
- An `AblationResult` compares two `pipeline_mode` groups within the same `question_id` set.
