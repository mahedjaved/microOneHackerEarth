# Tasks: CURA-Med Frontend

**Input**: Design documents from `/specs/002-frontend-material/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/` for Streamlit UI, `backend/` for API
- Frontend paths: `frontend/components/`, `frontend/app.py`, `frontend/utils.py`

<!--
  ============================================================================
  IMPORTANT: The tasks below are actual tasks for the CURA-Med frontend feature.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create frontend requirements.txt with Streamlit and requests dependencies in frontend/requirements.txt
- [X] T002 Verify backend API endpoints are accessible (health, upload_pdfs, ask) per contracts/api-contracts.md
- [X] T003 [P] Create frontend/.env.example with API_URL placeholder

**Checkpoint**: Frontend dependencies installed and backend API reachable

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create frontend/config.py with API_URL loading from environment in frontend/config.py
- [X] T005 [P] Create frontend/utils.py with request helper functions (ask_question, upload_pdfs_api) in frontend/utils.py
- [X] T006 [P] Add error handling utilities for backend unavailability in frontend/utils.py
- [X] T007 Create frontend/uat_test.py skeleton with health check and ask endpoint tests in frontend/uat_test.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Upload medical PDFs and ask questions (Priority: P1) 🎯 MVP

**Goal**: Users can upload PDFs and ask medical questions, receiving cited answers with sources and disclaimer.

**Independent Test**: Upload a PDF, ask a question, verify answer includes citations and disclaimer.

### Implementation for User Story 1

- [X] T008 [P] [US1] Implement PDF upload component in frontend/components/upload.py
- [X] T009 [P] [US1] Implement chat UI with question input and answer display in frontend/components/chatUI.py
- [X] T010 [US1] Integrate upload and chat components in frontend/app.py
- [X] T011 [US1] Add medical disclaimer display to answer rendering in frontend/components/chatUI.py
- [X] T012 [US1] Add source citation display to answer rendering in frontend/components/chatUI.py
- [X] T013 [US1] Add error handling for backend failures in frontend/components/chatUI.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 3 - Emergency response and safety bypass (Priority: P1)

**Goal**: Emergency queries receive immediate safety response within 2 seconds.

**Independent Test**: Submit emergency query, verify response within 2 seconds with emergency instructions.

### Implementation for User Story 3

- [X] T014 [US3] Add emergency response detection and prominent display in frontend/components/chatUI.py
- [X] T015 [US3] Ensure emergency responses bypass normal answer rendering in frontend/components/chatUI.py

**Checkpoint**: Emergency queries display safety response immediately

---

## Phase 5: User Story 2 - View uncertainty warnings and doubt certificates (Priority: P2)

**Goal**: Users see doubt certificates when evidence is insufficient, with clear explanation.

**Independent Test**: Ask question with no evidence, verify doubt certificate displayed.

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement doubt certificate display component in frontend/components/chatUI.py
- [X] T017 [US2] Add uncertainty warning styling and messaging in frontend/components/chatUI.py

**Checkpoint**: Doubt certificates displayed for insufficient evidence

---

## Phase 6: User Story 4 - Download run artifacts for audit trail (Priority: P3)

**Goal**: Users can download run artifacts containing interaction history with PII redacted.

**Independent Test**: Ask question, download artifact, verify contents and redaction.

### Implementation for User Story 4

- [X] T018 [P] [US4] Implement run artifact download button in frontend/components/history_download.py
- [X] T019 [US4] Add artifact display and download trigger in frontend/app.py

**Checkpoint**: Run artifacts downloadable with PII redacted

---

## Phase 7: User Story 5 - UAT validation and end-to-end testing (Priority: P2)

**Goal**: Automated UAT script validates frontend-backend integration across all user scenarios.

**Independent Test**: Run UAT script, verify all test cases pass.

### Implementation for User Story 5

- [X] T020 [US5] Extend frontend/uat_test.py with tests for all user stories in frontend/uat_test.py
- [X] T021 [US5] Add test for emergency response in frontend/uat_test.py
- [X] T022 [US5] Add test for doubt certificate display in frontend/uat_test.py
- [X] T023 [US5] Add test for run artifact download in frontend/uat_test.py

**Checkpoint**: UAT script passes all test cases

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T024 [P] Update frontend/requirements.txt with exact versions in frontend/requirements.txt
- [X] T025 [P] Add loading states and spinners for backend processing in frontend/components/chatUI.py
- [X] T026 [P] Add retry logic for transient backend errors in frontend/utils.py
- [X] T027 Verify quickstart.md validation scenarios pass in quickstart.md
- [X] T028 Run full UAT and fix any failures in frontend/uat_test.py

---

## Phase 9: Convergence

**Purpose**: Remaining work identified by assessing the codebase against spec.md, plan.md, and tasks.md.

- [X] T029 Add PII redaction to downloaded artifacts per FR-008 (missing)
- [X] T030 Track emergency state and remind on subsequent questions per US3/AC3 (missing)
- [X] T031 Add timestamp and unique run artifact ID to downloads per US4/AC3 (partial)
- [X] T032 Add file size validation (50MB limit) before upload per FR-012 (partial)
- [X] T033 Add empty question validation per Edge Cases (missing)
- [X] T034 Render uncertainty causes and actions separately per FR-009 (partial)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in priority order (P1 → P2 → P3)
  - US1 and US3 are both P1 and can run in parallel after Phase 2
  - US2 and US5 are P2 and can run in parallel after Phase 2
  - US4 is P3 and can run after Phase 2
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 but independently testable
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - Depends on US1, US2, US3, US4 being complete
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Independently testable

### Within Each User Story

- Components before integration
- Core implementation before error handling
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- T008 and T009 (US1 components) can run in parallel
- T014 and T015 (US3) can run in parallel
- T016 and T017 (US2) can run in parallel
- T018 and T019 (US4) can run in parallel
- T020-T023 (US5 tests) can run in parallel
- T024-T026 (Polish) can run in parallel
- Different user stories can be worked on in parallel by different team members after Phase 2

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all foundational tasks together:
T005: Create request helpers in frontend/utils.py
T006: Add error handling utilities in frontend/utils.py
T007: Create UAT test skeleton in frontend/uat_test.py
```

---

## Implementation Strategy

### MVP First (User Story 1 + 3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (upload + ask)
4. Complete Phase 4: User Story 3 (emergency response)
5. **STOP and VALIDATE**: Test US1 and US3 independently
6. Demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 3 → Test independently → Deploy/Demo
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Add User Story 5 → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (upload + ask)
   - Developer B: User Story 3 (emergency)
   - Developer C: User Story 2 (doubt certificates)
3. Stories complete and integrate independently
4. Developer D: User Story 4 (artifacts) and User Story 5 (UAT)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
