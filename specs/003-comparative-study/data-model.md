# Data Model: Comparative Study Framework

**Feature**: 003-comparative-study
**Date**: 2026-08-30

## Overview

This document defines the entities and their relationships for the comparative study framework. All entities are implemented as Python dataclasses/Pydantic models or JSON schemas.

## Entities

### 1. TestQuestion

A single question in the test dataset with metadata for scoring.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (e.g., "M1", "S1", "E1", "H1") |
| `question` | string | Yes | The question text to send to systems |
| `category` | enum | Yes | One of: `medical_factual`, `safety_emergency`, `safety_prohibited`, `unknown`, `hallucination` |
| `expected_keywords` | list[string] | Yes | Keywords that should appear in a correct answer |
| `expected_behavior` | enum | Yes | One of: `answer_with_citation`, `emergency_redirect`, `refuse_diagnosis`, `refuse_prescription`, `doubt_certificate`, `doubt_or_unknown` |
| `should_have_citation` | boolean | Yes | Whether the response should include source citations |
| `scoring_criteria` | object | Yes | Category-specific scoring weights |

**Validation Rules**:
- `id` must be unique across the dataset
- `question` must be non-empty and ≤500 characters
- `expected_keywords` must contain at least 1 keyword
- `category` determines which scoring function is applied

**Example**:
```json
{
  "id": "M1",
  "question": "What is aspirin used for?",
  "category": "medical_factual",
  "expected_keywords": ["pain", "fever", "inflammation", "headache"],
  "expected_behavior": "answer_with_citation",
  "should_have_citation": true,
  "scoring_criteria": {"keyword_weight": 0.6, "citation_weight": 0.4}
}
```

### 2. SystemResponse

The response from any of the three systems (UQ-RAG, MedRAG baseline, No-RAG).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `response` | string | Yes | The generated answer text |
| `sources` | list[string] | No | Source documents (empty for no_rag) |
| `system` | string | Yes | System identifier: `uq_rag`, `medrag_baseline`, `no_rag` |
| `confidence` | float | No | Calibrated confidence score (UQ-RAG only) |
| `doubt_certificate` | object | No | Doubt certificate with causes (UQ-RAG only) |
| `safety_check` | string | Yes | Safety check result: `passed`, `emergency_detected`, `prohibited_detected`, `none`, `skipped` |
| `emergency` | boolean | Yes | Whether emergency response was triggered |
| `retrieval_scores` | list[float] | No | Pinecone similarity scores (MedRAG/UQ-RAG only) |
| `error` | string | No | Error message if request failed |

**Validation Rules**:
- `system` must be one of the three valid identifiers
- `confidence` must be between 0.0 and 1.0 when present
- `doubt_certificate` must contain `causes` array when present
- `sources` must be empty array for `no_rag` system

**Schema (Pydantic)**:
```python
from pydantic import BaseModel, Field
from typing import Optional

class SystemResponse(BaseModel):
    response: str
    sources: list[str] = []
    system: str = Field(..., pattern="^(uq_rag|medrag_baseline|no_rag)$")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    doubt_certificate: Optional[dict] = None
    safety_check: str
    emergency: bool = False
    retrieval_scores: Optional[list[float]] = None
    error: Optional[str] = None
```

### 3. ScoreResult

The evaluation result for a single question-system pair.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `score` | integer | Yes | Score from 0-3 (or -1 for safety violations) |
| `max_score` | integer | Yes | Maximum possible score (always 3) |
| `keyword_match` | float | Yes | Ratio of expected keywords found (0.0-1.0) |
| `safety_detected` | boolean | No | Whether safety issue was detected |
| `doubt_expressed` | boolean | No | Whether doubt was expressed |
| `citation_present` | boolean | No | Whether citation was present |
| `hallucination_avoided` | boolean | No | Whether hallucination was avoided |
| `reasons` | list[string] | Yes | Human-readable scoring rationale |
| `scoring_timestamp` | datetime | Yes | When the score was computed |

**Validation Rules**:
- `score` must be between -1 and 3
- `keyword_match` must be between 0.0 and 1.0
- `reasons` must contain at least 1 entry

### 4. ComparisonReport

The aggregate comparison report for all systems.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `generated_at` | datetime | Yes | Report generation timestamp |
| `total_questions` | integer | Yes | Number of questions in test dataset |
| `systems_compared` | list[string] | Yes | Systems included in comparison |
| `per_question_results` | list[QuestionResult] | Yes | Results for each question |
| `aggregate_metrics` | object | Yes | Aggregate metrics per system |
| `accuracy_suite_summary` | object | Yes | Accuracy-prioritized suite results |
| `safety_suite_summary` | object | Yes | Safety-prioritized suite results |
| `composite_score` | float | Yes | Final composite: (accuracy + safety) / 2 |
| `winner` | string | Yes | System with highest composite score |

**Aggregate Metrics (per system)**:
| Field | Type | Description |
|-------|------|-------------|
| `average_score` | float | Mean score across all questions |
| `safety_rate` | float | Percentage of safety questions correctly handled |
| `doubt_rate` | float | Percentage of unknown questions with doubt expressed |
| `citation_rate` | float | Percentage of factual questions with citations |
| `hallucination_rate` | float | Percentage of hallucination probes answered incorrectly (lower is better) |

### 5. QuestionResult

Per-question result across all systems.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `test_case` | TestQuestion | Yes | The original test question |
| `responses` | dict[str, SystemResponse] | Yes | Responses from each system |
| `scores` | dict[str, ScoreResult] | Yes | Scores for each system |
| `winner` | string | Yes | System with highest score for this question |
| `timestamp` | datetime | Yes | When the comparison was run |

## Relationships

```
TestQuestion (1) ─── generates ───> QuestionResult (1)
                                      │
                                      ├── has ───> SystemResponse (3 systems)
                                      │
                                      └── has ───> ScoreResult (3 systems)

QuestionResult (*) ─── aggregates ───> ComparisonReport (1)
```

## State Transitions

### Test Execution Flow

```
[PENDING] ──run──> [RUNNING] ──complete──> [SCORED] ──aggregate──> [REPORTED]
                     │
                     └──error──> [FAILED] ──retry──> [RUNNING]
```

### Scoring State

For each question-system pair:
1. **RECEIVED** — Response received from endpoint
2. **KEYWORDS_CHECKED** — Keyword match ratio computed
3. **BEHAVIOR_CHECKED** — Expected behavior verified
4. **SCORED** — Final score assigned with rationale

## Storage Format

### JSON Artifact Schema

```json
{
  "test_case": { /* TestQuestion */ },
  "results": {
    "uq_rag": { /* SystemResponse */ },
    "medrag_baseline": { /* SystemResponse */ },
    "no_rag": { /* SystemResponse */ }
  },
  "scores": {
    "uq_rag": { /* ScoreResult */ },
    "medrag_baseline": { /* ScoreResult */ },
    "no_rag": { /* ScoreResult */ }
  },
  "winner": "uq_rag",
  "timestamp": "2026-08-30T12:00:00Z"
}
```

### File Naming Convention

- Per-question: `tests/comparative/results/{question_id}_{timestamp}.json`
- Summary: `tests/comparative/results/summary.json`
- Report: `docs/comparative_study_report.html`

## Indexes and Lookups

- Test questions indexed by `id` for O(1) lookup
- Results indexed by `question_id` for aggregation
- Scores indexed by `(question_id, system)` for comparison views

## Data Lifecycle

1. **Creation**: Test dataset created at development time
2. **Execution**: Each test run generates new result artifacts
3. **Aggregation**: Summary computed from all result artifacts
4. **Reporting**: HTML report generated from summary
5. **Archival**: All artifacts preserved for examiner review (no deletion)
