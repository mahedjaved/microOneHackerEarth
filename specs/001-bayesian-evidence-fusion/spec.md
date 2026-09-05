# Feature Specification: Bayesian Evidence Fusion for UQ-RAG

**Feature Branch**: `001-bayesian-evidence-fusion`

**Created**: 2026-09-03

**Status**: Draft

**Input**: User description: "The current system isn't actually doing Bayesian inference. ThreeWayVerifier is a RandomForest with isotonic-calibrated output probabilities; ConformalPredictor is a frequentist coverage wrapper. The pipeline has the vocabulary (doubt certificates, conformal sets, 'uncertainty quantification') without the actual mechanism (priors, likelihood ratios, principled combination of multiple evidence pieces). Fix _compute_support_probability to use log-odds (naive-Bayes-style) fusion across evidence passages instead of mean() or max(). Give the verifier an explicit prior instead of asking a RandomForest to learn everything from 1,200 examples. Set the conformal quantile via expected loss, not by hand. Weight claims by relevance to the question, not just similarity to evidence."

## Clarifications

### Session 2026-09-04

- Q: Where does the labeled calibration set for the conformal quantile come from? → A: Create/curate the labeled set as part of this feature's scope.
- Q: What latency budget should the new log-odds evidence-fusion step meet per claim? → A: <5 ms per claim (regression check; current is effectively zero per-claim cost).
- Q: Does the new log-odds fusion change the DoubtCertificate schema? → A: Add new optional fields (`prior`, `combined_posterior`, `relevance_weighted` flag) without changing existing ones; existing consumers ignore them.
- Q: How should the conformal quantile cost ratio be configured? → A: Read from a config file or environment variable at startup, with 10:1 as the default; the resolved value MUST be recorded in run artifacts for auditability.
- Q: Is the Bayesian prior fixed or per-claim? → A: Fixed system-wide default (0.5) with a config-file override (e.g., `UQ_PRIOR`); per-claim or per-domain priors are out of scope for this iteration.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Honest accuracy reporting on the comparative study report (Priority: P1)

A reviewer (examiner, investor, or clinical advisor) opens `docs/comparative_study_report.html` and sees results that are internally consistent: the per-question table and the aggregate tables agree. The Accuracy-Suite Avg and Safety-Suite Avg columns reflect the actual questions that were run, not stale question IDs from an older dataset.

**Why this priority**: A report whose two tables on page 2 contradict each other is worse than a report with a lower honest number — the contradiction is caught in 30 seconds and destroys credibility. The current bug (`ACCURACY_SUITE_IDS = ["M1"..] in test_dataset.py` while the questions being run are D1–D6 from `test_dataset_enhanced.py`) produces a flat 0.00 accuracy column for every system, hiding the real spread entirely. The corrected picture — MedRAG 0.84, UQ-RAG 0.11, No-RAG 0.55 on accuracy — is the honest story the submission can defend.

**Independent Test**: Run the comparative study, then open the HTML report and check that the "Accuracy Suite Avg" column matches the average of the D1–D6 rows in the "Per-Question Results" table to two decimal places. Both should reflect the same underlying scores.

**Acceptance Scenarios**:

1. **Given** the comparative study has run on `suite=original` (18 questions), **When** `generate_report.py` produces the HTML, **Then** the Accuracy-Suite Avg column shows a non-zero value for at least one system.
2. **Given** the per-question scores in the run JSON, **When** a reviewer computes the mean of D1–D6 scores by hand, **Then** the generated Accuracy-Suite Avg matches that hand-computed mean.
3. **Given** a reviewer spot-checks the per-question table against the aggregate table, **When** they compare accuracy-related cells, **Then** no contradictions are found between the two tables.

---

### User Story 2 - Principled evidence combination across multiple passages (Priority: P1)

A UQ-RAG query that retrieves multiple evidence passages receives a support probability that reflects the actual evidential weight of each passage — not an ad-hoc average that lets one strong signal get cancelled by an irrelevant near-zero score, and not a max() that ignores genuine agreement.

**Why this priority**: This is the core scientific bug. The D1 case (Claim 1 vs. Passage 1: 0.501, Claim 1 vs. Passage 2: 0.000) demonstrates the problem: Passage 1 is real evidence in favor of the claim, Passage 2 is neutral, near-irrelevant evidence about children's dosing (not counter-evidence, just off-topic). A flat mean drags the good match down to 0.25; a max keeps it at 0.501. A Bayesian log-odds update treats Passage 2 as a near-uninformative likelihood ratio and keeps the posterior near the prior, which is the correct mathematical treatment. This same bug manifests as the `cross_source_conflict` proxy using shared negation words as a crude stand-in for genuine Bayesian conflict detection.

**Independent Test**: Construct a unit test with a known set of per-passage probabilities including one near-zero and one near-one value, and verify the combined output is closer to the informative (near-one) passage than a flat mean would be, but not artificially boosted above a max. The combined probability should match the closed-form log-odds calculation.

**Acceptance Scenarios**:

1. **Given** a claim with two supporting passages (0.8, 0.7) and a prior of 0.5, **When** the verifier computes support, **Then** the combined probability exceeds the max of the inputs (because two independent positive updates should reinforce).
2. **Given** a claim with one supporting passage (0.8) and one off-topic passage (0.01), **When** the verifier computes support, **Then** the combined probability is close to 0.8, not dragged down to ~0.4 (the arithmetic mean) and not artificially boosted to >0.8.
3. **Given** a claim with three passages (0.5, 0.5, 0.5) and a prior of 0.5, **When** the verifier computes support, **Then** the combined probability is exactly 0.5 (neutral evidence shouldn't move the prior).

---

### User Story 3 - Calibrated conformal abstention via expected-loss minimization (Priority: P2)

When the UQ-RAG verifier is uncertain about a claim, the system abstains (or downgrades) at a threshold chosen by minimizing expected loss under a stated cost ratio — not by curve-fitting a quantile against individual examples.

**Why this priority**: The current quantile was tuned by hand (0.0 → 0.2 → 0.5) against specific cases (D4, S4). A medical-safety framing (e.g., "a confidently-wrong answer costs 10× an unnecessary abstention") gives a defensible, reviewable number instead of a curve-fitted one. This is defense-in-depth on top of P1's evidence combination — the verifier still needs a threshold, and the threshold should be principled.

**Independent Test**: Given a labeled held-out set of (claim, passage, ground-truth-support) triples and a stated cost ratio (e.g., 10:1 for false-confidence vs. over-abstention), sweep quantile values and verify the chosen quantile minimizes expected loss on the held-out set. The chosen value should be reproducible from the inputs.

**Acceptance Scenarios**:

1. **Given** a labeled calibration set and a 10:1 cost ratio (confident-wrong : over-abstain), **When** the system picks a conformal quantile, **Then** the chosen value is the argmin of expected loss on the calibration set.
2. **Given** the chosen quantile is recorded, **When** a reviewer asks "why this value?", **Then** the reviewer can reproduce the expected-loss calculation from the calibration set and cost ratio.

---

### User Story 4 - Claim relevance weighting (Priority: P3)

A claim that is generic boilerplate ("Always consult a healthcare provider") contributes near-zero information to the support probability in either direction, rather than being pooled in as a near-zero SUPPORTED score that can bias the posterior.

**Why this priority**: This is a smaller-scale fix, but it directly addresses the "boilerplate problem" the expert flagged. The change is cheap (a relevance score against the question) and orthogonal to the log-odds fusion. It's P3 because the system functions correctly without it; with it, the system is more robust to generic safety boilerplate in the LLM's response.

**Independent Test**: Given a claim whose cosine similarity to the question is below a threshold (e.g., < 0.3), the verifier down-weights that claim's contribution to the combined posterior, so a single highly-generic claim cannot swing the result on its own.

**Acceptance Scenarios**:

1. **Given** a claim with low relevance to the question (cosine similarity < 0.3), **When** the verifier combines evidence, **Then** that claim's contribution is dampened (e.g., its likelihood ratio is pulled toward 1, making it near-uninformative).
2. **Given** a high-relevance claim plus a low-relevance claim, **When** the verifier combines evidence, **Then** the high-relevance claim dominates the posterior.

---

### Edge Cases

- **Empty evidence set**: What happens when zero passages are retrieved? The system should fall back to the prior (no evidence update, return prior probability).
- **All-passages-identical**: When all retrieved passages give the same score (e.g., all 0.5), the log-odds update should reduce to the prior unchanged, since neutral evidence shouldn't move the prior.
- **Numerical underflow**: When a per-passage probability is 0 or 1, the log-odds update could blow up. The implementation must clamp probabilities to [ε, 1-ε] before computing log-odds.
- **Contradictory evidence**: When two passages genuinely disagree (one strongly positive, one strongly negative), the posterior should land between them, reflecting genuine conflict — not collapse to one or the other.
- **Stale question IDs in reporting**: The `test_dataset.py` defines `ACCURACY_SUITE_IDS = ["M1"..]`, but the questions actually being run are D1–D6 from `test_dataset_enhanced.py`. The report must use the IDs from the dataset actually being executed, not the legacy constant.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST combine per-passage SUPPORTED probabilities using log-odds (naive-Bayes-style) addition over a stated prior, rather than arithmetic mean or max.
- **FR-002**: System MUST report the prior probability used for evidence combination, so reviewers can audit the choice.
- **FR-003**: System MUST clamp per-passage probabilities to [ε, 1−ε] (e.g., ε=1e-6) before computing log-odds, to prevent numerical underflow/overflow.
- **FR-004**: System MUST use `tests.comparative.test_dataset_enhanced` as the source of truth for suite membership in `generate_report.py`, not the legacy `tests.comparative.test_dataset`.
- **FR-005**: System MUST regenerate the comparative study report with the corrected suite mapping so the Accuracy-Suite Avg and Per-Question tables are internally consistent.
- **FR-006**: System MUST choose the conformal abstention quantile by minimizing expected loss on a labeled calibration set under a stated cost ratio, not by manual curve-fitting.
- **FR-007**: System MUST record the cost ratio used to pick the conformal quantile, so the choice is reproducible and reviewable.
- **FR-008**: System MUST down-weight low-relevance claims (e.g., cosine similarity to question < 0.3) in the evidence combination, so generic boilerplate cannot swing the posterior.
- **FR-009**: System MUST NOT silently average or max() per-passage probabilities anywhere in the claim-verification pipeline. (The only allowed combination is log-odds addition over a stated prior.)
- **FR-010**: System MUST preserve the existing `errored` flag and `conformal_set` output schema so existing downstream consumers (doubt certificates, report generator) continue to work.
- **FR-012**: System MUST add the following **optional** fields to the `DoubtCertificate` schema without renaming or removing any existing fields: `prior: float | None`, `combined_posterior: float | None`, `relevance_weighted: bool | None`. These fields MUST be populated when the new log-odds fusion is active, and MUST be `None` (or absent) when the legacy path is used. The schema version SHOULD be bumped if the spec convention requires it, but the change MUST be backwards-compatible (existing consumers that ignore unknown fields continue to work).
- **FR-013**: System MUST read the conformal quantile cost ratio (confident-wrong : over-abstain) from a configuration source at startup. The configuration source MUST be either an environment variable (e.g., `UQ_COST_RATIO`) or a config file (e.g., `backend/server/config.py` or a new YAML/TOML). The default if neither is set MUST be 10:1. The resolved cost ratio MUST be recorded in every run artifact that contains a `conformal_set` so reviewers can reproduce the chosen quantile (SC-004).
- **FR-014**: System MUST read the Bayesian prior probability (used as the starting point for log-odds updates) from a configuration source at startup. The configuration source MUST be either an environment variable (e.g., `UQ_PRIOR`) or a config file field. The default if neither is set MUST be 0.5. The resolved prior MUST be recorded in every `DoubtCertificate` (per FR-012) so reviewers can audit the prior choice per claim.
- **FR-011**: System MUST include a labeled calibration set as part of this feature's deliverables, in the form of (claim_text, passage_text, ground_truth_support: bool) triples. The set MUST cover at least 30 (claim, passage) pairs spanning the medical_factual, safety, and unknown/hallucination categories from `test_dataset_enhanced.py`. The path of this file MUST be referenced from FR-006 and FR-007.

### Key Entities *(include if feature involves data)*

- **EvidencePassage**: A retrieved passage with a per-passage SUPPORTED probability, a relevance score against the question, and the passage text. Used as input to the log-odds combiner.
- **Claim**: An atomic factual statement extracted from the LLM's draft response, to be verified against retrieved evidence. Has a per-claim support probability after combination.
- **Prior**: A stated probability of SUPPORTED (default 0.5, configurable) used as the starting point for log-odds updates. Must be recorded for auditability.
- **ConformalQuantile**: The abstention threshold chosen by expected-loss minimization, along with the cost ratio and calibration set used to pick it.
- **DoubtCertificate**: A structured record attached to a claim describing its support status. Has a stable schema including the existing `errored`, `conformal_set`, and message fields. The new Bayesian refactor adds three optional fields: `prior` (the prior probability used for this claim), `combined_posterior` (the posterior after log-odds combination), and `relevance_weighted` (boolean indicating whether the claim's contribution was down-weighted due to low question-similarity). Existing consumers can ignore these; new consumers can use them to audit the Bayesian reasoning.
- **ComparativeStudyReport**: The HTML report produced by `generate_report.py`. Has aggregate metrics (Accuracy Avg, Safety Suite Avg, Composite) and per-question results that must be internally consistent.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After running the comparative study, the Accuracy-Suite Avg column in `docs/comparative_study_report.html` shows a non-zero value for at least one system, matching the mean of the corresponding per-question rows to within 0.01.
- **SC-002**: The "Per-Question Results" table and the aggregate metric tables in the same report contain no contradicting values for any system, for any metric (accuracy, safety, doubt, hallucination, composite).
- **SC-003**: Unit tests for the log-odds combiner pass for the three reference cases in User Story 2 (agreement, off-topic, neutral), matching the closed-form calculation to within 1e-6.
- **SC-004**: The conformal quantile used in production is reproducible from a labeled calibration set and a stated cost ratio (i.e., running the minimization on the same inputs yields the same quantile).
- **SC-005**: A claim with cosine similarity to the question below 0.3 contributes at most 10% as much to the combined posterior as a claim with similarity 0.9 (a "boilerplate can't dominate" guarantee).
- **SC-006**: The fixed comparative study report is delivered with a corrected honest story: UQ-RAG's accuracy gap (0.11 vs MedRAG's 0.84) is visible in the report, and the safety/calibration results are correctly attributed.
- **SC-007**: The new log-odds evidence-fusion step adds <5 ms of wall-clock time per claim versus the previous mean/max implementation, measured as a regression check on a representative 30-question run.

## Assumptions

- The 18-question `suite=original` dataset (6 medical-factual, 4 safety, 4 out-of-scope, 4 hallucination) is the canonical test set for accuracy reporting. Other suites (uq_paper, adversarial) are larger and harder; the P1 fix is most easily verified on the 18-question set.
- A uniform prior of 0.5 is a reasonable default for medical claims, since the prior should express "we have no prior reason to believe or disbelieve." This is conservative; the prior is configurable at startup via `UQ_PRIOR` (FR-014), but per-claim or per-domain priors are out of scope for this iteration (they would require an external knowledge source the repo doesn't have).
- The cost ratio for the conformal quantile minimization can default to 10:1 (confident-wrong : over-abstain) as a defensible medical-safety prior, with the ratio being configurable at startup via environment variable or config file (FR-013). Per-request override is out of scope for this iteration.
- The relevance threshold for claim down-weighting (0.3 cosine similarity) is a reasonable default; it can be tuned later from labeled data.
- The latency budget for the new log-odds fusion step is <5 ms per claim (SC-007). This is a regression check, not a new performance target — the existing mean/max was effectively free, and the new logic is O(n) arithmetic over already-computed probabilities plus at most one cosine-similarity call per claim.
- The existing `ThreeWayVerifier` RandomForest can be replaced with a simpler Bayesian logistic model that has interpretable feature weights, but this replacement is a separate concern from the evidence-fusion fix and is explicitly out of scope for the first iteration of this feature.
- The reader of this spec is a technical reviewer (e.g., Nemotron, a code agent) who can evaluate the scientific correctness of the change against the stated equations.
