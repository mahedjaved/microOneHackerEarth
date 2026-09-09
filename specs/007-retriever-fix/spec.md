# Feature Specification: retriever-fix

**Feature Branch**: `007-retriever-fix`

**Created**: 2026-09-08

**Status**: Draft

**Input**: User description: "Fix the retriever. There are two separate, deliberate cost-saving truncations stacked on top of each other in the live retrieval path, both explicitly flagged in the code's own comments, and both work directly against giving the verifier enough evidence to ever say SUPPORTED. Finding 1 — top_k=2, deliberately reduced. Finding 2 — passages hard-truncated to 500 characters, twice."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Increase retrieval depth to capture relevant evidence (Priority: P1)

As a medical RAG system, I want to retrieve at least 3-5 top matching chunks instead of 2, so that the verifier has access to the actual best evidence rather than missing it due to an arbitrary cost-cutting limit.

**Why this priority**: The current top_k=2 means that if the chunk that actually answers the question ranks 3rd by embedding similarity, the verifier never sees it. This is a fundamental evidence-starvation failure that makes the verifier's job impossible.

**Independent Test**: Run the comparative study on D1-D6 accuracy questions and verify that the retriever returns at least 3 chunks per query. Check that the correct answer appears in at least one of the retrieved chunks for questions where it was previously missing.

**Acceptance Scenarios**:

1. **Given** a medical question with a known answer in the corpus, **When** the retriever queries Pinecone, **Then** it returns at least 3 matches (top_k >= 3).
2. **Given** a question where the correct chunk ranks 3rd by similarity, **When** top_k=2 is used, **Then** the correct chunk is NOT retrieved. **When** top_k >= 3 is used, **Then** the correct chunk IS retrieved.
3. **Given** the comparative study D1-D6 questions, **When** re-run with the fix, **Then** at least some questions that previously scored 0 due to insufficient evidence now have access to the correct evidence.

---

### User Story 2 - Remove hard 500-character truncation on retrieved passages (Priority: P1)

As a medical RAG system, I want retrieved passages to be delivered in full (or intelligently truncated at sentence boundaries) instead of being cut at exactly 500 characters, so that the verifier and LLM generator can see complete medical facts.

**Why this priority**: The 500-character hard truncation silently removes evidence that appears after character 500. For medical abstracts and detailed passages, the specific fact needed to answer a question often appears after the first 500 characters. This is a silent, deterministic evidence loss.

**Independent Test**: Run the comparative study and verify that retrieved passages contain the full text from the corpus. For questions that previously failed due to missing keywords, check whether those keywords now appear in the retrieved passages.

**Acceptance Scenarios**:

1. **Given** a retrieved passage with text longer than 500 characters, **When** the passage is processed, **Then** the full text is preserved (or truncated at a sentence boundary, not character 500).
2. **Given** a medical question requiring a specific dosage or fact that appears at character 600 of a passage, **When** the old 500-char truncation is used, **Then** the fact is missing. **When** the fix is applied, **Then** the fact is present.
3. **Given** the D1 aspirin dosage question, **When** re-run with the fix, **Then** the retrieved passages contain "650 mg" (the correct answer) rather than truncating before it.

---

### User Story 3 - Re-evaluate verifier performance after retrieval fix (Priority: P2)

As a researcher, I want to re-run the comparative study after fixing retrieval, so that I can determine how much of the verifier's abstention rate was due to retrieval starvation versus actual reasoning failure.

**Why this priority**: The current ~71% abstention rate could be caused by either (a) the verifier not having enough evidence to reason about, or (b) the verifier failing to reason correctly even with sufficient evidence. Fixing retrieval first isolates these two failure modes.

**Independent Test**: Re-run D1-D6 and H1-H4 cases after the retrieval fix. Compare abstention rates and accuracy scores before and after. If abstention drops significantly, retrieval starvation was a major contributor.

**Acceptance Scenarios**:

1. **Given** the current comparative study results with top_k=2 and 500-char truncation, **When** I fix both issues and re-run, **Then** I can compare the new results to determine how much of the abstention was retrieval-caused.
2. **Given** the D1-D6 accuracy suite, **When** re-run with the fix, **Then** at least some questions that previously returned INSUFFICIENT evidence now return SUPPORTED or REFUTED.
3. **Given** the H1-H4 hallucination suite, **When** re-run with the fix, **Then** the verifier has access to the full evidence needed to detect hallucinations.

---

### Edge Cases

- What happens when a passage is extremely long (e.g., 10,000+ characters)? The system should truncate at a sentence boundary (e.g., last complete sentence before a reasonable token limit) rather than at a fixed character count.
- What happens when top_k is increased but the corpus has fewer than 3 relevant chunks? The system should return all available chunks without error.
- What happens when the LLM context window is exceeded by longer passages? The system should handle this gracefully, either by further intelligent truncation or by returning an error rather than silently cutting evidence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The retriever in `backend/server/routes/ask_question.py` MUST use `top_k >= 3` instead of `top_k=2`.
- **FR-002**: The retriever in `backend/server/routes/ask_question.py` MUST NOT truncate passage text at exactly 500 characters. It should preserve full text or truncate at sentence boundaries.
- **FR-003**: The retriever in `backend/server/routes/medrag_baseline.py` MUST NOT truncate passage text at exactly 500 characters. It should preserve full text or truncate at sentence boundaries.
- **FR-004**: The `page_content` field of `Document` objects MUST contain the full passage text (or sentence-boundary-truncated text), not a fixed 500-character slice.
- **FR-005**: The `text` field of `Passage` objects in the evidence packet MUST contain the full passage text (or sentence-boundary-truncated text), not a fixed 500-character slice.
- **FR-006**: The comparative study MUST be re-run after these fixes to measure the impact on verifier performance.
- **FR-007**: The performance report MUST clearly distinguish between retrieval-starvation failures and verifier-reasoning failures.

### Key Entities *(include if feature involves data)*

- **Passage**: A retrieved text chunk from the corpus, with attributes: chunk_id, document_id, text, page_location, provenance_hash.
- **EvidencePacket**: A collection of passages with metadata, used as input to the verifier.
- **Retriever**: The component that queries Pinecone and returns matching passages.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The retriever returns at least 3 chunks per query (top_k >= 3) in 100% of test cases.
- **SC-002**: Retrieved passages contain the full text from the corpus, with no fixed 500-character truncation.
- **SC-003**: After the fix, at least 20% of questions that previously scored 0 due to "insufficient evidence" now have access to the correct evidence.
- **SC-004**: The comparative study re-run shows a measurable change in abstention rate, allowing isolation of retrieval-starvation vs. verifier-reasoning failure modes.
- **SC-005**: The D1-D6 accuracy suite shows improved scores after the fix, demonstrating that retrieval depth was a limiting factor.

## Assumptions

- The Pinecone index contains chunks longer than 500 characters, and the relevant evidence for some questions appears after character 500.
- The LLM context window can handle longer passages; if not, intelligent truncation at sentence boundaries is acceptable.
- Increasing top_k from 2 to 3-5 does not significantly increase latency or cost to the point of being impractical.
- The verifier's reasoning capability is not fundamentally broken; it just needs sufficient evidence to work with.
- Fixing retrieval will not completely eliminate abstention; some questions genuinely lack sufficient evidence in the corpus.
