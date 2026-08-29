# Data Model: CURA-Med Frontend

**Feature**: 002-frontend-material  
**Date**: 2026-08-29  
**Status**: Draft

## Entities

### User Upload

Represents a PDF file uploaded by the user for processing.

| Field | Type | Description |
|-------|------|-------------|
| `filename` | string | Original filename of the uploaded PDF |
| `size_bytes` | integer | File size in bytes |
| `upload_timestamp` | datetime | When the file was uploaded |
| `status` | enum | `uploaded`, `processing`, `ready`, `error` |
| `error_message` | string | Error details if status is `error` |

**Validation rules**:
- File MUST be a PDF (MIME type `application/pdf`)
- File size MUST NOT exceed 50MB
- Filename MUST NOT contain path traversal characters

**State transitions**:
```
uploaded → processing → ready
uploaded → processing → error
```

### Question

Represents a user's medical question submitted to the backend.

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | The question text (PII-redacted) |
| `timestamp` | datetime | When the question was asked |
| `session_id` | string | Browser session identifier |
| `run_artifact_id` | UUID | Link to the generated run artifact |

**Validation rules**:
- Text MUST NOT be empty
- Text MUST be redacted before sending to backend

### Answer

Represents the system's response to a question.

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | The answer text (may be empty if doubt certificate shown) |
| `sources` | list of strings | Cited source references |
| `disclaimer` | string | Medical disclaimer text |
| `doubt_certificate` | DoubtCertificate | Present if evidence is insufficient |
| `emergency` | boolean | True if emergency response triggered |
| `run_artifact_id` | UUID | Link to the run artifact |
| `latency_ms` | integer | Response time in milliseconds |

**Validation rules**:
- If `doubt_certificate` is present, `text` MAY be empty
- If `emergency` is true, response MUST be displayed within 2 seconds
- `sources` MUST be displayed if present

### Run Artifact

Represents a downloadable record of an interaction.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | UUID | Unique identifier for this interaction |
| `timestamp` | datetime | When the interaction occurred |
| `question` | RedactedQuestion | The question with PII redacted |
| `answer` | string | The system's answer |
| `sources` | list of strings | Cited sources |
| `disclaimer` | string | Medical disclaimer |
| `doubt_certificate` | DoubtCertificate | Present if applicable |
| `emergency` | boolean | True if emergency response |
| `verifier_outputs` | list | Verification decisions per claim |
| `conformal_sets` | list | Conformal prediction sets |
| `eav_actions` | list | Uncertainty-reduction actions taken |
| `final_decision` | enum | `answer`, `doubt_certificate`, `safety_response` |
| `corpus_id` | string | Active corpus identifier |
| `corpus_hash` | string | SHA-256 hash of corpus |
| `model_version` | string | LLM model version |
| `verifier_version` | string | Verifier model version |
| `calibration_id` | string | Calibration artifact identifier |
| `latency_ms` | integer | Total response time |
| `pii_redacted` | boolean | Whether PII was redacted |

### Doubt Certificate

Represents the system's explanation of why it cannot answer.

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `insufficient_evidence` or `clarification_required` |
| `message` | string | Fixed message: "I do not know from the approved evidence." |
| `support_probability` | float | P(claim fully supported by active retrieved evidence) |
| `conformal_set` | list of Verdict | Possible verdicts from conformal prediction |
| `coverage_target` | float | Target coverage level (0.90) |
| `uncertainty_causes` | list of UncertaintyCause | Reasons for uncertainty |
| `actions_taken` | list of EAVAction | Uncertainty-reduction actions attempted |
| `human_review_recommended` | boolean | Whether human review is recommended |
| `corpus_id` | string | Active corpus identifier |

## Relationships

```
User Upload 1..* Question
Question 1..1 Answer
Question 1..1 Run Artifact
Run Artifact 1..* Answer
Run Artifact 0..* Doubt Certificate
Doubt Certificate 0..* Uncertainty Cause
Doubt Certificate 0..* EAV Action
```

## State Transitions

### Question Lifecycle

1. User types question → `pending`
2. Frontend redacts PII → `redacted`
3. Backend processes → `processing`
4. Backend returns answer/doubt/emergency → `complete`

### Upload Lifecycle

1. User selects file → `uploaded`
2. Frontend validates → `processing` or `error`
3. Backend confirms → `ready` or `error`
