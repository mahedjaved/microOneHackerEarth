# Feature Specification: CURA-Med Frontend

**Feature Branch**: `002-frontend-material`

**Created**: 2026-08-29

**Status**: Draft

**Input**: User description: "Build a Streamlit frontend for the CURA-Med medical QA system that allows users to upload PDFs, ask questions, view cited answers with uncertainty warnings, and download run artifacts. The frontend must display doubt certificates when evidence is insufficient and show emergency responses for urgent queries. Include UAT validation for end-to-end testing."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Upload medical PDFs and ask questions (Priority: P1)

A user uploads medical PDF documents to the system, then asks a medical question in natural language. The system retrieves relevant evidence from the uploaded documents, verifies the answer, and displays a cited response with source references.

**Why this priority**: This is the core functionality of the medical QA system. Without document upload and question answering, the system has no value.

**Independent Test**: Can be fully tested by uploading a single PDF, asking a question about its contents, and verifying that the answer includes citations and sources. Delivers a working medical QA experience.

**Acceptance Scenarios**:

1. **Given** the user is on the home page, **When** they upload a valid PDF file, **Then** the system confirms the upload and makes the document available for questioning
2. **Given** a PDF has been uploaded, **When** the user asks "What is aspirin used for?", **Then** the system displays a cited answer with source references
3. **Given** the user has asked a question, **When** the answer is generated, **Then** the system shows a medical disclaimer

---

### User Story 2 - View uncertainty warnings and doubt certificates (Priority: P2)

A user asks a question where the available evidence is insufficient or ambiguous. The system displays a doubt certificate explaining why a definitive answer cannot be provided, and suggests what additional information would help.

**Why this priority**: This is a key differentiator for CURA-Med. The uncertainty-aware behavior builds trust and safety, which is critical for medical information.

**Independent Test**: Can be fully tested by asking a question with no matching evidence in the corpus. Delivers transparency about system limitations.

**Acceptance Scenarios**:

1. **Given** no relevant evidence exists in the corpus, **When** the user asks a question, **Then** the system displays a doubt certificate instead of a guess
2. **Given** a doubt certificate is shown, **When** the user reviews it, **Then** they understand why the system cannot answer and what additional information is needed
3. **Given** the user receives a doubt certificate, **When** they choose to provide more context, **Then** the system attempts to answer again with the new information

---

### User Story 3 - Emergency response and safety bypass (Priority: P1)

A user asks a question indicating a medical emergency (e.g., "I have severe chest pain"). The system immediately displays an emergency response directing them to contact emergency services, bypassing normal QA processing.

**Why this priority**: Safety-critical feature. Must be fast and reliable to prevent harm in emergency situations.

**Independent Test**: Can be fully tested by submitting an emergency query and verifying the system responds within 2 seconds with emergency instructions. Delivers user safety.

**Acceptance Scenarios**:

1. **Given** the user submits an emergency query, **When** the system processes it, **Then** it responds within 2 seconds with emergency instructions
2. **Given** an emergency response is triggered, **When** the user sees it, **Then** the response clearly states this is not a substitute for emergency medical care
3. **Given** the user has asked an emergency question, **When** they attempt to ask another question, **Then** the system reminds them to contact emergency services

---

### User Story 4 - Download run artifacts for audit trail (Priority: P3)

A user wants to download a record of their interaction for personal records or to share with a healthcare provider. The system generates a downloadable artifact containing the question, answer, sources, and metadata.

**Why this priority**: Useful for accountability and continuity of care, but not required for basic functionality.

**Independent Test**: Can be fully tested by asking a question and clicking the download button. Verifies the artifact contains all required information. Delivers auditability.

**Acceptance Scenarios**:

1. **Given** the user has received an answer, **When** they click "Download Run Artifact", **Then** a file is downloaded containing the question, answer, sources, and timestamp
2. **Given** the user downloads an artifact, **When** they open it, **Then** all PII has been redacted and the document is readable
3. **Given** the user has multiple interactions, **When** they download artifacts, **Then** each artifact is uniquely identified and timestamped

---

### User Story 5 - UAT validation and end-to-end testing (Priority: P2)

A developer or tester runs the UAT script to validate that the frontend-backend integration works correctly across all user scenarios.

**Why this priority**: Ensures system reliability before deployment. Critical for hackathon demonstration.

**Independent Test**: Can be fully tested by running the UAT script and verifying all test cases pass. Delivers confidence in system correctness.

**Acceptance Scenarios**:

1. **Given** both frontend and backend are running, **When** the UAT script is executed, **Then** all test cases pass
2. **Given** the UAT script completes, **When** the results are reviewed, **Then** each user story has at least one passing test
3. **Given** a test fails, **When** the issue is fixed, **Then** the UAT script passes on re-run

---

### Edge Cases

- What happens when the user uploads a non-PDF file?
- How does the system handle very large PDFs (100+ pages)?
- What happens when the backend is unreachable?
- How does the system behave when the user submits an empty question?
- What happens when multiple PDFs are uploaded simultaneously?
- How does the system handle questions in languages other than English?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to upload PDF files through a web interface
- **FR-002**: System MUST accept natural language questions from users
- **FR-003**: System MUST display cited answers with source references
- **FR-004**: System MUST show a medical disclaimer with every answer
- **FR-005**: System MUST display a doubt certificate when evidence is insufficient
- **FR-006**: System MUST show an emergency response within 2 seconds for urgent queries
- **FR-007**: System MUST allow users to download run artifacts containing interaction history
- **FR-008**: System MUST redact PII from all downloaded artifacts
- **FR-009**: System MUST display uncertainty warnings when the verifier is not confident
- **FR-010**: System MUST provide a UAT script that validates end-to-end functionality
- **FR-011**: System MUST handle backend unavailability gracefully with user-friendly error messages
- **FR-012**: System MUST validate uploaded files and reject non-PDF formats with clear feedback

### Key Entities *(include if feature involves data)*

- **User Upload**: Represents a PDF file uploaded by the user, including filename, size, upload timestamp, and processing status
- **Question**: A user's medical question in natural language, including the text, timestamp, and any redacted PII
- **Answer**: The system's response, including the answer text, cited sources, confidence level, and any doubt certificate or emergency flag
- **Run Artifact**: A downloadable record of an interaction, including the question, answer, sources, metadata, and PII redaction status
- **Doubt Certificate**: A structured explanation of why the system cannot answer, including uncertainty causes and recommended actions

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can upload a PDF and receive their first cited answer in under 30 seconds
- **SC-002**: Emergency queries receive a response within 2 seconds
- **SC-003**: 90% of users can complete a full question-answer cycle without errors on first attempt
- **SC-004**: All PII is redacted from downloaded artifacts with zero leakage
- **SC-005**: UAT script passes all test cases on first run after deployment
- **SC-006**: Users can download a run artifact in under 5 seconds
- **SC-007**: The frontend remains responsive during backend processing (no frozen UI)

## Clarifications

### Session 2026-08-29

- Q: Should the frontend require user authentication before accessing the medical QA system? → A: No authentication; open access for demo purposes
- Q: Should the frontend support multi-turn conversation history within a single session? → A: Yes, maintain conversation history within the session

## Assumptions

- Authentication is not required for v1; the frontend is a public demo application
- Conversation history is maintained within a single browser session; no persistent history across sessions

- Users have a modern web browser with JavaScript enabled
- Users have stable internet connectivity for backend communication
- PDF uploads are limited to 50MB per file
- The backend API is running and accessible at a configurable URL
- Users understand this is a demonstration system and not a replacement for professional medical advice
- The system operates on synthetic or publicly available medical data, not real patient records
- Emergency detection is based on keyword matching and may not catch all emergency situations
- The frontend is used primarily on desktop browsers (mobile responsiveness is out of scope for v1)
