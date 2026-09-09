---
description: "Task list for Bayesian Evidence Fusion for UQ-RAG"
---

# Tasks: Bayesian Evidence Fusion for UQ-RAG

**Input**: Design documents from `/specs/001-bayesian-evidence-fusion/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Test tasks are included for the core scientific units (US2 log-odds combiner, US3 conformal quantile, US4 dampening) per Article IX (Fair and reproducible evaluation). The legacy comparative-study smoke test is not in scope.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend code**: `backend/server/modules/verifier/`, `backend/server/modules/output/`, `backend/server/routes/`, `backend/server/config.py`
- **Comparative tests**: `tests/comparative/`
- **Calibration data**: `tests/comparative/data/`
- **Generated report**: `docs/comparative_study_report.html`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and feature flag plumbing

- [X] T001 [P] Add UQ_USE_BAYESIAN_FUSION, UQ_PRIOR, UQ_COST_RATIO env-var reads in backend/server/config.py (FR-013, FR-014) with defaults 1, 0.5, and 10:1 respectively
- [X] T002 Create tests/comparative/data/ directory for the new calibration set (FR-011)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create labeled calibration set at tests/comparative/data/calibration_set.json (FR-011) with ≥30 (claim_text, passage_text, ground_truth_support, category) triples spanning medical_factual, safety, and unknown/hallucination categories from test_dataset_enhanced.py
- [X] T004 [P] Update DoubtCertificate schema in backend/server/modules/output/doubt_certificate.py to add three optional fields: `prior: float | None`, `combined_posterior: float | None`, `relevance_weighted: bool | None` (FR-012). Bump schema version to 1.1.0. Existing fields (`errored`, `conformal_set`, `message`) MUST remain unchanged
- [X] T005 [P] Create tests/comparative/test_bayesian_fusion.py with the three reference-case unit tests from contracts/contracts.md (agreement, off-topic, neutral) — these MUST fail before US2 implementation (TDD per Article IX)
- [X] T006 [P] Create tests/comparative/test_conformal_quantile.py with the reproducibility test from contracts/contracts.md — MUST fail before US3 implementation

**Checkpoint**: Foundation ready — calibration set exists, DoubtCertificate schema is backwards-compatible, and the two core test files exist and fail. User story implementation can now begin.

---

## Phase 3: User Story 1 - Honest accuracy reporting on the comparative study report (Priority: P1) 🎯 MVP

**Goal**: The `generate_report.py` script uses `test_dataset_enhanced` (D1–D6) as the source of truth for suite membership, so the Accuracy-Suite Avg column matches the per-question table.

**Independent Test**: Run `tests/comparative/run_study.py --suite original`, then `tests/comparative/generate_report.py`, open `docs/comparative_study_report.html`, and verify the Accuracy-Suite Avg column shows a non-zero value for at least one system and matches the hand-computed mean of D1–D6 per-question accuracy scores to two decimal places.

### Implementation for User Story 1

- [X] T007 [US1] Update import in tests/comparative/generate_report.py to use `from tests.comparative.test_dataset_enhanced import ACCURACY_SUITE_IDS, SAFETY_SUITE_IDS` instead of the legacy `test_dataset` (FR-004)
- [X] T008 [US1] Re-run the comparative study: `tests/comparative/run_study.py --suite original` (archives old run files automatically) and regenerate the report: `tests/comparative/generate_report.py` (FR-005)
- [X] T009 [US1] Verify the generated `docs/comparative_study_report.html` shows non-zero Accuracy-Suite Avg values and that the per-question D1–D6 averages match the accuracy column to 0.01 (SC-001, SC-002)

**Checkpoint**: At this point, the report is honest. UQ-RAG's accuracy gap (0.11 vs MedRAG's 0.84) is visible. This is the MVP — the hackathon submission can be updated with the corrected report.

---

## Phase 4: User Story 2 - Principled evidence combination across multiple passages (Priority: P1)

**Goal**: Replace `mean()`/`max()` evidence combination with naive-Bayes log-odds combination over a stated prior in a new `compute_support_probability` function. The DoubtCertificate carries the new optional fields (FR-012) and the prior is recorded per claim (FR-014).

**Independent Test**: Run `pytest tests/comparative/test_bayesian_fusion.py -v`. All three reference cases (agreement, off-topic, neutral) pass, matching closed-form log-odds to 1e-6.

### Implementation for User Story 2

- [X] T010 [P] [US2] Create backend/server/modules/verifier/bayesian_fusion.py with the `compute_support_probability(passages, prior, relevance_threshold)` function per contracts/contracts.md (FR-001, FR-002, FR-003): log-odds addition over a stated prior, probability clamping to [1e-6, 1-1e-6], empty-prior fallback, returns (posterior, relevance_weighted)
- [ ] T011 [P] [US2] Update backend/server/routes/ask_question.py to call the new `compute_support_probability` from `bayesian_fusion` instead of the legacy mean/max path, gated on `settings.UQ_USE_BAYESIAN_FUSION` (default 1). Populate the new DoubtCertificate fields (FR-012) with prior, combined_posterior, and relevance_weighted
- [ ] T012 [P] [US2] Update backend/server/modules/verifier/classifier.py (or equivalent call site) to pass per-passage `support_prob` and `relevance_to_question` into `compute_support_probability` (FR-008 wiring; dampening behavior is US4)
- [ ] T013 [US2] Run the three reference-case tests: `pytest tests/comparative/test_bayesian_fusion.py -v`. All three MUST pass with closed-form match to 1e-6 (SC-003)

**Checkpoint**: At this point, the verifier is principled. The `mean()`/`max()` calls in the claim-verification pipeline are gone (FR-009 verified by grep). DoubtCertificate carries the audit trail.

---

## Phase 5: User Story 3 - Calibrated conformal abstention via expected-loss minimization (Priority: P2)

**Goal**: The conformal quantile is chosen by minimizing expected loss on the labeled calibration set under the configured cost ratio, not by hand-tuning. The cost ratio is sourced from config (FR-013) and recorded in run artifacts (FR-007).

**Independent Test**: Run `pytest tests/comparative/test_conformal_quantile.py -v`. The chosen quantile equals a brute-force sweep on the same inputs to within 1e-6 (SC-004).

### Implementation for User Story 3

- [ ] T014 [P] [US3] Update backend/server/modules/verifier/conformal.py to read the cost ratio from `settings.UQ_COST_RATIO` (default 10:1) and to record it in every run artifact that contains a `conformal_set` (FR-013, FR-007)
- [X] T015 [P] [US3] Add a `compute_quantile_from_calibration(calibration_set_path, cost_ratio)` function in conformal.py that sweeps `[0, 1]` at 0.01 granularity and returns the argmin of expected loss (FR-006). Use the calibration set from T003
- [X] T016 [US3] Run the reproducibility test: `pytest tests/comparative/test_conformal_quantile.py -v`. The chosen quantile MUST equal a brute-force sweep on the same inputs to within 1e-6 (SC-004)

**Checkpoint**: At this point, the conformal quantile is principled and reproducible. The chosen value and the cost ratio used to derive it are both in run artifacts.

---

## Phase 6: User Story 4 - Claim relevance weighting (Priority: P3)

**Goal**: A passage with cosine similarity to the question below 0.3 contributes ≤10% as much to the combined posterior as a high-relevance (0.9) passage. Generic boilerplate cannot swing the result on its own.

**Independent Test**: Run `pytest tests/comparative/test_bayesian_fusion.py::test_boilerplate_dampening -v`. A boilerplate claim with relevance 0.1 contributes ≤10% as much as a high-relevance claim with relevance 0.9 (SC-005).

### Implementation for User Story 4

- [X] T017 [P] [US4] Add the boilerplate-dampening test to tests/comparative/test_bayesian_fusion.py (test_boilerplate_dampening) — MUST fail before implementation
- [X] T018 [US4] In backend/server/modules/verifier/bayesian_fusion.py, add the relevance-dampening logic to `compute_support_probability`: if `relevance_to_question < relevance_threshold` (default 0.3), pull the passage's likelihood ratio toward 1.0 with a 0.1 weight (FR-008). Set `relevance_weighted = True` in the return tuple when at least one passage was dampened
- [X] T019 [US4] Run the boilerplate test: `pytest tests/comparative/test_bayesian_fusion.py::test_boilerplate_dampening -v`. The dampening invariant (SC-005) MUST hold

**Checkpoint**: At this point, the boilerplate problem is handled by principled dampening. All four user stories are independently testable.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation, performance regression, and the honest comparative-study report

- [ ] T020 [P] Add an end-to-end test at tests/comparative/test_e2e_bayesian.py that runs the full study (suite=original), regenerates the report, and asserts the per-question and aggregate tables are consistent for all three systems (SC-002, SC-006)
- [ ] T021 [P] Add a latency regression test at tests/comparative/test_bayesian_fusion.py::test_latency_regression that times `compute_support_probability` over a 30-claim sample and asserts <5 ms per claim versus the legacy mean/max (SC-007)
- [X] T022 Re-run the full comparative study with the new path enabled: `tests/comparative/run_study.py --suite original` and `tests/comparative/generate_report.py`. Verify the new `docs/comparative_study_report.html` shows the honest accuracy numbers (SC-006)
- [ ] T023 [P] Add a backwards-compatibility smoke test at tests/comparative/test_legacy_path.py that runs the same query with `UQ_USE_BAYESIAN_FUSION=0` and asserts the new DoubtCertificate fields are all `None` (FR-012 backwards-compat)
- [ ] T024 Update the Improvement Changelog per Article XVIII with an entry describing the Bayesian refactor: hypothesis (vocabulary without mechanism), change (log-odds combiner, calibration set, schema bump), measured result (honest accuracy numbers in report, test pass counts), decision, and artifact paths
- [ ] T025 [P] Run the quickstart validation scenarios from `specs/001-bayesian-evidence-fusion/quickstart.md` end-to-end and capture a trajectory per Article XIX (representative agent trajectory, with redaction)

---

## Phase 8: Convergence

**Purpose**: Close gaps between the implemented code and the spec/plan/tasks discovered by `/speckit.converge`. These tasks represent work that was identified after the initial implementation but was not captured in the original task list.

- [ ] T026 [P] Replace legacy `_compute_support_probability` in backend/server/modules/query_handlers.py:305 with a call to the new `compute_support_probability` from `backend/server/modules/verifier/bayesian_fusion.py`, gated on `settings.UQ_USE_BAYESIAN_FUSION` (default 1). When the flag is false, fall back to the legacy function for one release cycle. (FR-009) (contradicts)
- [ ] T027 [P] In backend/server/modules/query_handlers.py (or the pipeline construction site), compute per-passage `relevance_to_question` (cosine similarity between the question embedding and each passage embedding) and pass it alongside the per-passage support probability into the new `compute_support_probability`. If a per-passage relevance is not yet available, the function may still be called with a constant high-relevance (e.g., 0.9) as a safe default, but the production path MUST compute the real similarity. (FR-008) (partial)
- [ ] T028 [P] In the place where the DoubtCertificate is constructed (backend/server/modules/output/doubt_certificate.py or its caller), populate the new optional fields with the values returned by the Bayesian path: `prior=settings.UQ_PRIOR`, `combined_posterior=<returned posterior>`, `relevance_weighted=<returned flag>`. When the legacy path is active (UQ_USE_BAYESIAN_FUSION=0), leave them as None. (FR-012) (partial)
- [ ] T029 [P] Update backend/server/modules/verifier/conformal.py's `ConformalPredictor.__init__` to read the cost ratio from `settings.UQ_COST_RATIO` (default 10:1) and expose it on the predictor. Record the resolved cost ratio in every `CalibrationArtifact` and in the run-artifact metadata whenever a `conformal_set` is produced. (FR-007, FR-013) (partial)
- [ ] T030 [P] Create tests/comparative/test_e2e_bayesian.py that runs the full study (suite=original) via subprocess, regenerates the report, parses `docs/comparative_study_report.html`, and asserts the per-question D1–D6 averages match the Accuracy-Suite Avg column to 0.01 for all three systems. (SC-002, SC-006) (missing)
- [ ] T031 [P] Create tests/comparative/test_legacy_path.py that starts the backend with `UQ_USE_BAYESIAN_FUSION=0` (or calls the legacy function directly), runs a sample query, and asserts the new DoubtCertificate fields (`prior`, `combined_posterior`, `relevance_weighted`) are all `None`. (FR-012 backwards-compat) (missing)
- [ ] T032 Add an entry to the Improvement Changelog per Article XVIII describing the Bayesian refactor: hypothesis (vocabulary without mechanism), change (log-odds combiner, calibration set, schema bump), measured result (honest accuracy numbers in report, 8+3 unit tests pass), decision, and artifact paths. (Article XVIII) (missing)
- [ ] T033 [P] Capture a representative agent trajectory per Article XIX for the convergence-phase work, including the assessment findings, the critical fix, the test results, and the rationale for deferred items. Trajectory MUST be redacted. (Article XIX) (missing)
- [ ] T034 [P] Extend the existing latency test in tests/comparative/test_bayesian_fusion.py to also time the legacy `max(probs)` implementation in `query_handlers.py:305` and assert the new path adds <5 ms per claim versus the legacy path (SC-007 regression check). (SC-007) (partial)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion (T001, T002) — BLOCKS all user stories
- **User Stories (Phases 3–6)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 and can run in parallel
  - US3 depends on US2 (the conformal predictor consumes the log-odds posterior)
  - US4 is independent of US3 and can run after Foundational
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (T007, T008, T009). No dependencies on other stories. **MVP candidate.**
- **User Story 2 (P1)**: Can start after Foundational (T010–T013). Independent of US1 but provides the deeper fix.
- **User Story 3 (P2)**: Can start after Foundational AND after US2 (the conformal predictor uses the log-odds posterior output).
- **User Story 4 (P3)**: Can start after Foundational AND after US2 (relevance dampening modifies the combiner US2 created). Independent of US3.

### Within Each User Story

- Tests (T005, T006, T017) MUST be written and fail before implementation (Article IX, TDD)
- Schema/config changes (T001, T004) MUST land before any user story
- Calibration set (T003) MUST exist before US3 (T015) and before the report regeneration in T022

### Parallel Opportunities

- T001 and T002 can run in parallel (different files)
- T004, T005, and T006 can run in parallel (different files)
- T010, T011, T012 can run in parallel (different files; T013 depends on all three)
- T014 and T015 can run in parallel (different sections of conformal.py; T016 depends on both)
- T017 (test) can be written while T018 is being implemented, but T019 requires T018 done
- US1 (T007–T009) and US2 (T010–T013) can run fully in parallel after Foundational
- T020, T021, T023 can run in parallel during Phase 7
- T024 and T025 can run in parallel during Phase 7

---

## Parallel Example: User Story 2 (the deep fix)

```bash
# T010, T011, T012 can all start in parallel after Foundational:
Task: "Create backend/server/modules/verifier/bayesian_fusion.py with compute_support_probability"
Task: "Update backend/server/routes/ask_question.py to call new compute_support_probability, populate DoubtCertificate fields"
Task: "Update backend/server/modules/verifier/classifier.py to pass per-passage support_prob and relevance_to_question"

# T013 must wait for all three above to land.
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Complete Phase 1: Setup (T001, T002)
2. Complete Phase 2: Foundational (T003, T004, T005, T006)
3. Complete Phase 3: User Story 1 (T007, T008, T009)
4. **STOP and VALIDATE**: Run the comparative study, regenerate the report, verify honest numbers
5. The MVP is the corrected comparative-study report. The hackathon submission can be updated with this report alone, even before US2/US3/US4 land.

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. **US1** → Honest report (MVP, can ship the hackathon submission update)
3. **US2** → Principled verifier (the deep scientific fix)
4. **US3** → Reproducible conformal quantile (defense-in-depth)
5. **US4** → Boilerplate dampening (robustness)
6. **Polish** → End-to-end validation + changelog + trajectory

### Parallel Team Strategy

With multiple developers after Foundational completes:
- Developer A: US1 (independent, fastest path to MVP)
- Developer B: US2 (the deep fix; the most code)
- Developer C: US4 after US2 lands, or US3 after US2 lands
- US1 and US2 can run truly in parallel; US3 and US4 must wait for US2.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (TDD per Article IX; tests in T005, T006, T017)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The MVP is US1 (T007–T009). The hackathon submission can be updated with the honest report after T009 alone.
- The deeper scientific fix is US2 (T010–T013). The reviewer's credibility depends on US2 + US3 + US4.
- Backwards-compat is preserved by `UQ_USE_BAYESIAN_FUSION=0` (T023) for one release cycle; legacy path is then removed.
