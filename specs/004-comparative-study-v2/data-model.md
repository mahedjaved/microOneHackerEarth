# Data Model: Comparative Study v2

**Feature:** 004-comparative-study-v2
**Date:** 2026-08-30

## Overview

Entities and relationships for the redesigned comparative study framework.

## Entities

### 1. TestQuestion

A single question in the test dataset.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique identifier (e.g., "D1", "S1", "H1") |
| question | string | Yes | The question text |
| category | enum | Yes | One of: medical_factual, safety_emergency, safety_prohibited, unknown, hallucination |
| expected_keywords | list[string] | No | Keywords for accuracy scoring |
| document_does_not_contain | boolean | No | True for hallucination probes |
| general_knowledge_unanswerable | boolean | No | True if LLM cannot answer from training data |

**Validation Rules:**
- id must be unique
- question must be non-empty and ≤500 characters
- hallucination questions must have document_does_not_contain=True

### 2. ScoreResult

The evaluation result for a single question-system pair.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| score | float | Yes | Normalized score in [0, 1] |
| dimension | string | Yes | One of: safety, accuracy, calibration, hallucination |
| raw_response | string | No | The system's response text |
| confidence | float | No | UQ-RAG confidence score (if available) |
| sources | list[string] | No | Source documents cited |
| timestamp | datetime | Yes | When score was computed |

**Validation Rules:**
- score must be in [0, 1]
- dimension must be one of the valid values

### 3. RunResult

Results from a single complete test run.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| run_id | integer | Yes | Run number (1, 2, or 3) |
| timestamp | datetime | Yes | When run completed |
| results | list[QuestionResult] | Yes | Per-question results |
| aggregate | dict[str, float] | Yes | System-level aggregates |

### 4. QuestionResult

Per-question result across all systems for a single run.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| test_case | TestQuestion | Yes | The original test question |
| scores | dict[str, ScoreResult] | Yes | Scores per system |
| winner | string | Yes | System with highest score |

### 5. ComparisonReport

The final aggregate comparison report.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| generated_at | datetime | Yes | Report generation timestamp |
| total_questions | integer | Yes | Number of questions tested |
| runs | integer | Yes | Number of test runs performed |
| systems | list[string] | Yes | Systems compared |
| per_system_metrics | dict | Yes | Aggregate metrics per system |
| calibration | dict | Yes | Calibration data per system |
| methodology | string | Yes | Scoring methodology description |

**Per-System Metrics:**
| Field | Type | Description |
|-------|------|-------------|
| mean_score | float | Mean score across all questions and runs |
| std_score | float | Standard deviation |
| ci_95 | tuple[float, float] | 95% confidence interval |
| safety_rate | float | Safety detection rate (for safety questions) |
| calibration_ece | float | Expected Calibration Error |

## Relationships

```
TestQuestion (1) ──generates──> QuestionResult (1 per run)
                                    │
                                    └──has──> ScoreResult (3 systems)

RunResult (3) ──contains──> QuestionResult (*)

ComparisonReport (1) ──aggregates──> RunResult (3)
```

## State Transitions

### Test Execution

```
[INIT] ──run──> [RUNNING] ──complete──> [SCORED] ──aggregate──> [REPORTED]
                  │
                  └──error──> [RETRY] ──> [RUNNING]
```

### Scoring State (per question)

```
[RECEIVED] ──evaluate──> [SCORED] ──normalize──> [NORMALIZED]
```

## Storage Format

### JSON Artifact Schema (per question per run)

```json
{
  "run_id": 1,
  "test_case": { /* TestQuestion */ },
  "scores": {
    "uq_rag": {
      "score": 0.85,
      "dimension": "accuracy",
      "confidence": 0.92,
      "sources": ["doc1.pdf"],
      "timestamp": "2026-08-30T12:00:00Z"
    },
    "medrag_baseline": { /* ... */ },
    "no_rag": { /* ... */ }
  },
  "winner": "uq_rag"
}
```

### Summary Schema

```json
{
  "runs": 3,
  "systems": ["uq_rag", "medrag_baseline", "no_rag"],
  "metrics": {
    "uq_rag": {
      "mean": 0.82,
      "std": 0.05,
      "ci_95": [0.77, 0.87],
      "safety_rate": 0.95,
      "calibration_ece": 0.08
    }
  }
}
```

## File Naming

- Per-question: `tests/comparative/results/{question_id}_run{run_id}_{timestamp}.json`
- Summary: `tests/comparative/results/summary.json`
- Report: `docs/comparative_study_report_v2.html`
