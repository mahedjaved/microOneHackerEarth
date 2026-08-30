# Tasks: Comparative Study Framework

**Input**: Design documents from `/specs/003-comparative-study/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included per the spec requirements (FR-006, FR-008, SC-007).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/server/routes/` for endpoint implementations
- **Frontend**: `frontend/components/` for UI components
- **Tests**: `tests/comparative/` for comparative study tests
- **Tests**: `tests/regression/` for Playwright E2E tests
- **Docs**: `docs/` for generated reports

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for comparative study framework

- [x] T001 Create `tests/comparative/__init__.py` file to make it a Python package
- [x] T002 Create `tests/comparative/results/` directory for JSON artifacts
- [x] T003 Create `docs/` directory for generated reports
- [x] T004 Verify Playwright is installed and configured for E2E tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Create `tests/comparative/test_dataset.py` with centralized 20+ question dataset across 4 categories (medical_factual, safety_emergency, safety_prohibited, unknown, hallucination) per data-model.md TestQuestion entity
- [x] T006 Create `tests/comparative/scoring.py` with category-specific scoring functions (keyword match, safety detection, doubt expression, citation presence, hallucination avoidance) returning ScoreResult per data-model.md
- [x] T007 Create `tests/comparative/conftest.py` fixtures for backend health check and test configuration
- [x] T008 Create `backend/server/schemas.py` update with SystemResponse Pydantic model including optional fields for UQ-specific data (confidence, doubt_certificate)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Examiner Evidence Review (Priority: P1) 🎯 MVP

**Goal**: Generate HTML comparison report showing UQ-RAG advantages over baselines for safety, accuracy, and trustworthiness metrics

**Independent Test**: Run `python tests/comparative/generate_report.py` and verify `docs/comparative_study_report.html` is generated with pass/fail criteria showing UQ-RAG advantages

### Implementation for User Story 1

- [x] T009 [P] [US1] Create `backend/server/routes/medrag_baseline.py` implementing `POST /medrag_baseline/` endpoint with standard RAG (top-5 retrieval, no UQ) per contracts/medrag_baseline.md
- [x] T010 [P] [US1] Create `backend/server/routes/no_rag.py` implementing `POST /no_rag/` endpoint with direct LLM (no retrieval) per contracts/no_rag.md
- [x] T011 [US1] Register `medrag_baseline` and `no_rag` routers in `backend/server/main.py`
- [x] T012 [US1] Update `tests/comparative/test_comparison.py` ENDPOINTS dict to include `medrag_baseline` and `no_rag` systems alongside existing `uq_rag`
- [x] T013 [US1] Expand test dataset in `tests/comparative/test_dataset.py` to 20+ questions (add 2 medical_factual, 2 safety, 2 unknown, 2 hallucination beyond existing 12)
- [x] T014 [US1] Update `tests/comparative/scoring.py` to compute two test suites (accuracy-prioritized: M1-M6; safety-prioritized: S1-S4, E1-E4, H1-H4) with equal weighting
- [x] T015 [US1] Update `tests/comparative/generate_report.py` to generate HTML report with: executive summary, per-question results table, aggregate metrics, accuracy suite summary, safety suite summary, composite score = (accuracy + safety) / 2, winner declaration
- [x] T016 [US1] Add validation that HTML report shows UQ-RAG advantages in safety detection rate, doubt expression rate, citation presence, and hallucination rate

**Checkpoint**: At this point, User Story 1 should be fully functional - run `python tests/comparative/generate_report.py` and verify `docs/comparative_study_report.html` exists

---

## Phase 4: User Story 2 - Automated Regression Testing (Priority: P2)

**Goal**: Automated tests that detect regressions in UQ advantages as the system evolves

**Independent Test**: Run `pytest tests/comparative/ -v` and verify all tests pass consistently; verify tests fail when regression is introduced

### Implementation for User Story 2

- [x] T017 [P] [US2] Create `tests/comparative/test_regression.py` with regression tests for: safety detection rate >= 90%, doubt expression rate >= 80%, hallucination rate <= 50% of baseline
- [x] T018 [P] [US2] Create `tests/comparative/test_reproducibility.py` that runs scoring 3 times and verifies consistent results (FR-008)
- [x] T019 [US2] Add performance test verifying each question scored within 30 seconds (SC-009)
- [x] T020 [US2] Add test verifying full report generation within 5 minutes (SC-008)
- [x] T021 [US2] Update `tests/comparative/conftest.py` with fixtures for: empty corpus simulation, Pinecone unavailable simulation, rate limit simulation
- [x] T022 [US2] Add graceful degradation tests: empty corpus returns doubt certificate for UQ-RAG, error message for baselines

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - run `pytest tests/comparative/ -v` and verify all pass

---

## Phase 5: User Story 3 - Baseline Comparison API (Priority: P3)

**Goal**: Programmatic API endpoints for comparing responses from all three systems

**Independent Test**: Send POST requests to `/medrag_baseline/` and `/no_rag/` endpoints and verify responses match expected schema

### Implementation for User Story 3

- [x] T023 [P] [US3] Create `tests/comparative/test_contracts.py` with contract tests for `/medrag_baseline/` and `/no_rag/` endpoints verifying response schema matches contracts/
- [x] T024 [US3] Verify all three endpoints return common schema with `system` field (FR-007)
- [x] T025 [US3] Verify `/medrag_baseline/` response includes `response`, `sources`, `system` fields but no `confidence` or `doubt_certificate` (FR-001)
- [x] T026 [US3] Verify `/no_rag/` response includes `response`, `system` fields but no `sources` or `confidence` (FR-002)
- [x] T027 [US3] Verify `/ask/` (UQ-RAG) response includes `response`, `sources`, `confidence`, `doubt_certificate` (when applicable), `emergency` flag
- [x] T028 [US3] Add error handling tests: empty corpus returns structured error, Pinecone unavailable returns 503, rate limit returns 429

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Playwright E2E Tests (Cross-Cutting)

**Purpose**: End-to-end UI tests verifying complete user journey

- [x] T029 [P] Create `tests/regression/test_comparative_ui.py` with Playwright tests for: document upload via frontend, question submission via frontend, response display verification, history download verification
- [x] T030 [P] Create `tests/regression/test_comparative_systems.py` with Playwright tests verifying all three systems respond through the Streamlit frontend
- [x] T031 Update `tests/regression/conftest.py` with Playwright fixtures for: frontend URL, backend URL, browser launch

**Checkpoint**: Run `pytest tests/regression/test_comparative*.py -v` and verify all E2E tests pass

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T032 [P] Update `specs/003-comparative-study/quickstart.md` with actual validation results
- [x] T033 [P] Add README.md in `tests/comparative/` documenting how to run tests and interpret results
- [x] T034 Code cleanup: ensure all endpoints follow same error handling pattern, all tests use common fixtures
- [x] T035 Security hardening: verify no PII in test questions, verify no credentials in test outputs
- [x] T036 Run full validation per quickstart.md and verify all success criteria met

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (Phase 2)
- **User Story 2 (Phase 4)**: Depends on Foundational (Phase 2) + US1 completion for report validation
- **User Story 3 (Phase 5)**: Depends on Foundational (Phase 2) + US1 completion for endpoint existence
- **Playwright E2E (Phase 6)**: Depends on US1 + US3 completion
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Uses test_dataset.py and scoring.py from foundation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Tests endpoints created in US1

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T001-T004)
- All Foundational tasks marked [P] can run in parallel (T005-T008)
- US1 tasks T009 and T010 (endpoint creation) can run in parallel
- US2 tasks T017-T018 can run in parallel
- US3 tasks T023, T024-T028 can run in parallel
- Different user stories can be worked on in parallel by different team members (after Foundation)

---

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for User Story 1 in parallel:
Task: "Create backend/server/routes/medrag_baseline.py"
Task: "Create backend/server/routes/no_rag.py"

# After endpoints created, launch tests:
Task: "Update test_comparison.py with new endpoints"
Task: "Expand test dataset to 20+ questions"
Task: "Update scoring.py for two test suites"
Task: "Update generate_report.py for HTML report"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T008) - CRITICAL
3. Complete Phase 3: User Story 1 (T009-T016)
4. **STOP and VALIDATE**: Run `python tests/comparative/generate_report.py` and verify HTML report shows UQ-RAG advantages
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Generate HTML report (MVP!)
3. Add User Story 2 → Test independently → Regression tests pass
4. Add User Story 3 → Test independently → Contract tests pass
5. Add Playwright E2E → Test independently → Full UI validation
6. Polish → Final validation → Submission ready

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (endpoints + report)
   - Developer B: User Story 2 (regression tests)
   - Developer C: User Story 3 (contract tests)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

## Success Criteria Mapping

| Success Criterion | Task(s) |
|-------------------|---------|
| SC-001: UQ-RAG citations >= 85% | T013, T014, T015 |
| SC-002: UQ-RAG accuracy within 10% of MedRAG | T013, T014 |
| SC-003: UQ-RAG hallucination rate 50% lower | T013, T014, T015 |
| SC-004: Safety detection rate >= 90% | T013, T014, T017 |
| SC-005: Doubt expression rate >= 80% | T013, T014, T017 |
| SC-006: Composite score = (accuracy + safety) / 2 | T014, T015 |
| SC-007: Playwright E2E tests pass | T29, T30 |
| SC-008: Report generated within 5 min | T020 |
| SC-009: Each question scored within 30s | T019 |

## Functional Requirement Mapping

| FR | Task(s) |
|----|---------|
| FR-001: /medrag_baseline/ endpoint | T009, T011 |
| FR-002: /no_rag/ endpoint | T010, T011 |
| FR-003: 20+ question test dataset | T005, T013 |
| FR-004: Automated scoring | T006, T014 |
| FR-005: HTML comparison report | T015 |
| FR-006: Playwright E2E tests | T29, T30 |
| FR-007: system field in responses | T024 |
| FR-008: Consistent reproducible results | T018 |
