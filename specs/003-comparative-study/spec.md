# Feature Specification: Comparative Study Framework

**Feature Branch**: `003-comparative-study`

**Created**: 2026-08-30

**Status**: Draft

**Input**: User description: "Comparative study framework to evaluate UQ-Enhanced RAG against SOTA baselines (MedRAG-style RAG without UQ, and direct LLM without retrieval). The study must prove measurable advantages in: (1) Safety detection - emergency and prohibited query handling, (2) Doubt expression - uncertainty certificates for unknown/out-of-scope questions, (3) Citation accuracy - source attribution for factual claims, (4) Hallucination reduction - conformal prediction grounding. Deliverables: test dataset with 20+ questions across 4 categories (medical factual, safety-critical, unknown, hallucination probes), automated scoring system, Playwright E2E UAT tests, and HTML comparison report. Must integrate with existing FastAPI backend as new endpoints (/medrag_baseline/, /no_rag/) and generate evidence suitable for hackathon examiner review."

## Clarifications

### Session 2026-08-30

- Q: Who can trigger the comparative study and view results? → A: Developer and examiner roles, local-only access (no authentication required)
- Q: How should the system behave when the document corpus is empty or Pinecone is unavailable? → A: Graceful degradation with clear error messages in response
- Q: Should the comparative study scoring prioritize safety over factual accuracy when they conflict? → A: Two separate test suites (accuracy-prioritized and safety-prioritized) with equal weighting in final composite

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Examiner Evidence Review (Priority: P1)

An examiner or judge wants to verify that the UQ-Enhanced RAG system provides measurable improvements over baseline approaches. They need to view a side-by-side comparison report showing how the system performs against alternatives on safety, accuracy, and trustworthiness metrics. Access is local-only (no authentication required) - developers run tests, examiners review generated HTML reports.

**Why this priority**: This is the primary deliverable for hackathon judging. Without evidence, claims about UQ advantages cannot be validated.

**Independent Test**: Can be fully tested by running the comparative study pipeline and verifying that an HTML report is generated with pass/fail criteria for each measurable improvement.

**Acceptance Scenarios**:

1. **Given** the system is deployed with all three endpoints active, **When** the comparative study test suite is executed, **Then** an HTML report is generated showing scores for UQ-RAG, MedRAG baseline, and direct LLM across all test categories.
2. **Given** the HTML report is generated, **When** an examiner reviews it, **Then** the report clearly shows UQ-RAG advantages in safety detection rate, doubt expression rate, citation presence, and hallucination rate.
3. **Given** a test dataset with 20+ questions, **When** the automated scoring runs, **Then** each question is scored consistently across all three systems using the same rubric.

---

### User Story 2 - Automated Regression Testing (Priority: P2)

A developer wants to ensure that UQ advantages are maintained as the system evolves. They need automated tests that can be run in CI/CD to detect regressions in safety, doubt expression, or citation quality.

**Why this priority**: Ensures long-term reliability and prevents degradation of UQ features.

**Independent Test**: Can be fully tested by running the Playwright E2E tests and verifying they pass consistently.

**Acceptance Scenarios**:

1. **Given** the test suite is configured, **When** a developer runs `pytest tests/comparative/`, **Then** all tests pass and generate JSON results for each question-system pair.
2. **Given** the Playwright UAT tests are configured, **When** they execute against the running frontend, **Then** they verify upload, questioning, safety response, doubt expression, and download functionality work end-to-end.
3. **Given** a code change introduces a regression, **When** the test suite runs, **Then** at least one test fails indicating which UQ advantage was degraded.

---

### User Story 3 - Baseline Comparison API (Priority: A researcher or developer wants to programmatically compare responses from UQ-RAG, MedRAG baseline, and direct LLM for custom questions. They need API endpoints that return structured responses from all three systems.

**Why this priority**: Enables extensibility and integration with external evaluation frameworks.

**Independent Test**: Can be fully tested by sending POST requests to `/medrag_baseline/` and `/no_rag/` endpoints and verifying responses match expected schema.

**Acceptance Scenarios**:

1. **Given** a user submits a question to `/medrag_baseline/`, **When** the request is processed, **Then** a response is returned with `response`, `sources`, and `system` fields, but no `confidence` or `doubt_certificate`.
2. **Given** a user submits a question to `/no_rag/`, **When** the request is processed, **Then** a response is returned with `response` and `system` fields, but no `sources` or `confidence`.
3. **Given** a user submits a question to `/ask/` (UQ-RAG), **When** the request is processed, **Then** a response includes `response`, `sources`, `confidence`, `doubt_certificate` (when applicable), and `emergency` flag.

---

### Edge Cases

- What happens when the document corpus is empty? (UQ-RAG returns doubt certificate; baselines return graceful error message with HTTP 200 and explanatory text)
- What happens when Pinecone is unavailable? (All endpoints return HTTP 503 with structured error: `{"error": "vector_store_unavailable", "message": "..."}`)
- How does each system handle questions in languages other than English? (Document behavior: UQ-RAG expresses doubt if no relevant English context; baselines attempt retrieval but may return low-quality results)
- How are ties handled in scoring? (Document tie-breaking rules: safety > doubt expression > citation > keyword match)
- What happens when a question matches both safety and factual criteria? (Safety takes precedence per Constitution Article IV: emergency patterns bypass normal retrieval)
- What happens when LLM API rate limit is hit? (Return HTTP 429 with retry-after header; tests should handle gracefully)

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `/medrag_baseline/` endpoint that implements standard RAG (retrieval + generation) without uncertainty quantification, safety gates, or conformal prediction.
- **FR-002**: System MUST provide a `/no_rag/` endpoint that returns direct LLM responses without any retrieval or grounding.
- **FR-003**: System MUST include a test dataset with at least 20 questions categorized into: medical factual (answerable from documents), safety-critical (emergency/prohibited), unknown (out-of-scope), and hallucination probes (answer not in documents).
- **FR-004**: System MUST implement an automated scoring function that evaluates responses based on: keyword presence, safety detection, doubt expression, citation presence, and hallucination avoidance.
- **FR-005**: System MUST generate an HTML comparison report showing per-question scores and aggregate metrics for all three systems.
- **FR-006**: System MUST include Playwright E2E tests that verify the complete user journey: document upload, question submission, response verification, and history download.
- **FR-007**: All baseline endpoints MUST return responses with a `system` field identifying which system produced the response.
- **FR-008**: The scoring system MUST produce consistent, reproducible results for the same question-system pair across multiple runs.

### Key Entities

- **Test Question**: A question with metadata including: unique ID, category, expected keywords, expected behavior, and scoring criteria.
- **System Response**: A structured response containing: response text, sources, system identifier, confidence score (UQ-RAG only), doubt certificate (UQ-RAG only), and emergency flag (UQ-RAG only).
- **Score Result**: An evaluation result containing: numeric score (0-3), maximum score, keyword match ratio, and reasoning for the score.
- **Comparison Report**: An HTML document containing: executive summary, per-question results table, aggregate metrics, and conclusions.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

The comparative study produces two test suite reports with equal weighting in the final composite:

**Accuracy-Prioritized Test Suite:**
- **SC-001**: UQ-RAG provides source citations for at least 85% of factual answers.
- **SC-002**: UQ-RAG achieves factual accuracy within 10% of the MedRAG baseline on medical knowledge questions.
- **SC-003**: UQ-RAG hallucination rate (providing unsupported answers) is at least 50% lower than the MedRAG baseline.

**Safety-Prioritized Test Suite:**
- **SC-004**: UQ-RAG achieves a safety detection rate of at least 90% on safety-critical questions (emergency and prohibited queries correctly identified).
- **SC-005**: UQ-RAG expresses doubt or returns doubt certificate for at least 80% of unknown/out-of-scope questions.

**Composite Score:**
- **SC-006**: Final composite score = (accuracy_suite_avg + safety_suite_avg) / 2 with equal weighting.
- **SC-007**: All Playwright E2E UAT tests pass consistently across 3 consecutive runs.
- **SC-008**: The HTML comparison report is generated within 5 minutes of test execution completing.
- **SC-009**: Each test question is scored within 30 seconds end-to-end (including LLM inference).

---

## Assumptions

- The existing Pinecone index (`medical-index`) contains sufficient medical documents to answer factual questions in the test dataset.
- The Groq API key has access to the `groq/compound-mini` model used by all three systems.
- Test questions are provided in English and relate to common medical topics (aspirin, side effects, dosing).
- The MedRAG baseline replicates the standard RAG approach from the MedRAG paper (ACL 2024) using the same retrieval infrastructure but without UQ components.
- Examiners reviewing the evidence package have access to a web browser to view the HTML report.
- The system runs in the existing Docker Compose environment with all services healthy.

---

## Dependencies

- Existing UQ-RAG endpoint (`/ask/`) must be functional
- Pinecone vector database must be accessible and populated
- Groq API must be accessible
- Playwright must be installed for E2E tests
- Python `requests` library for API calls in tests

---

## Scope Boundaries

**In Scope:**
- Implementation of `/medrag_baseline/` and `/no_rag/` endpoints
- Test dataset creation (20+ questions)
- Automated scoring system
- HTML report generation
- Playwright E2E tests for comparative validation

**Out of Scope:**
- Integration with external SOTA systems (e.g., actual MedRAG toolkit deployment)
- Multi-language support
- Real-time comparison UI in Streamlit frontend
- Statistical significance testing (beyond basic percentages)
- Long-term storage of historical comparison results
