# Implementation Plan: Comparative Study Framework

**Branch**: `003-comparative-study` | **Date**: 2026-08-30 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-comparative-study/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Implement a comparative study framework that benchmarks the existing UQ-RAG system against two baselines: a MedRAG-style RAG without uncertainty quantification (`/medrag_baseline/`) and a direct LLM without retrieval (`/no_rag/`). The framework includes a 20+ question test dataset across four categories (medical factual, safety-critical, unknown, hallucination probes), automated scoring with keyword/safety/doubt/citation/hallucination metrics, and an HTML comparison report for examiner evidence review. Two separate test suites (accuracy-prioritized and safety-prioritized) are scored with equal weighting in the final composite per Constitution Article XX (Baseline comparison).

## Technical Context

**Language/Version**: Python 3.11 (existing project uses Python 3.10 system + 3.11 venv)

**Primary Dependencies**: FastAPI, LangChain, LangChain-Groq, Pinecone, sentence-transformers (all already in project)

**Storage**: Pinecone vector DB (`medical-index`, 384-dim cosine), local JSON for test results, HTML for reports

**Testing**: pytest, Playwright (Python bindings already installed in project)

**Target Platform**: Windows/Linux server (local deployment, no auth per clarifications)

**Project Type**: web-service (FastAPI backend extensions + test harness)

**Performance Goals**: Each question scored within 30s end-to-end (SC-009); full report generated within 5 min (SC-008)

**Constraints**: Local-only access, no authentication, two separate test suites with equal weighting

**Scale/Scope**: 20+ test questions, 3 systems compared, 4 question categories, 5 scoring dimensions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Assessment | Status |
|---------|------------|--------|
| I — Evidence is the product boundary | All baselines return sources where applicable; UQ-RAG shows citations | PASS |
| II — Abstention is valid | Scoring rewards doubt expression for unknown/hallucination questions | PASS |
| III — Human authority | Framework produces evidence for examiner review, not autonomous diagnosis | PASS |
| IV — Emergency safety | Safety test suite explicitly tests emergency detection (SC-004) | PASS |
| V — Corpus governance | All systems use same frozen corpus per Article XX | PASS |
| VI — Privacy | No real patient data in test questions; PII redaction already in place | PASS |
| VII — Untrusted isolation | Test questions are data, not instructions | PASS |
| VIII — Structured artifacts | All responses conform to schema; scoring produces structured results | PASS |
| IX — Fair evaluation | Same frozen corpus, questions, labels for all three systems (Article XX) | PASS |
| X — Purposeful complexity | Each component addresses documented failure mode | PASS |
| XI — Observability | Test results saved as JSON artifacts with timestamps | PASS |
| XII — Disclaimer not evidence | Scoring based on observable behaviors, not confidence numbers | PASS |
| XIII — Confidence names testable event | Calibration artifact included in UQ responses | PASS |
| XIV — External evidence > confidence | Keyword match against corpus-derived answers | PASS |
| XV — Ambiguity fails closed | Doubt certificate scoring rewards abstention | PASS |
| XVI — Uncertainty causes separate | Safety vs doubt vs citation scored independently | PASS |
| XVII — Adaptive policies calibrated | Conformal predictor loaded from frozen calibration artifact | PASS |
| XVIII — Improvement changelog | Each test run generates evidence artifacts for changelog | PASS |
| XIX — Agent trajectories | Test framework captures full request/response pairs | PASS |
| XX — Baseline comparison | Framework explicitly implements Article XX requirements | PASS |

**Result**: All articles pass. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/003-comparative-study/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── server/
│   ├── main.py                    # FastAPI app (add medrag_baseline router import)
│   └── routes/
│       ├── ask_question.py        # UQ-RAG endpoint (existing)
│       ├── simple_ask.py          # Simple RAG baseline (existing, rename to medrag)
│       ├── sota_ask.py            # Direct LLM baseline (existing, rename to no_rag)
│       ├── medrag_baseline.py     # NEW: MedRAG-style RAG (FR-001)
│       └── no_rag.py              # NEW: Direct LLM endpoint (FR-002)

frontend/
├── app.py                         # Streamlit app (existing)
└── components/
    ├── chatUI.py                  # Existing UI
    ├── upload.py                  # Existing upload
    └── history_download.py        # Existing download

tests/
├── comparative/
│   ├── conftest.py                # Backend health fixture (existing)
│   ├── test_comparison.py         # Core comparison tests (existing, expand to 20+ questions)
│   ├── generate_report.py         # HTML report generator (existing)
│   ├── test_dataset.py            # NEW: Centralized test dataset (FR-003)
│   ├── scoring.py                 # NEW: Scoring functions (FR-004)
│   └── results/                   # JSON artifacts from test runs
└── regression/
    ├── test_frontend_ui.py        # Playwright E2E tests (FR-006)
    └── test_uat_comparative.py    # UAT tests for comparative flows
```

**Structure Decision**: Extend existing web application structure. The project already has FastAPI backend with multiple routes (ask, simple_ask, sota_ask). We add `medrag_baseline.py` and `no_rag.py` as new routes following the same pattern, and expand the existing `tests/comparative/` module with a centralized dataset, scoring functions, and more comprehensive test coverage.

## Complexity Tracking

> No Constitution violations — complexity tracking not required.

---
