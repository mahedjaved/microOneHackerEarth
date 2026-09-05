# Research: abstention-measurement

**Feature**: [spec.md](spec.md)  
**Date**: 2026-09-05  
**Status**: Complete — all unknowns resolved

## Research Tasks

### R1 — Risk-coverage curve methodology

**Question**: How should the risk-coverage curve be computed, and what does AUC mean in this context?

**Decision**: Use the standard selective-risk formulation from conformal prediction literature. For each threshold `t` in `[0, 1]`, define the answered set as claims with `support_probability >= t`. Coverage = `|answered| / |total|`. Risk = `1 - accuracy` among answered claims. AUC is computed via trapezoidal integration over the sorted threshold sweep.

**Rationale**: This is the same metric used by MedAbstain and related work. It directly answers "if I only answer the claims I'm most confident about, how accurate am I?" without requiring any new methodology.

**Alternatives considered**:
- Expected Calibration Error (ECE): rejected because it bins by confidence rather than sweeping a decision threshold; it measures calibration, not the abstention-accuracy tradeoff.
- Precision-recall curve: rejected because precision/recall are classification-oriented and the system produces graded probabilities, not binary classifications.
- Brier score: rejected because it is a proper scoring rule, not a risk-coverage tradeoff curve.

---

### R2 — Adversarial perturbation design

**Question**: How should clean vs. adversarial question pairs be constructed?

**Decision**: Use the existing `data/corpus/adversarial/adversarial_cases.jsonl` as the perturbation source. Each case already contains `expected_conformal_set` and `expected_abstention_reason`. For the perturbation comparison, create a clean version (original question) and an adversarial version (same question with a semantically equivalent but lexically perturbed phrasing). The perturbation must preserve medical meaning while changing surface form enough to potentially affect retrieval or generation.

**Rationale**: The adversarial corpus is already validated, hand-built, and predates this feature. Reusing it avoids introducing new ethical-review burden and ensures the perturbation is synthetic and controlled.

**Alternatives considered**:
- LLM-generated paraphrases: rejected because they introduce model-dependent noise and are not deterministic.
- Synonym replacement: rejected because medical terminology requires domain-aware substitution to preserve meaning.
- Human-authored pairs: rejected due to time constraints; existing corpus is sufficient for pilot.

---

### R3 — Explicit abstention ablation design

**Question**: How can the effect of explicit doubt-certificate output be isolated without changing other components?

**Decision**: Add a boolean flag `UQ_SUPPRESS_DOUBT_CERTIFICATE` to `backend/server/config.py`. When `True`, the pipeline runs the full claim-verification and conformal-prediction path but replaces the `DoubtCertificate` with a generic "I don't know" response and sets `doubt_certificate=None` in the API response. All other components (retrieval, verifier, conformal predictor, EAV controller) remain identical.

**Rationale**: This isolates the abstention-output mechanism from the abstention-decision mechanism. The comparison then answers: does making abstention explicit and structured change user-facing behavior, compared to suppressing that explicitness?

**Alternatives considered**:
- Suppress the entire UQ pipeline: rejected because it would conflate abstention output with retrieval/verification quality.
- Suppress only the conformal set: rejected because the conformal set is the decision mechanism, not the output mechanism.
- Run two different models: rejected because it introduces model variance as a confound.

---

### R4 — Calibration repair prerequisites

**Question**: What must be true about the live pipeline before any conference artifacts are generated?

**Decision**: The following conditions must hold, verified by automated test:
1. `backend/server/modules/query_handlers.py` calls `compute_support_probability()` from `bayesian_fusion.py` at the claim-verification step.
2. `ConformalPredictor` is initialized via `from_quantile()` and `predict_set_from_probs()` is called at runtime.
3. The calibration set used to compute `conformal_quantile.json` includes the adversarial cases from `data/corpus/adversarial/adversarial_cases.jsonl`, or the limitation is explicitly documented.

**Rationale**: A risk-coverage curve computed on an under-confident or broken verifier measures noise, not abstention quality. The Bayesian refactor and conformal wiring are prerequisites, not optional enhancements.

**Alternatives considered**:
- Generate artifacts anyway and label them "pilot": rejected because a pilot on broken calibration is not a pilot, it's a misleading artifact.
- Wait for full Bayesian refactor: rejected because the conference deadline is 48 hours away; the existing `max(probs)` path can be replaced with the already-implemented `compute_support_probability()` in one focused edit.

---

### R5 — Per-claim export format

**Question**: What fields must each claim record contain to support all three user stories?

**Decision**: Each `ClaimRecord` must contain:
- `claim_id`: stable identifier within a run
- `question_id`: links to test dataset entry
- `support_probability`: float from verifier/calibrator
- `conformal_set`: list of labels from conformal predictor
- `is_correct`: bool, ground-truth label (manual annotation acceptable for pilot)
- `perturbation_type`: enum `clean` | `adversarial`
- `pipeline_mode`: enum `full` | `abstention_suppressed`
- `run_artifact_id`: links to full trajectory artifact

**Rationale**: These fields are the minimum set required to compute risk-coverage curves, compare perturbation effects, and run the abstention ablation. They map directly to existing schema fields where available.

**Alternatives considered**:
- Include full passage text: rejected because it bloats the artifact and is not needed for curve computation.
- Include LLM-generated correctness label: rejected because it introduces circularity; ground truth must be human-annotated or from a gold answer key.

---

## Decisions Summary

| Decision | Chosen Approach | Rejected Alternatives | Rationale |
|----------|----------------|----------------------|-----------|
| Risk-coverage metric | Selective risk vs. coverage sweep | ECE, Brier score, precision-recall | Directly measures abstention-accuracy tradeoff |
| Adversarial pairs | Reuse `adversarial_cases.jsonl` | LLM paraphrases, synonym swap, human-authored | Existing, validated, synthetic, time-efficient |
| Abstention ablation | `UQ_SUPPRESS_DOUBT_CERTIFICATE` flag | Suppress full pipeline, suppress conformal set, different model | Isolates output mechanism from decision mechanism |
| Calibration prerequisite | Automated test for Bayesian fusion + conformal wiring | Generate anyway, wait for full refactor | Broken calibration produces misleading curves |
| Claim export format | Minimal JSONL with 8 fields | Full passage text, LLM labels | Sufficient for all analyses, minimal bloat |
