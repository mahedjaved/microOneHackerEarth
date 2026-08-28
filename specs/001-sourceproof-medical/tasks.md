# Tasks: SourceProof Medical / CURA-Med

**Input**: Design documents from `/specs/001-sourceproof-medical/`
- `plan.md` — extend existing `backend/` FastAPI + Streamlit system
- `spec.md` — 5 user stories (P1–P3)
- `research.md` — GP verifier + MAPIE + MedRAG foundation
- `data-model.md` — entities extending existing schemas
- `contracts/` — 5 JSON schemas
- `quickstart.md` — 7 validation scenarios

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/, quickstart.md

**Tests**: Tests are OPTIONAL — not explicitly requested in spec. Focus on implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Existing backend**: `backend/server/`
- **New modules**: `backend/server/modules/{safety,claims,verifier,eav,output,artifacts}/`
- **Routes**: `backend/server/routes/`
- **Tests**: `backend/tests/`
- **Contracts**: `specs/001-sourceproof-medical/contracts/`
- **Scripts**: `backend/scripts/`

---

## Phase 1: Setup (Extend Existing Backend)

**Purpose**: Prepare the existing `backend/` for CURA-Med extension

- [ ] T001 Extend `backend/server/requirements.txt` with scikit-learn, mapie, sentence-transformers
- [ ] T002 Create new module directories under `backend/server/modules/`: safety/, claims/, verifier/, eav/, output/, artifacts/
- [ ] T003 [P] Add `__init__.py` files to all new module directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Extend `backend/server/schemas.py` with DoubtCertificate, RunArtifact, EAVAction, Claim, VerifierResult, EvidenceFeatureVector, SafetyScope, Verdict, AmbiguityFlag, UncertaintyCause, EAVActionType, FinalDecision
- [ ] T005 [P] Implement `backend/server/modules/safety/gate.py` — medical-scope gate with emergency detection, personal diagnosis/prescription rejection, and scope explanation
- [ ] T006 [P] Implement `backend/server/modules/safety/isolation.py` — untrusted-content isolation for retrieved passages and user text
- [ ] T007 [P] Implement `backend/server/modules/corpus/loader.py` — load and version corpus chunks with provenance (MIRAGE/PubMed + synthetic adversarial set)
- [ ] T008 Implement `backend/server/modules/corpus/hash.py` — corpus hashing and versioning
- [ ] T009 [P] Implement `backend/server/modules/claims/composer.py` — atomic claim decomposition from LLM answer using existing Groq/Llama
- [ ] T010 [P] Implement `backend/server/modules/claims/feature_vector.py` — 8-block evidence feature vector computation
- [ ] T011 [P] Implement `backend/server/modules/verifier/classifier.py` — GaussianProcessClassifier + CalibratedClassifierCV wrapper
- [ ] T012 [P] Implement `backend/server/modules/verifier/calibration.py` — probability calibration with isotonic regression
- [ ] T013 [P] Implement `backend/server/modules/verifier/conformal.py` — MAPIE split conformal prediction (LAC/APS)
- [ ] T014 [P] Implement `backend/server/modules/eav/controller.py` — deterministic EAV policy (clarify vs retrieve decision)
- [ ] T015 [P] Implement `backend/server/modules/eav/clarify.py` — bounded clarification action
- [ ] T016 [P] Implement `backend/server/modules/eav/retrieve.py` — targeted retrieval / adjacent-page expansion action
- [ ] T017 [P] Implement `backend/server/modules/output/doubt_certificate.py` — Doubt Certificate construction per contract schema
- [ ] T018 [P] Implement `backend/server/modules/output/safety_response.py` — emergency safety response per Article IV
- [ ] T019 [P] Implement `backend/server/modules/output/answer.py` — cited answer composer for singleton {SUPPORTED} path
- [ ] T020 [P] Implement `backend/server/modules/artifacts/run_artifact.py` — structured run artifact with PII redaction per contract schema
- [ ] T021 Prepare frozen corpus: download MIRAGE/PubMed subset + generate synthetic adversarial cases (30-50 cases)
- [ ] T022 Train and calibrate verifier on labeled claim-evidence pairs, produce calibration artifact

**Checkpoint**: Foundation ready — all schemas, modules, corpus, and calibration artifact exist. User story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Receive a cited answer when evidence supports the claim (Priority: P1) 🎯 MVP

**Goal**: When evidence supports a claim, the system returns a cited answer with conformal set {SUPPORTED}

**Independent Test**: Submit a question whose answer is directly entailed by a single approved passage. Verify the response contains the answer, a citation, and a conformal status of {SUPPORTED}.

- [ ] T023 [P] [US1] Extend `backend/server/routes/ask_question.py` — insert UQ pipeline after retrieval, before existing RAG chain (Q6 integration point)
- [ ] T024 [US1] Extend `backend/server/modules/query_handlers.py` — add UQ pipeline orchestration: safety gate → retrieval → claim decomposition → verifier → conformal → answer/doubt/EAV/safety
- [ ] T025 [US1] Implement `{SUPPORTED}` path in `backend/server/modules/output/answer.py` — compose cited answer with claim IDs and citation references
- [ ] T026 [US1] Update `QuestionResponse` schema in `backend/server/schemas.py` — add optional `doubt_certificate`, `run_artifact_id`; make `response` nullable
- [ ] T027 [US1] Integrate run artifact recording in `backend/server/routes/ask_question.py` — log all decisions, redact PII, store artifact
- [ ] T028 [US1] Validate Scenario 2 from quickstart.md: C0 system answers a supported question with singleton {SUPPORTED}

**Checkpoint**: User Story 1 is fully functional. Cited answers with {SUPPORTED} conformal sets are returned. Run artifacts are recorded.

---

## Phase 4: User Story 2 - Receive an explicit non-answer when evidence is insufficient (Priority: P1)

**Goal**: When evidence is insufficient or conflicting, the system returns a Doubt Certificate instead of fabricating an answer

**Independent Test**: Submit a question outside the approved corpus scope or with no supporting passage. Verify the response is a Doubt Certificate containing the uncertainty causes, conformal set, and evidence needed, with no fabricated medical claims.

- [ ] T029 [P] [US2] Implement non-singleton conformal set handling in `backend/server/modules/query_handlers.py` — map {REFUTED}, {INSUFFICIENT}, and multi-label sets to abstention
- [ ] T030 [P] [US2] Implement `cross_source_conflict` detection in `backend/server/modules/claims/feature_vector.py` — identify when retrieved passages contradict each other
- [ ] T031 [US2] Implement Doubt Certificate generation in `backend/server/modules/output/doubt_certificate.py` — populate uncertainty_causes, conformal_set, evidence_needed, human_review_recommended per contract schema
- [ ] T032 [US2] Update `backend/server/routes/ask_question.py` — return Doubt Certificate when conformal set is non-singleton and EAV budget exhausted
- [ ] T033 [US2] Validate Scenarios 3 and 4 from quickstart.md: C0 system abstains on unsupported and conflicting questions

**Checkpoint**: User Stories 1 AND 2 both work independently. System shows cited answers for supported claims and Doubt Certificates for unsupported/conflicting claims.

---

## Phase 5: User Story 3 - Resolve ambiguity with one bounded action (Priority: P2)

**Goal**: When the conformal set is ambiguous, the system performs exactly one bounded uncertainty-reduction action (clarify or retrieve)

**Independent Test**: Submit a question with a missing dosage or date qualifier. Verify the system asks exactly one bounded clarification or performs one targeted retrieval, then either answers or returns a Doubt Certificate.

- [ ] T034 [P] [US3] Implement EAV policy logic in `backend/server/modules/eav/controller.py` — predict whether one action is likely to collapse ambiguous conformal set
- [ ] T035 [P] [US3] Implement clarification action in `backend/server/modules/eav/clarify.py` — generate bounded clarification question for missing entity/date/scope
- [ ] T036 [P] [US3] Implement targeted retrieval action in `backend/server/modules/eav/retrieve.py` — perform adjacent-page expansion or refined query
- [ ] T037 [US3] Wire EAV into `backend/server/modules/query_handlers.py` — invoke at most once per execution, record action in run artifact, recompute conformal set after action
- [ ] T038 [US3] Update `backend/server/routes/ask_question.py` and `frontend/app.py` — handle clarification round-trip: backend returns clarification question in Doubt Certificate, frontend displays it, user submits answer, backend re-runs UQ pipeline with clarified input
- [ ] T039 [US3] Validate Scenario 6 from quickstart.md: EAV controller resolves ambiguity with one bounded action

**Checkpoint**: User Stories 1, 2, AND 3 all work independently. EAV controller performs one bounded action and records productivity in run artifact.

---

## Phase 6: User Story 4 - Emergency queries bypass synthesis (Priority: P2)

**Goal**: Emergency queries bypass retrieval, generation, and verification entirely, returning a safety response in <2s

**Independent Test**: Submit a query containing emergency indicators. Verify the response is a safety message, no retrieval or generation occurred, and the run artifact records the safety escalation.

- [ ] T040 [P] [US4] Implement emergency detection in `backend/server/modules/safety/gate.py` — regex/keyword patterns for immediate emergency indicators
- [ ] T041 [US4] Implement `backend/server/modules/output/safety_response.py` — concise safety message directing user to emergency services
- [ ] T042 [US4] Wire emergency bypass in `backend/server/routes/ask_question.py` — activate before retrieval, skip RAG chain, return safety response
- [ ] T043 [US4] Validate Scenario 5 from quickstart.md: emergency query bypasses synthesis with <2s latency

**Checkpoint**: User Stories 1–4 all work independently. Emergency queries bypass all synthesis and return safety responses in <2s.

---

## Phase 7: User Story 5 - Reviewer inspects a complete audit trail (Priority: P3)

**Goal**: Every execution produces a complete run artifact containing all inputs, decisions, and outputs, redacted for safe sharing

**Independent Test**: After any run, inspect the run artifact. Verify it contains all decision inputs and outputs, is redacted of sensitive values, and is sufficient to reconstruct the final decision without re-running the system.

- [ ] T044 [P] [US5] Implement run artifact redaction in `backend/server/modules/artifacts/run_artifact.py` — strip PII, sensitive values, raw keys before storage/sharing
- [ ] T045 [US5] Implement run artifact inspection CLI in `backend/scripts/` — commands to summarize, inspect conflicts, show EAV actions, check safety bypass
- [ ] T046 [US5] Validate Scenario 1 from quickstart.md: existing baseline runs unchanged
- [ ] T047 [US5] Validate Scenario 7 from quickstart.md: full evaluation on PubMedQA + synthetic adversarial set
- [ ] T048 [US5] Generate Improvement Changelog entries for each phase transition (C0 baseline → US1 → US2 → US3 → US4 → US5)
- [ ] T049 [P] [US5] Evaluate selective risk on held-out test set: measure unsupported material-claim rate in shown answers, verify ≤10% (SC-001)
- [ ] T050 [P] [US5] Measure empirical coverage at 90% target conformal coverage level on held-out test set, verify ≥70% (SC-002)
- [ ] T051 [P] [US5] Measure unsupported material-claim rate in shown answers on held-out test set, verify <10% (SC-003)

**Checkpoint**: All user stories complete. Full audit trail exists for every execution. Improvement Changelog documents all iterations. All success criteria measured and passing.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T052 [P] Update `backend/README.md` with CURA-Med extension overview, architecture diagram, and usage instructions
- [ ] T053 [P] Update `backend/server/requirements.txt` with exact versions for all new dependencies
- [ ] T054 Validate all 7 quickstart.md scenarios end-to-end
- [ ] T055 Run reproducibility check from clean environment per quickstart.md
- [ ] T056 Update `specs/001-sourceproof-medical/quickstart.md` with actual commands and expected output from implemented system
- [ ] T057 Verify all contract schemas in `specs/001-sourceproof-medical/contracts/` match implemented output
- [ ] T058 Record agent trajectories for each user story per Article XIX
- [ ] T059 Generate final Improvement Changelog with all iterations, removed experiments, and lessons learned per Article XVIII

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately
- **Phase 2 (Foundational)**: Depends on Setup completion — **BLOCKS all user stories**
- **Phase 3+ (User Stories)**: All depend on Foundational phase completion
  - User stories can proceed sequentially in priority order (US1 → US2 → US3 → US4 → US5)
  - US1 and US2 are both P1 and can proceed in parallel after Phase 2 if staffed
- **Phase 8 (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories. **MVP.**
- **US2 (P1)**: Can start after Phase 2 — independently testable, no dependency on US1
- **US3 (P2)**: Can start after Phase 2 — depends on US2's Doubt Certificate infrastructure for abstention path
- **US4 (P2)**: Can start after Phase 2 — independently testable, no dependency on other stories
- **US5 (P3)**: Can start after Phase 2 — depends on US1–US4 for complete audit trail coverage

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1**: T001, T002, T003 can run in parallel (different files/operations)
- **Phase 2**: T005–T020 can run in parallel (different module files, no dependencies)
- **Phase 3 (US1)**: T023, T024, T025, T026, T027, T028 can run in parallel where files differ
- **Phase 4 (US2)**: T029, T030, T031, T032, T033 can run in parallel where files differ
- **Phase 5 (US3)**: T034, T035, T036, T037, T038, T039 can run in parallel where files differ
- **Phase 6 (US4)**: T040, T041, T042, T043 can run in parallel where files differ
- **Phase 7 (US5)**: T044, T045, T046, T047, T048 can run in parallel where files differ
- **Phase 8**: T049, T050, T051, T052, T053, T054, T055, T056 can run in parallel where files differ

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all foundational module implementations in parallel:
Task T005: safety/gate.py
Task T006: safety/isolation.py
Task T007: corpus/loader.py
Task T008: corpus/hash.py
Task T009: claims/composer.py
Task T010: claims/feature_vector.py
Task T011: verifier/classifier.py
Task T012: verifier/calibration.py
Task T013: verifier/conformal.py
Task T014: eav/controller.py
Task T015: eav/clarify.py
Task T016: eav/retrieve.py
Task T017: output/doubt_certificate.py
Task T018: output/safety_response.py
Task T019: output/answer.py
Task T020: artifacts/run_artifact.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 independently — submit supported question, verify cited answer with {SUPPORTED}
5. Demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Demo (MVP!)
3. Add US2 → Test independently → Demo (abstention working)
4. Add US3 → Test independently → Demo (EAV working)
5. Add US4 → Test independently → Demo (safety bypass working)
6. Add US5 → Test independently → Demo (audit trail complete)
7. Polish → Final submission

### Parallel Team Strategy

With multiple developers:
1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (P1) + US2 (P1) in parallel
   - Developer B: US3 (P2) + US4 (P2) in parallel
   - Developer C: US5 (P3)
3. Stories complete and integrate independently

---

## Notes

- **[P]** tasks = different files, no dependencies on incomplete tasks
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Total task count: 59
