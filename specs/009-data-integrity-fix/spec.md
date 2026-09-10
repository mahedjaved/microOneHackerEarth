# Feature Specification: data-integrity-fix

**Feature Branch**: `009-data-integrity-fix`

**Created**: 2026-09-10

**Status**: Draft

**Input**: User description: "Fix two blocking data-integrity issues before any further comparative analysis: (1) MedRAG baseline retrieval wiring — verify retrieved passages are actually injected into the prompt and responses cite the document; (2) Provider fallback chain — replace multi-provider fallback with a single working primary provider (Groq) to eliminate 60s timeouts from burning through broken providers. Re-run 5-case subset and manually inspect responses. Deprioritize top_k experiment until these are fixed."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify and fix MedRAG baseline retrieval wiring (Priority: P1)

As a developer validating comparative study integrity, I want `medrag_baseline.py` to actually inject retrieved passages into the LLM prompt, so MedRAG responses cite the real document instead of falling back to general knowledge.

**Why this priority**: The feedback shows MedRAG responses starting with "I don't have access to the specific aspirin document" and answering from general knowledge. This makes the entire UQ-RAG vs MedRAG comparison invalid — one side isn't running the system it's supposed to represent.

**Independent Test**: Diff `medrag_baseline.py` against the last known-good version from `007-numeric-containment-feature`. Run 5 test cases, extract the actual prompt sent to the LLM, and verify retrieved passage text appears in the prompt. Verify responses cite document-specific facts (e.g., "650 mg" for aspirin) rather than generic knowledge.

**Acceptance Scenarios**:

1. **Given** `medrag_baseline.py` is called, **When** the LLM prompt is constructed, **Then** the prompt contains retrieved passage text from Pinecone, not an empty or generic context.
2. **Given** a document-specific question is asked, **When** MedRAG responds, **Then** the response cites facts from the retrieved document (e.g., "650 mg") rather than generic medical knowledge (e.g., "1000 mg OTC max").
3. **Given** the retrieval wiring is fixed, **When** the 5-case subset is run, **Then** every MedRAG response references the uploaded document.

---

### User Story 2 - Replace multi-provider fallback with single working primary provider (Priority: P1)

As a developer investigating pipeline latency, I want to replace the 4-provider fallback chain (Gemini → Groq → OpenCodeZen → Kilo) with a single working primary provider (Groq), so requests complete in single-digit seconds instead of timing out at 60s.

**Why this priority**: The timing report shows 60s latencies from burning through broken providers. Adding more fallbacks doesn't solve the problem — it adds latency. A single working provider with a valid key is the correct fix.

**Independent Test**: Configure Groq as the sole primary LLM provider with a valid API key. Run 5 test cases and verify all complete in <10s with no fallback chain activation.

**Acceptance Scenarios**:

1. **Given** Groq is configured as the primary provider with a valid key, **When** a request is made, **Then** the response completes in <10s without falling back to other providers.
2. **Given** the fallback chain is removed, **When** the 5-case subset is run, **Then** no log entries show "Gemini unavailable", "OpenCodeZen unavailable", or "Kilo unavailable".
3. **Given** Groq is the sole provider, **When** latency is measured, **Then** per-request latency is consistent and in the single-digit seconds range.

---

### User Story 3 - Re-run 5-case subset and manually inspect responses (Priority: P2)

As a developer validating data integrity, I want to re-run the 5-case subset after fixes and manually inspect each response, so I can confirm MedRAG cites the real document, UQ-RAG abstention behavior is correct, and latency is normal.

**Why this priority**: Automated scores don't catch systematic prompt-injection failures or broken retrieval. Manual inspection of actual response text is necessary to validate the fixes.

**Independent Test**: Run D1-D5 with the fixed MedRAG and single-provider setup. Read each response and verify: MedRAG cites document facts, UQ-RAG abstains appropriately, and latency is <10s per case.

**Acceptance Scenarios**:

1. **Given** the fixes are applied, **When** D1-D5 are run, **Then** MedRAG responses cite "650 mg" for aspirin questions, not generic "1000 mg" knowledge.
2. **Given** UQ-RAG is tested, **When** evidence is insufficient, **Then** it abstains with a Doubt Certificate; when evidence is sufficient, **Then** it provides a cited answer.
3. **Given** latency is measured, **When** the 5 cases complete, **Then** no case exceeds 10s total latency.

---

### User Story 4 - Deprioritize top_k experiment until data integrity is confirmed (Priority: P2)

As a developer managing investigation scope, I want to deprioritize the `top_k` experiment until MedRAG retrieval and provider fallback are fixed, so we don't waste time on a secondary question while primary data integrity issues remain unresolved.

**Why this priority**: The feedback explicitly states: "I'd deprioritize the top_k experiment specifically — it's looking like a smaller effect than the verifier training-data problem."

**Independent Test**: Document the decision in the spec and do not run `top_k=2` vs `top_k=5` comparisons until Stories 1-3 are complete.

**Acceptance Scenarios**:

1. **Given** Stories 1-3 are incomplete, **When** someone proposes a `top_k` experiment, **Then** it is deferred until data integrity is confirmed.
2. **Given** Stories 1-3 are complete, **When** the team revisits `top_k`, **Then** it is run as a separate, smaller experiment on the fixed baseline.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `backend/server/routes/medrag_baseline.py` MUST query Pinecone, build `Document` objects from matches, join `page_content` into context, and inject that context into the LLM prompt.
- **FR-002**: `backend/server/routes/medrag_baseline.py` MUST NOT fall back to general LLM knowledge when retrieved passages are present — the prompt must contain the actual retrieved text.
- **FR-003**: `backend/server/modules/llm.py` MUST use Kilo as the primary LLM provider with a valid API key; other providers MUST be commented out, not deleted.
- **FR-004**: The LLM fallback chain (Groq → OpenCodeZen → Gemini) MUST be commented out in code, preserving the logic for future re-enablement.
- **FR-005**: A 5-case subset (D1-D5) MUST be run after fixes and each response MUST be manually inspected for document citation correctness.
- **FR-006**: Latency per request MUST be <10s after fixes; any request exceeding this threshold MUST be investigated.
- **FR-007**: The `top_k` experiment MUST be deprioritized until Stories 1-3 are complete and verified.

### Key Entities *(include if feature involves data)*

- **MedRAGResponse**: Dict with fields: `response` (actual LLM text), `sources` (list of cited document paths), `retrieval_scores` (list of Pinecone scores), `context_used` (the actual prompt context injected).
- **ProviderChain**: The ordered list of LLM providers; after this fix, Kilo MUST be primary and other providers MUST be commented out in code.
- **LatencyMeasurement**: Dict with fields: `test_case_id`, `provider`, `elapsed_seconds`, `fallback_triggered` (bool).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: MedRAG responses for D1-D5 cite document-specific facts (e.g., "650 mg") rather than generic knowledge.
- **SC-002**: The LLM prompt for MedRAG contains retrieved passage text from Pinecone, verified by inspecting the actual prompt or response.
- **SC-003**: All 5 test cases complete in <10s with Kilo as the primary provider; no fallback chain activation.
- **SC-004**: No log entries show "Groq unavailable", "OpenCodeZen unavailable", or "Gemini unavailable" during the 5-case run; Kilo is the only active provider.
- **SC-005**: UQ-RAG abstention behavior is unchanged or improved; abstention reasons are traceable to specific evidence issues.
- **SC-006**: The `top_k` experiment is explicitly deferred until data integrity is confirmed.

## Assumptions

- A valid Kilo API key is available and configured in `backend/.env`; Kilo MUST be the primary provider for this investigation.
- The last known-good version of `medrag_baseline.py` is from branch `007-numeric-containment-feature`; if that branch is unavailable, the current version will be audited directly.
- Manual inspection of 5 cases is sufficient to detect systematic retrieval-wiring failures; a full 36-case run is not required for this validation.
- Commenting out the fallback chain is acceptable even if it reduces "resilience" — the current chain is not resilient, it is noisy.
