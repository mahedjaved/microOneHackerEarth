# API Contracts: CURA-Med Frontend

**Feature**: 002-frontend-material  
**Date**: 2026-08-29  
**Status**: Draft

## Overview

The frontend consumes three backend endpoints:
- `POST /upload_pdfs/` — Upload PDF files
- `POST /ask/` — Submit a medical question
- `GET /health` — Check backend health

All endpoints return JSON. The frontend must handle errors gracefully and display user-friendly messages.

---

## Contract 1: Upload PDFs

**Endpoint**: `POST /upload_pdfs/`  
**Purpose**: Upload one or more PDF files for processing

### Request

- **Content-Type**: `multipart/form-data`
- **Body**:
  - `files` (array of files, required): PDF files to upload

### Response 200 OK

```json
{
  "message": "Files uploaded successfully",
  "uploaded_files": ["doc1.pdf", "doc2.pdf"],
  "index_name": "medical-index"
}
```

### Error Responses

| Status | Body | Meaning |
|--------|------|---------|
| 400 | `{"detail": "No files provided"}` | Missing files in request |
| 413 | `{"detail": "File too large"}` | File exceeds 50MB limit |
| 422 | `{"detail": "Invalid file type"}` | Non-PDF file uploaded |
| 500 | `{"detail": "Internal server error"}` | Backend processing failed |

### Frontend Behavior

- Show success message with list of uploaded filenames
- On error, display the `detail` message to the user
- Disable upload button while processing

---

## Contract 2: Ask Question

**Endpoint**: `POST /ask/`  
**Purpose**: Submit a medical question and receive a response

### Request

- **Content-Type**: `application/x-www-form-urlencoded`
- **Body**:
  - `question` (string, required): The user's medical question

### Response 200 OK

```json
{
  "response": "Aspirin is used for pain relief and reducing inflammation.",
  "sources": ["medical-doc-1:page-1", "medical-doc-2:page-3"],
  "disclaimer": "This is not medical advice. Consult a healthcare professional.",
  "injection_detected": false,
  "pii_redacted": false,
  "doubt_certificate": null,
  "run_artifact_id": "6aa1c7ae-1653-4383-a273-5b857efa0ac3"
}
```

### Response with Doubt Certificate

```json
{
  "response": null,
  "sources": [],
  "disclaimer": "This is not medical advice. Consult a healthcare professional.",
  "injection_detected": false,
  "pii_redacted": false,
  "doubt_certificate": {
    "status": "insufficient_evidence",
    "message": "I do not know from the approved evidence.",
    "support_probability": 0.0,
    "probability_semantics": "P(claim fully supported by active retrieved evidence)",
    "conformal_set": ["SUPPORTED", "INSUFFICIENT"],
    "coverage_target": 0.90,
    "uncertainty_causes": [],
    "actions_taken": [],
    "human_review_recommended": true,
    "corpus_id": "mirage-pubmed-v1"
  },
  "run_artifact_id": "6aa1c7ae-1653-4383-a273-5b857efa0ac3"
}
```

### Response with Emergency

```json
{
  "response": "If you are experiencing a medical emergency, please contact your local emergency services or go to the nearest emergency room immediately.",
  "sources": [],
  "disclaimer": "This is not medical advice. In an emergency, contact emergency services.",
  "injection_detected": false,
  "pii_redacted": false,
  "doubt_certificate": null,
  "run_artifact_id": "6aa1c7ae-1653-4383-a273-5b857efa0ac3"
}
```

### Error Responses

| Status | Body | Meaning |
|--------|------|---------|
| 400 | `{"detail": "Question cannot be empty"}` | Empty question submitted |
| 422 | `{"detail": "Please remove personal information from your query."}` | PII detected in strict mode |
| 500 | `{"detail": "Internal server error"}` | Backend processing failed |

### Frontend Behavior

- Display `response` in chat bubble if present
- Display `sources` as clickable links or citations
- Display `disclaimer` in info box
- If `doubt_certificate` is present, display it in a warning box
- If `emergency` is true (inferred from response text), display prominently
- Show `run_artifact_id` for download reference
- On error, display the `detail` message

---

## Contract 3: Health Check

**Endpoint**: `GET /health`  
**Purpose**: Check if backend is running

### Response 200 OK

```json
{
  "status": "healthy"
}
```

### Frontend Behavior

- On startup, check health endpoint
- If unhealthy, display warning: "Backend is not available. Please ensure the server is running at [API_URL]"
- Retry health check every 30 seconds while user is on the page

---

## Shared Concerns

### Error Handling

All errors follow the pattern:
```json
{
  "detail": "Human-readable error message"
}
```

Frontend MUST:
- Display `detail` to the user in an error message
- Log the full error for debugging
- Never expose stack traces or internal error details to the user

### Timeouts

- Frontend request timeout: 30 seconds
- Emergency queries MUST complete in under 2 seconds (backend responsibility)
- If timeout occurs, display: "Request timed out. Please try again."

### PII Redaction

- Backend handles PII redaction; frontend displays redacted text only
- Frontend MUST NOT log raw user questions
- If `pii_redacted` is true, optionally show a notice: "Personal information was redacted from your query"

### Security

- Frontend MUST NOT execute any content from backend responses as code
- Backend responses are rendered as Markdown only
- Uploaded files are sent directly to backend; frontend does not inspect PDF contents
