# Tasks: abstention-measurement

**Input**: Design documents from `/specs/006-abstention-measurement/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume web app layout per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create `data/runs/` directory for exported claim records and risk-coverage artifacts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Add `UQ_SUPPRESS_DOUBT_CERTIFICATE` flag to `backend/server/config.py` with default `False`
- [ ] T003 Verify `backend/server/modules/query_handlers.py` uses `compute_support_probability()` from `bayesian_fusion.py` instead of `max(probs)` at the claim-verification step
- [ ] T004 Verify `ConformalPredictor` is initialized via `from_quantile()` and `predict_set_from_probs()` is called at runtime in `backend/server/main.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 4 - Repair calibration before conference (Priority: P1) 🎯 MVP

**Goal**: Ensure the live pipeline uses calibrated Bayesian fusion and a properly wired conformal predictor before any conference artifacts are generated.

**Independent Test**: Automated tests confirm `max(probs)` is absent from the claim-verification path and `compute_support_probability()` is present.

### Implementation for User Story 4

- [ ] T005 [US4] Replace `max(probs)` combination in `backend/server/modules/query_handlers.py:305` with `compute_support_probability()` from `backend.server.modules.verifier.bayesian_fusion`
- [ ] T006 [US4] Update `backend/server/main.py` `_init_uq_pipeline()` to initialize `ConformalPredictor` via `from_quantile(quantile, alpha=alpha, method="LAC")` instead of the `is_fitted = True` stub
- [ ] T007 [US4] Add test in `backend/tests/test_verifier_modules.py` asserting the live claim-verification path calls `compute_support_probability()`
- [ ] T008 [US4] Add test in `backend/tests/test_verifier_modules.py` asserting `ConformalPredictor.predict_set_from_probs()` is called at runtime

**Checkpoint**: At this point, User Story 4 should be fully functional and testable independently. The pipeline is now calibrated and ready for abstention measurement.

---

## Phase 4: User Story 1 - Measure abstention quality with risk-coverage curves (Priority: P1)

**Goal**: Generate a risk-coverage curve demonstrating that the system's confidence scores actually track correctness, with AUC reported alongside calibration metadata.

**Independent Test**: Run `scripts/risk_coverage.py` on a labeled claim set and produce `data/runs/risk_coverage.json` plus `data/runs/risk_coverage.png`.

### Implementation for User Story 1

- [ ] T009 [P] [US1] Add `ClaimRecord` fields to `backend/server/schemas.py` for per-claim export (`support_probability`, `conformal_set`, `is_correct`, `perturbation_type`, `pipeline_mode`, `run_artifact_id`)
- [ ] T010 [P] [US1] Implement claim exporter in `backend/server/modules/output/answer.py` to write one JSONL line per claim to `data/runs/claims.jsonl`
- [ ] T011 [US1] Create `scripts/risk_coverage.py` with `load_claims()`, `risk_coverage_curve()`, and `plot()` functions per `contracts/risk-coverage.md`
- [ ] T012 [US1] Add bootstrap 95% CI computation for AUC in `scripts/risk_coverage.py`
- [ ] T013 [US1] Add calibration metadata fields (`calibration_brier`, `calibration_ece`, `calibration_warning`) to `data/runs/risk_coverage.json` output
- [ ] T014 [US1] Integrate claim export into `backend/scripts/test_e2e.py` so end-to-end runs produce `data/runs/claims.jsonl`
- [ ] T015 [P] [US1] Add unit test for `scripts/risk_coverage.py` in `backend/tests/test_risk_coverage.py` using synthetic claims with known correctness labels
- [ ] T016 [US1] Generate pilot risk-coverage curve on existing run artifacts and save to `data/runs/risk_coverage.json` and `data/runs/risk_coverage.png`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. A risk-coverage curve PNG and JSON artifact exist for the conference.

---

## Phase 5: User Story 2 - Compare abstention under clean vs. adversarial perturbation (Priority: P2)

**Goal**: Run the same questions through clean and adversarially perturbed versions and report whether abstention behavior shifts more under perturbation or under the explicit abstention mechanism.

**Independent Test**: Run `scripts/risk_coverage.py --compare-clean-adversarial` on a labeled claim set and produce `data/runs/perturbation_comparison.json`.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Load `data/corpus/adversarial/adversarial_cases.jsonl` and create clean/adversarial question pairs in `scripts/risk_coverage.py`
- [ ] T018 [US2] Add `--compare-clean-adversarial` mode to `scripts/risk_coverage.py` that groups claims by `perturbation_type` and compares abstention rates and average `support_probability`
- [ ] T019 [US2] Generate `data/runs/perturbation_comparison.json` with abstention shift analysis per `contracts/ablation.md`
- [ ] T020 [P] [US2] Add test in `backend/tests/test_risk_coverage.py` for adversarial perturbation comparison using synthetic clean/adversarial pairs

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. The perturbation comparison artifact exists.

---

## Phase 6: User Story 3 - Ablate the explicit abstention option (Priority: P2)

**Goal**: Compare the full UQ-RAG pipeline against a version with doubt-certificate output suppressed on the same question set, reporting accuracy, abstention rate, and safety-detection deltas with effect size.

**Independent Test**: Run the same question set twice with `UQ_SUPPRESS_DOUBT_CERTIFICATE=False` and `True`, then run `scripts/risk_coverage.py --ablate` to produce `data/runs/ablation.json`.

### Implementation for User Story 3

- [ ] T021 [US3] Implement `UQ_SUPPRESS_DOUBT_CERTIFICATE` behavior in `backend/server/modules/output/answer.py`: when `True`, replace `DoubtCertificate` with generic non-committal response and set `doubt_certificate=None`
- [ ] T022 [US3] Add `doubt_certificate_suppressed` field to run artifacts when the flag is active
- [ ] T023 [US3] Add `--ablate` mode to `scripts/risk_coverage.py` that takes two claim JSONL files (`full` vs `abstention_suppressed`) and computes `accuracy_delta`, `abstention_rate_delta`, `safety_detection_delta`, and `effect_size`
- [ ] T024 [US3] Generate `data/runs/ablation.json` comparing full vs. suppressed pipeline on the same question set per `contracts/ablation.md`
- [ ] T025 [P] [US3] Add test in `backend/tests/test_output_modules.py` verifying `UQ_SUPPRESS_DOUBT_CERTIFICATE=True` produces generic response and `doubt_certificate=None`

**Checkpoint**: All user stories should now be independently functional. The abstention ablation artifact exists.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T026 [P] Add `UQ_SUPPRESS_DOUBT_CERTIFICATE` to `backend/server/.env.example` with documentation comment
- [ ] T027 [P] Validate all generated artifacts (`risk_coverage.json`, `perturbation_comparison.json`, `ablation.json`) against their contracts in `specs/006-abstention-measurement/contracts/`
- [ ] T028 Run `quickstart.md` validation scenarios end-to-end and fix any gaps
- [ ] T029 Update `submission/unit-tests/report.md` with abstention-measurement artifacts and conference-ready summary

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order: US4 (P1) → US1 (P1) → US2 (P2) → US3 (P2)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 4 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. Must complete before US1.
- **User Story 1 (P1)**: Depends on US4 completion. Can then proceed independently.
- **User Story 2 (P2)**: Depends on US1 completion (reuses claim export format). Can then proceed independently.
- **User Story 3 (P2)**: Depends on US4 completion (reuses config flag). Can then proceed independently.

### Within Each User Story

- Models before services
- Services before scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T009 and T010 can run in parallel (different files)
- T017 and T021 can run in parallel (different files)
- T020 and T025 can run in parallel (different test files)
- T026 and T027 can run in parallel (different files)

---

## Parallel Example: User Story 1

```bash
# Launch parallel tasks for US1:
Task: "Add ClaimRecord fields to backend/server/schemas.py"
Task: "Implement claim exporter in backend/server/modules/output/answer.py"
```

---

## Implementation Strategy

### MVP First (User Stories 4 + 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 4 (calibration repair)
4. Complete Phase 4: User Story 1 (risk-coverage curve)
5. **STOP and VALIDATE**: Test US1 independently — you now have a conference-ready artifact
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US4 → Calibration repaired, tests pass
3. US1 → Risk-coverage curve generated (MVP!)
4. US2 → Perturbation comparison added
5. US3 → Abstention ablation added
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US4 (calibration repair)
   - Developer B: US1 (risk-coverage curve, depends on US4)
   - Developer C: US3 (ablation, depends on US4)
3. After US4 completes:
   - Developer B starts US1
   - Developer D starts US2 (depends on US1)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
