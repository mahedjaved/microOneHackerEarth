# Regression Tests for CURA-Med

This directory contains Playwright-based regression tests covering the full
pipeline from PDF upload through chunking, retrieval, answer generation,
and uncertainty handling.

## Prerequisites

```powershell
# Install dependencies
pip install pytest pytest-playwright playwright

# Install browser
python -m playwright install chromium

# Start services (from repo root)
cd backend
docker-compose up -d

# Start frontend (separate terminal)
cd frontend
streamlit run app.py
```

## Running Tests

```powershell
# Run all regression tests
pytest tests/regression/ -v

# Run only API tests (no browser)
pytest tests/regression/test_pipeline.py tests/regression/test_uncertainty.py tests/regression/test_edge_cases.py -v

# Run only UI tests (requires frontend running)
pytest tests/regression/test_frontend_ui.py -v

# Run with headed browser (visible)
pytest tests/regression/ -v --headed

# Run specific test class
pytest tests/regression/test_uncertainty.py::TestUncertaintyHandling -v
```

## Test Coverage

### Pipeline Tests (`test_pipeline.py`)

Covers the core document processing pipeline:

| Test | Scenario | Assertion |
|------|----------|-----------|
| `test_upload_pdf_returns_200` | Upload valid PDF | Returns 200 with filename in response |
| `test_upload_without_files_returns_400` | Upload with no files | Returns 400 |
| `test_upload_non_pdf_returns_error` | Upload non-PDF file | Returns 400 or 422 |
| `test_ask_endpoint_accepts_question` | Ask a question | Returns 200 or 500 |
| `test_ask_returns_sources_when_successful` | Successful query | Response includes sources list |
| `test_ask_empty_question_returns_error` | Empty question | Returns 400 or 422 |
| `test_ask_returns_disclaimer` | Successful query | Response includes disclaimer |
| `test_retrieved_sources_are_non_empty` | Successful query | Sources are non-empty strings |
| `test_irrelevant_query_triggers_doubt` | Unrelated query | Returns doubt certificate when no evidence |

### Uncertainty Tests (`test_uncertainty.py`)

Covers uncertainty detection and doubt certificate generation:

| Test | Scenario | Assertion |
|------|----------|-----------|
| `test_no_evidence_returns_doubt_certificate` | No matching evidence | Returns doubt certificate |
| `test_doubt_certificate_has_required_fields` | Doubt certificate present | Has status, message, support_probability |
| `test_doubt_certificate_uncertainty_causes` | Doubt certificate present | Includes uncertainty_causes list |
| `test_doubt_certificate_actions_taken` | Doubt certificate present | Includes actions_taken list |
| `test_confident_answer_no_doubt_certificate` | Confident answer | No doubt certificate present |
| `test_run_artifact_id_present` | Any query | Response includes run_artifact_id |
| `test_emergency_query_triggers_safety_response` | Emergency query | Response contains emergency instructions |
| `test_emergency_response_within_timeout` | Emergency query | Returns within 5 seconds |

### Edge Case Tests (`test_edge_cases.py`)

Covers validation, redaction, and error handling:

| Test | Scenario | Assertion |
|------|----------|-----------|
| `test_oversized_file_rejected` | Upload >50MB file | Returns 400, 413, or 422 |
| `test_valid_size_file_accepted` | Upload valid file | Returns 200 |
| `test_download_contains_no_ssN` | Download with PII | SSN redacted from download |
| `test_download_contains_no_email` | Download with PII | Email redacted from download |
| `test_empty_question_rejected` | Empty question | Returns 400 or 422 |
| `test_whitespace_only_question_rejected` | Whitespace-only question | Returns 400 or 422 |
| `test_health_endpoint_returns_status` | Health check | Returns status field |
| `test_invalid_endpoint_returns_404` | Invalid endpoint | Returns 404 |

### Frontend UI Tests (`test_frontend_ui.py`)

Covers UI workflows using Playwright:

| Test | Scenario | Assertion |
|------|----------|-----------|
| `test_page_loads` | Load frontend | Page title is correct |
| `test_upload_component_visible` | Page loaded | Upload section visible |
| `test_chat_input_visible` | Page loaded | Chat section visible |
| `test_upload_pdf_shows_success` | Upload PDF | Success message shown |
| `test_oversized_file_shows_error` | Upload >50MB | Error message shown |
| `test_send_question_shows_user_message` | Ask question | User message visible |
| `test_empty_question_shows_error` | Empty question | Error message shown |
| `test_response_shows_disclaimer` | Get response | Disclaimer visible |
| `test_emergency_query_shows_safety_response` | Emergency query | Safety response visible |
| `test_post_emergency_shows_reminder` | After emergency | Reminder shown |
| `test_download_available_after_chat` | After chat | Download button visible |
| `test_download_contains_metadata` | Download file | Contains run ID and timestamp |
| `test_conversation_history_persists` | Multiple questions | History persists in session |

## Notes

- Tests that require Pinecone vector store may be skipped or return 500 when
  Pinecone is not configured. This is expected behavior.
- UI tests require both the backend and frontend to be running.
- API tests only require the backend to be running.
- Use `--headed` flag to see browser interactions during UI tests.
