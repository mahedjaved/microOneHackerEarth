# Research: CURA-Med Frontend

**Feature**: 002-frontend-material  
**Date**: 2026-08-29  
**Status**: Complete

## Research Tasks

### 1. Streamlit best practices for file uploads and chat UIs

**Decision**: Use `st.file_uploader` for PDF uploads and `st.chat_message` for conversational UI.

**Rationale**: 
- `st.file_uploader` natively supports PDF MIME types, size limits, and multi-file uploads
- `st.chat_message` provides built-in chat bubbles with role-based styling
- Session state (`st.session_state`) handles conversation history without external storage
- Streamlit reruns the entire script on each interaction, so state must be explicitly preserved in `st.session_state`

**Alternatives considered**:
- Custom file upload component: Rejected because `st.file_uploader` is sufficient and more reliable
- Third-party chat components (e.g., `streamlit-chat`): Rejected to minimize dependencies

### 2. Frontend error handling and backend unavailability

**Decision**: Display user-friendly error messages with retry guidance when backend returns non-200 status codes or connection fails.

**Rationale**:
- Backend may be unreachable during demo (no Pinecone/Groq keys)
- Users need clear guidance: "Backend unavailable. Please ensure the server is running at [API_URL]"
- Emergency queries should bypass backend if possible, but current implementation relies on backend safety gate

**Alternatives considered**:
- Frontend-side emergency detection: Rejected because safety logic must remain in backend per constitution
- Silent failure with empty state: Rejected because it hides system state from user

### 3. UAT automation for Streamlit apps

**Decision**: Use `requests` library to hit backend endpoints directly, bypassing the Streamlit UI for automated testing.

**Rationale**:
- Streamlit's UI is not designed for headless automation
- Backend API is already testable via HTTP
- `frontend/uat_test.py` validates frontend-backend integration without browser automation
- For full UI automation, Playwright or Selenium could be added later, but is out of scope for v1

**Alternatives considered**:
- Playwright/Selenium: Rejected for v1 due to complexity; can be added in A0 if needed
- Streamlit testing framework: Rejected because it does not support full E2E testing

### 4. Conversation history persistence

**Decision**: Maintain conversation history in `st.session_state` only. No persistence across browser sessions or server restarts.

**Rationale**:
- Per spec clarification: "Conversation history is maintained within a single browser session; no persistent history across sessions"
- Simplifies implementation and aligns with privacy constraints (no storing user questions)
- Session state is lost when the Streamlit server restarts, which is acceptable for a demo

**Alternatives considered**:
- Database-backed history: Rejected due to privacy constraints and scope
- Browser localStorage: Rejected because it persists beyond session and complicates PII redaction

### 5. Download run artifacts

**Decision**: Backend generates artifact JSON; frontend triggers download via a button that fetches the artifact by `run_artifact_id`.

**Rationale**:
- Backend already builds `RunArtifact` objects with PII redaction
- Frontend only needs to expose a download link
- Keeps artifact generation logic in the backend where it belongs

**Alternatives considered**:
- Frontend-generated artifacts: Rejected because it would duplicate backend logic and risk PII leakage
- PDF export: Rejected for v1; JSON artifact is sufficient for audit trail
