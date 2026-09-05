# Feature Specification: abstention-measurement

**Feature Branch**: `006-abstention-measurement`

**Created**: 2026-09-05

**Status**: Draft

**Input**: User description: "I think this is our ticket, if my work can fill in this gap mentioned in the paper 'Knowing when to abstain' I can win this easily! But I am not sure how I can improve my work to fill this gap"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Measure abstention quality with risk-coverage curves (Priority: P1)

As a conference reviewer, I want to see a risk-coverage curve that demonstrates the system's confidence scores actually track correctness, so that I can verify the abstention mechanism is principled rather than arbitrary.

**Why this priority**: This is the single artifact that turns "we have a doubt certificate" into "we measured that doubt correlates with error." Without it, the abstention claim is architectural assertion; with it, it's evidence.

**Independent Test**: Run the system on a labeled held-out set, sweep the confidence threshold, plot coverage vs. risk, and report the area under the curve. This can be demonstrated with one PNG and one summary number.

**Acceptance Scenarios**:

1. **Given** a set of claims with ground-truth correctness labels and support_probability scores, **When** I sweep the abstention threshold from 0.0 to 1.0, **Then** the risk among answered claims should decrease as coverage decreases.
2. **Given** the same claims, **When** I compute the area under the risk-coverage curve, **Then** the AUC is reported with a confidence interval and sample size.
3. **Given** a curve that is flat or noisy, **When** I present it at the conference, **Then** I explicitly label it as a calibration failure mode rather than hiding it.

---

### User Story 2 - Compare abstention under clean vs. adversarial perturbation (Priority: P2)

As a conference reviewer, I want to see whether the system's abstention behavior is stable under input perturbation, so that I can distinguish genuine uncertainty from over-sensitivity to surface form.

**Why this priority**: MedAbstain's headline finding is that explicit abstention options change behavior more than adversarial perturbation does. Replicating that comparison on our own architecture shows we understand the distinction and can measure it.

**Independent Test**: Run the same questions through clean and adversarially perturbed versions, compare abstention rates and doubt-certificate rates, and report whether the shift is larger for perturbation or for the explicit abstention mechanism.

**Acceptance Scenarios**:

1. **Given** a set of clean medical questions, **When** I run them through the UQ pipeline, **Then** I record abstention rate, doubt-certificate rate, and average support_probability.
2. **Given** adversarially perturbed versions of the same questions, **When** I run them through the same pipeline, **Then** I can compare the abstention shift against the clean baseline.
3. **Given** both result sets, **When** I present the comparison, **Then** I report whether the explicit doubt-certificate output or the input perturbation had the larger effect on abstention behavior.

---

### User Story 3 - Ablate the explicit abstention option (Priority: P2)

As a conference reviewer, I want to see an ablation that isolates the effect of the explicit doubt-certificate output, so that I can understand whether making abstention visible actually improves the accuracy-safety tradeoff.

**Why this priority**: This is the cleanest causal claim available: does the architecture component we added (explicit abstention) change behavior in a measurable way? It turns "we built a safety mechanism" into "we measured that our safety mechanism works."

**Independent Test**: Run two pipeline configurations on the same questions: one with doubt-certificate output enabled, one with it suppressed but all other components identical. Compare accuracy, abstention rate, and safety-detection rate.

**Acceptance Scenarios**:

1. **Given** the full UQ-RAG pipeline with doubt certificates enabled, **When** I run a labeled test set, **Then** I record accuracy, abstention rate, and safety-detection rate.
2. **Given** the same pipeline with doubt-certificate output suppressed, **When** I run the identical test set, **Then** I can compare the two configurations on the same metrics.
3. **Given** both result sets, **When** I report the ablation, **Then** I state whether explicit abstention improved, degraded, or did not change the accuracy-safety tradeoff, with effect size.

---

### User Story 4 - Repair calibration before conference (Priority: P1)

As a conference reviewer, I want the underlying confidence signal to be calibrated before I interpret any risk-coverage curve, so that I can trust the abstention experiments are not measuring noise.

**Why this priority**: A risk-coverage curve computed on an under-confident verifier will look bad regardless of framework quality. The log-odds fusion and richer calibration data already identified in `specs/001-bayesian-evidence-fusion/` are prerequisites for credible abstention measurement.

**Independent Test**: Verify that `query_handlers.py:305` uses `compute_support_probability()` instead of `max(probs)`, that the conformal predictor is wired into the live pipeline, and that calibration-set accuracy is above baseline before generating any conference artifacts.

**Acceptance Scenarios**:

1. **Given** the live pipeline, **When** I inspect the claim-verification path, **Then** it uses Bayesian log-odds fusion rather than ad-hoc mean/max combination.
2. **Given** the conformal predictor, **When** I inspect the initialization, **Then** it is fitted from saved quantile and `predict_set_from_probs()` is called at runtime.
3. **Given** a calibration set, **When** I evaluate predicted support probabilities against ground truth, **Then** the Brier score and ECE improve over the legacy `max(probs)` path.

---

### Edge Cases

- What happens when the calibration set is too small to produce a stable quantile? The system MUST report the calibration sample size and abstain from displaying percentages when the artifact is missing or stale.
- How does the system handle a question where every retrieved passage is adversarially perturbed but topically similar? The abstention mechanism MUST not collapse to always-answer or always-abstain; both extremes are failure modes.
- What happens when the explicit-abstention ablation is run with `UQ_USE_BAYESIAN_FUSION=0`? The legacy path MUST be tested separately so the ablation isolates the abstention mechanism from the fusion mechanism.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST export per-claim records containing `support_probability`, `conformal_set`, `is_correct`, `run_artifact_id`, and `question_id` for offline analysis.
- **FR-002**: System MUST compute a risk-coverage curve by sweeping a confidence threshold across the exported claim set and plotting coverage against error rate among answered claims.
- **FR-003**: System MUST report area under the risk-coverage curve with bootstrap confidence intervals and the number of claims used.
- **FR-004**: System MUST support running the same question set through two pipeline configurations (abstention enabled vs. suppressed) and produce comparable per-question metrics.
- **FR-005**: System MUST include adversarial perturbation variants of a held-out question subset and record whether abstention behavior shifts more under perturbation or under the explicit abstention mechanism.
- **FR-006**: System MUST validate that the live claim-verification path uses `compute_support_probability()` from `bayesian_fusion.py` rather than `max(probs)` before any conference artifacts are generated.
- **FR-007**: System MUST record calibration metadata (Brier score, ECE, sample size) alongside every risk-coverage curve so reviewers can assess signal quality.
- **FR-008**: System MUST treat missing or stale calibration artifacts as a fail-closed condition: display `uncalibrated` and abstain rather than showing false precision.

### Key Entities

- **ClaimRecord**: A per-claim evidence packet containing `claim_id`, `question_id`, `support_probability`, `conformal_set`, `is_correct`, `perturbation_type` (clean / adversarial), `pipeline_mode` (full / abstention-suppressed), and `run_artifact_id`.
- **RiskCoverageArtifact**: A curve export containing `thresholds`, `coverage`, `risk`, `auc`, `auc_ci_low`, `auc_ci_high`, `n_claims`, `calibration_brier`, `calibration_ece`, and `generated_at`.
- **AblationResult**: A pairwise comparison between two pipeline configurations on the same question set, containing `config_a`, `config_b`, `accuracy_delta`, `abstention_rate_delta`, `safety_detection_delta`, and `effect_size`.
- **CalibrationArtifact**: Versioned metadata recording `verifier_model`, `calibrator_type`, `conformal_method`, `alpha`, `feature_schema_version`, `corpus_family`, `quantile`, `brier_score`, `ece`, and `sample_size`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A risk-coverage curve is generated from at least 30 labeled claims drawn from the held-out test set, with AUC reported to two decimal places and bootstrap 95% CI.
- **SC-002**: The abstention ablation compares two pipeline configurations on the same 30+ question set and reports accuracy, abstention rate, and safety-detection rate with effect size.
- **SC-003**: The adversarial perturbation comparison uses at least 10 adversarially modified questions and reports whether abstention shift is larger for perturbation or for the explicit abstention mechanism.
- **SC-004**: Before any curve or ablation is generated, the live pipeline uses `compute_support_probability()` and a properly wired conformal predictor, verified by automated test.
- **SC-005**: Calibration metadata (Brier score, ECE, sample size) is included in every exported artifact so reviewers can assess whether the confidence signal is trustworthy.
- **SC-006**: All conference-facing artifacts are reproducible from a clean clone using documented commands, with no manual post-processing of JSON files.

## Assumptions

- The held-out test set includes ground-truth correctness labels for at least 30 claims. If labels are missing, manual annotation is acceptable for the pilot curve but must be documented with annotator agreement.
- The adversarial cases in `data/corpus/adversarial/adversarial_cases.jsonl` are suitable as perturbation variants and do not require additional ethical review because they are synthetic.
- The conference deadline is 2026-09-07, so the MVP is a pilot curve on ~30–50 claims rather than a full benchmark. A larger evaluation is planned as post-conference work.
- The existing `run_artifact_id` field is populated on non-safety queries, which is required to join claim records with correctness labels after the fact.
- Judges and reviewers will accept a stated next-step ("full benchmark after conference") if the pilot curve is honest about sample size and limitations.
