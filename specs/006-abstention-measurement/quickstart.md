# Quickstart: abstention-measurement

**Feature**: [spec.md](spec.md)  
**Date**: 2026-09-05  
**Status**: Draft

## Prerequisites

- Backend unit tests pass: `cd backend && python -m pytest tests/ -v --tb=short`
- Prebuilt model artifacts present in `data/models/` (verifier, calibrator, conformal quantile)
- Python dependencies installed: `pip install matplotlib numpy`
- `backend/server/.env` exists with dummy keys (Pinecone/Groq degrade gracefully)

## Validation Scenarios

### Scenario 1: Export claim records from a clean run

**Setup**: Start backend with `UQ_SUPPRESS_DOUBT_CERTIFICATE=False`.

**Command**:
```powershell
cd backend
python scripts/test_e2e.py
```

**Expected outcome**: `data/runs/claims.jsonl` is created with one JSON object per claim. Each object contains all required fields: `claim_id`, `question_id`, `support_probability`, `conformal_set`, `is_correct`, `perturbation_type`, `pipeline_mode`, `run_artifact_id`.

**Pass criterion**: `claims.jsonl` contains at least 30 records with `is_correct` populated.

---

### Scenario 2: Generate risk-coverage curve

**Setup**: Ensure `claims.jsonl` exists with labeled claims.

**Command**:
```powershell
cd backend
python scripts/risk_coverage.py --input data/runs/claims.jsonl --output data/runs/risk_coverage.json
```

**Expected outcome**: `data/runs/risk_coverage.json` is created with `thresholds`, `coverage`, `risk`, `auc`, `auc_ci_low`, `auc_ci_high`, `n_claims`, `calibration_brier`, `calibration_ece`, `generated_at`.

**Pass criterion**: 
- `n_claims >= 30`
- `auc` is reported to two decimal places
- `auc_ci_low <= auc <= auc_ci_high`
- A PNG plot is generated at `data/runs/risk_coverage.png`

---

### Scenario 3: Run abstention ablation

**Setup**: Run the same question set twice — once with `UQ_SUPPRESS_DOUBT_CERTIFICATE=False`, once with `True`.

**Command**:
```powershell
# Run A: full pipeline
$env:UQ_SUPPRESS_DOUBT_CERTIFICATE="False"
python scripts/test_e2e.py --output data/runs/claims_full.jsonl

# Run B: suppressed pipeline
$env:UQ_SUPPRESS_DOUBT_CERTIFICATE="True"
python scripts/test_e2e.py --output data/runs/claims_suppressed.jsonl

# Compare
python scripts/risk_coverage.py --ablate data/runs/claims_full.jsonl data/runs/claims_suppressed.jsonl --output data/runs/ablation.json
```

**Expected outcome**: `data/runs/ablation.json` contains `config_a`, `config_b`, `accuracy_delta`, `abstention_rate_delta`, `safety_detection_delta`, `effect_size`, `n_questions`.

**Pass criterion**: `n_questions >= 30`; `effect_size` is reported with direction.

---

### Scenario 4: Verify calibration prerequisite

**Setup**: Inspect the live pipeline before generating any conference artifacts.

**Command**:
```powershell
cd backend
python -c "import ast; tree = ast.parse(open('server/modules/query_handlers.py').read()); print('max(probs)' in open('server/modules/query_handlers.py').read())"
```

**Expected outcome**: Prints `False`, confirming the legacy `max(probs)` path is no longer present in the claim-verification code path.

**Pass criterion**: The live pipeline uses `compute_support_probability()` from `bayesian_fusion.py` and `ConformalPredictor.predict_set_from_probs()` is called at runtime.

---

### Scenario 5: Adversarial perturbation comparison

**Setup**: Run clean and adversarial question pairs through the full pipeline.

**Command**:
```powershell
python scripts/risk_coverage.py --compare-clean-adversarial data/runs/claims.jsonl --output data/runs/perturbation_comparison.json
```

**Expected outcome**: `data/runs/perturbation_comparison.json` reports abstention rate and average `support_probability` for clean vs. adversarial questions.

**Pass criterion**: At least 10 adversarial questions are included; the report states whether abstention shift is larger for perturbation or for the explicit abstention mechanism.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `claims.jsonl` missing `is_correct` | Manually annotate or use gold answer key; see `specs/006-abstention-measurement/spec.md` Assumptions |
| `calibration_brier` is `null` | Calibration set is too small; document sample size and proceed with warning |
| `auc` is `null` | No claims meet the highest threshold; check for degenerate `support_probability` values |
| `n_claims < 30` | Expand test set or annotate more claims; pilot curve is acceptable if sample size is stated |
