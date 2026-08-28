# Feature Specification: SourceProof Medical / CURA-Med

**Feature Branch**: `001-sourceproof-medical`

**Created**: 2026-08-28

**Status**: Draft

**Input**: User description: "Build a medical information assistant that produces evidence-constrained, uncertainty-aware answers from an approved corpus, with abstention when evidence is insufficient, conformal prediction for calibrated confidence, and a one-step uncertainty-reduction policy."

## Clarifications

### Session 2026-08-28

- Q: What baseline approach should we compare against? → A: Dense retrieval + generic RAG with filename citations, no claim decomposition, no evidence verification, no conformal prediction, and no abstention. Same corpus and model family as the advanced system.
- Q: What corpus should we use? → A: Two-part corpus: (1) MIRAGE/PubMed abstract subset for external benchmark comparability, and (2) a synthetic adversarial case set for stress-testing abstention, contradictions, retrieval failure, and EAV behavior.
- Q: Which external benchmark should be the primary evaluation venue? → A: PubMedQA primary (1,000 expert-labeled yes/no/maybe + long answer questions), supplemented by MIRAGE benchmark retrieval metrics, and the synthetic adversarial set for UQ-specific stress tests.
- Q: How should the three-way verifier be implemented? → A: Machine learning classifier preferred. Gaussian process classifier suggested by project owner as easy to train. Calibrated probabilities are required for conformal prediction. If training data is insufficient, fallback to prompted LLM with structured output noted as prototype limitation.
- Q: What is the model access constraint? → A: Priority order is (1) HuggingFace example model if available, (2) ML methods such as Gaussian process classifier, (3) black-box LLM API as fallback. Feature-Gap signals remain optional and only used if a local open-weight model is selected.
- Q: Where does the UQ pipeline insert into the existing /ask/ route, and what is the new response schema? → A: Insert UQ after retrieval but before the existing RAG chain. New QuestionResponse extends with optional doubt_certificate and run_artifact_id fields. response becomes nullable when a Doubt Certificate or safety response is returned.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive a cited answer when evidence supports the claim (Priority: P1)

A medical learner asks a well-formed question about an approved corpus topic. The system retrieves relevant passages, decomposes the answer into atomic claims, verifies each claim against the evidence, and returns a cited answer because the conformal decision set is singleton SUPPORTED.

**Why this priority**: This is the primary value delivery. Without it, the system has no useful output.

**Independent Test**: Submit a question whose answer is directly entailed by a single approved passage. Verify the response contains the answer, a citation, and a conformal status of {SUPPORTED}.

**Acceptance Scenarios**:

1. **Given** an approved corpus and a valid question directly answered by one passage, **When** the learner submits the question, **Then** the system returns a cited answer with conformal set {SUPPORTED} and the claim is directly entailed by the cited passage.
2. **Given** the same question, **When** the learner re-runs the query, **Then** the system returns the same answer and citation with a stable run artifact.

---

### User Story 2 - Receive an explicit non-answer when evidence is insufficient (Priority: P1)

A learner asks a question that cannot be reliably answered from the approved corpus. The system detects insufficient or conflicting evidence, the conformal set is not singleton SUPPORTED, and after at most one bounded uncertainty-reduction action the set remains ambiguous. The system returns a Doubt Certificate with structured uncertainty causes instead of fabricating an answer.

**Why this priority**: Abstention is the product's safety guarantee. A system that fabricates fluent but unsupported answers is worse than no system.

**Independent Test**: Submit a question outside the approved corpus scope or with no supporting passage. Verify the response is a Doubt Certificate containing the uncertainty causes, conformal set, and evidence needed, with no fabricated medical claims.

**Acceptance Scenarios**:

1. **Given** a question with no supporting passage in the approved corpus, **When** the learner submits the question, **Then** the system returns a Doubt Certificate with conformal set containing INSUFFICIENT and does not invent medical facts.
2. **Given** a question answered by conflicting passages, **When** the learner submits the question, **Then** the system returns a Doubt Certificate with uncertainty_cause type `cross_source_conflict` and preserves both conflicting sources.

---

### User Story 3 - Resolve ambiguity with one bounded action (Priority: P2)

A learner submits an ambiguous question (missing qualifier, entity, or scope). The system identifies the ambiguity through the evidence feature vector, invokes the EAV controller, and performs exactly one clarification request or targeted retrieval. If the action resolves the conformal set to {SUPPORTED}, the learner receives a cited answer. If not, the system returns a Doubt Certificate.

**Why this priority**: This is the differentiating feature. It demonstrates adaptive uncertainty reduction without unbounded agent loops.

**Independent Test**: Submit a question with a missing dosage or date qualifier. Verify the system asks exactly one bounded clarification or performs one targeted retrieval, then either answers or returns a Doubt Certificate.

**Acceptance Scenarios**:

1. **Given** a question missing a required date qualifier and an unused action budget, **When** the EAV controller predicts positive value for a clarification, **Then** the system asks one bounded clarification question, recomputes the verifier and conformal set, and either answers or abstains.
2. **Given** a question missing a required entity and an unused action budget, **When** the EAV controller predicts positive value for targeted retrieval, **Then** the system performs exactly one targeted retrieval, recomputes the verifier and conformal set, and either answers or abstains.
3. **Given** a question where the EAV action does not resolve ambiguity, **When** the conformal set remains non-singleton after the action, **Then** the system returns a Doubt Certificate and records the action in the run artifact.

---

### User Story 4 - Emergency queries bypass synthesis (Priority: P2)

A user submits a query indicating a possible immediate emergency. The system bypasses retrieval, generation, and verification entirely and returns a concise safety response directing the user to local emergency services or urgent qualified care.

**Why this priority**: Emergency bypass is a hard safety requirement. It must never be delayed by document retrieval or model generation.

**Independent Test**: Submit a query containing emergency indicators. Verify the response is a safety message, no retrieval or generation occurred, and the run artifact records the safety escalation.

**Acceptance Scenarios**:

1. **Given** a query indicating a possible immediate emergency, **When** the safety gate activates, **Then** the system returns a safety response, does not retrieve documents, does not call the generator, and records the escalation in the run artifact.

---

### User Story 5 - Reviewer inspects a complete audit trail (Priority: P3)

A qualified reviewer examines a run artifact for any query. The artifact contains the question, retrieved evidence, atomic claims, evidence feature vector, verifier probabilities, conformal set, any EAV actions taken, uncertainty causes, and the final decision. The reviewer can determine why the system answered, abstained, or requested clarification without re-running the query.

**Why this priority**: Required for reproducibility, judging, and trust. Secondary to delivering correct answers but essential for submission quality.

**Independent Test**: After any run, inspect the run artifact. Verify it contains all decision inputs and outputs, is redacted of sensitive values, and is sufficient to reconstruct the final decision.

**Acceptance Scenarios**:

1. **Given** a completed run, **When** a reviewer opens the run artifact, **Then** the artifact contains the question, corpus ID, model version, retrieval results, claims, evidence features, verifier output, conformal set, any EAV actions, and the final decision, with no raw sensitive values.
2. **Given** a run that invoked EAV, **When** a reviewer inspects the artifact, **Then** the artifact records the uncertainty cause, the action taken, and whether it changed the final decision.

---

### Edge Cases

- What happens when the calibration artifact is missing or stale?
- What happens when the corpus has no approved documents?
- What happens when a document in the corpus contains prompt-injection instructions addressed to the system?
- What happens when two approved documents conflict on a medically material point?
- What happens when the question requires a multi-hop inference not supported by a single passage?
- What happens when the user asks for diagnosis, prescription, or patient-specific risk?
- What happens when the verifier fails or returns an empty conformal set?
- What happens when the question is ambiguous but the action budget has already been used?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a question against a named approved corpus consisting of the MIRAGE/PubMed abstract subset plus the synthetic adversarial case set.
- **FR-002**: System MUST enforce a privacy and medical-scope gate before retrieval: emergency queries MUST escalate to safety response; personal diagnosis, prescription, and patient-specific risk queries MUST be rejected with a scope explanation.
- **FR-003**: System MUST perform corpus-scoped retrieval and return a versioned evidence packet containing retrieved passages, chunk IDs, retrieval metadata, and provenance.
- **FR-004**: System MUST decompose the answer into atomic claims, each with stable claim IDs and citation references to the evidence packet.
- **FR-005**: System MUST compute an evidence feature vector for each claim-passage pair, covering local entailment, claim coverage, retrieval quality, conflict, provenance, query ambiguity, and system state.
- **FR-006**: System MUST run a three-way claim-evidence verifier (SUPPORTED / REFUTED / INSUFFICIENT) over each claim and its cited evidence, producing calibrated probabilities.
- **FR-007**: System MUST apply split conformal classification (LAC or APS) to convert calibrated probabilities into a prediction set for each claim.
- **FR-008**: System MUST treat a singleton conformal set {SUPPORTED} as sufficient to present the claim with its citation.
- **FR-009**: System MUST treat any non-singleton conformal set as ambiguous and MUST NOT present the claim as a supported answer.
- **FR-010**: System MUST invoke the EAV controller at most once when the conformal set is ambiguous, selecting either one bounded clarification or one targeted retrieval action.
- **FR-011**: System MUST return a Doubt Certificate when the conformal set remains ambiguous after the EAV action budget is exhausted or when no action is warranted, including structured uncertainty causes, conformal set, coverage target, and evidence needed.
- **FR-012**: System MUST record a run artifact for every execution containing: question, corpus ID, model and verifier versions, retrieval decisions, claims, evidence features, verifier output, conformal sets, EAV actions taken, and the final decision.
- **FR-013**: System MUST redact sensitive values from run artifacts and trajectories before storage or sharing.
- **FR-014**: System MUST treat retrieved passages, document metadata, and user text as untrusted data and MUST NOT execute instructions contained within them.
- **FR-015**: System MUST validate that the calibration artifact, feature schema, corpus family, and model version are compatible at startup and MUST fail closed if any mismatch is detected.

### Key Entities

- **Question**: User-submitted query with redacted PII, scope classification, and ambiguity flags.
- **Corpus**: Frozen two-part collection. Part 1 is the MIRAGE/PubMed abstract subset for external benchmark comparability. Part 2 is a synthetic adversarial case set for stress-testing abstention, contradictions, retrieval failure, and EAV behavior. Each part has a stable corpus ID, version, and hash.
- **Evidence Packet**: Versioned collection of retrieved passages with chunk IDs, document provenance, retrieval metadata, and corpus hash.
- **Claim**: Atomic medically material statement with a stable ID, text, citation references, and verifier output.
- **Evidence Feature Vector**: Per-claim aggregation of entailment, coverage, retrieval quality, conflict, provenance, query ambiguity, and system-state signals.
- **Conformal Decision Set**: Predicted label set (from {SUPPORTED, REFUTED, INSUFFICIENT}) at a declared coverage target, produced by split conformal classification.
- **Doubt Certificate**: Structured abstention record containing status, probability semantics, conformal set, uncertainty causes, actions taken, evidence needed, corpus and calibration IDs, and human review recommendation.
- **Run Artifact**: Immutable record of a single execution containing all inputs, intermediate artifacts, decisions, and outputs, with sensitive values redacted.
- **Calibration Artifact**: Versioned bundle of trained verifier, probability calibrator, conformal predictor, feature schema, and metadata required for runtime inference.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Of the answers the system chooses to show, no more than 10% contain unsupported material claims (selective risk at 90% coverage).
- **SC-002**: The system achieves at least 70% empirical coverage at the 90% target conformal coverage level on the held-out test set.
- **SC-003**: The unsupported material-claim rate in shown answers is below 10% on the held-out test set.
- **SC-004**: The EAV controller produces a productive action (collapses ambiguous set to correct singleton or correct abstention) on at least 50% of ambiguous cases where one action is taken.
- **SC-005**: Emergency and out-of-scope queries receive a safety or scope response within 2 seconds, with no retrieval or generation calls.
- **SC-006**: A second person can run the baseline, C0, and A0 configurations on the frozen test corpus and reproduce the primary metrics within documented variance.
- **SC-007**: The run artifact for any execution contains all inputs, intermediate decisions, and outputs needed to reconstruct the final answer or abstention without re-running the system.

## Assumptions

- The approved corpus consists of two frozen parts: (1) the MIRAGE/PubMed abstract subset, drawn from public biomedical literature with clear licensing, and (2) a synthetic adversarial case set constructed by the project team for stress-testing abstention, contradictions, retrieval failure, and EAV behavior. Neither part contains real patient data.
- A qualified medical reviewer is available to approve the corpus, labels, safety behavior, and final evaluation before any consequential use.
- The evaluation corpus contains at least 30 claim-evidence pairs across the three verifier classes, with sufficient examples in each class for conformalization.
- The baseline uses a standard dense retrieval plus generic RAG pipeline with the same corpus and model family as the advanced system.
- Model access supports at least one black-box or local LLM; Feature-Gap hidden-state signals are optional and only used if a local open-weight model is selected.
- Ten or more evaluation cases are feasible; if fewer are available, the result is presented as a prototype with disclosed sample-size limitations.
