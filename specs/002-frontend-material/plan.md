# Implementation Plan: CURA-Med Frontend

**Branch**: `002-frontend-material` | **Date**: 2026-08-29 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-frontend-material/spec.md`

## Summary

Build a Streamlit frontend for the CURA-Med medical QA system that lets users upload PDFs, ask questions, view cited answers with uncertainty warnings, download run artifacts, and see emergency responses. The frontend is a thin, display-only layer over the existing FastAPI backend and must not alter backend safety or verification behavior.

## Technical Context

**Language/Version**: Python 3.10 (matches backend venv)

**Primary Dependencies**: Streamlit, requests

**Storage**: Session state only; no persistent frontend storage. Backend handles corpus, models, and artifact persistence.

**Testing**: pytest for backend contract tests; existing `frontend/uat_test.py` for integration validation

**Target Platform**: Desktop web browser (mobile responsiveness out of scope per spec)

**Project Type**: Web application frontend

**Performance Goals**: 
- Emergency response displayed in under 2 seconds
- UI remains responsive during backend processing
- Run artifact download in under 5 seconds

**Constraints**: 
- No authentication (open demo)
- PDF upload limit 50MB
- Backend API configurable via `API_URL`
- Graceful degradation when backend/Pinecone is unavailable

**Scale/Scope**: Single-user demo; session-scoped conversation history only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Relevance | Status |
|---------|-----------|--------|
| I — Evidence is the product boundary | Frontend must display sources and citations with every answer | PASS |
| II — Abstention is a valid successful outcome | Frontend must render doubt certificates when evidence is insufficient | PASS |
| III — Human medical authority and review | Frontend must show disclaimer; no autonomous medical decisions | PASS |
| IV — Emergency safety behavior | Frontend must display emergency response within 2s | PASS |
| V — Corpus governance and time awareness | Frontend should show corpus provenance when available | PASS |
| VI — Privacy by construction | Frontend must redact PII in displayed artifacts | PASS |
| VII — Untrusted-content isolation | Frontend renders evidence as text only; no execution | PASS |
| VIII — Structured, verifiable artifacts | Frontend displays schema-backed run artifacts | PASS |
| IX — Fair and reproducible evaluation | Frontend includes UAT validation | PASS |
| X — Purposeful agentic complexity | Frontend adds no new agents; thin UI layer | PASS |
| XI — Observability without surveillance | Frontend shows run IDs; logs stay backend-side | PASS |
| XII — Disclaimer is not evidence | Frontend shows disclaimer but does not claim correctness | PASS |
| XIII — Confidence names a testable event | Frontend displays calibration artifact metadata | PASS |
| XIV — External evidence outranks confidence | Frontend emphasizes sources over confidence scores | PASS |
| XV — Ambiguity fails closed | Frontend shows doubt certificate for non-singleton sets | PASS |
| XVI — Uncertainty causes remain separate | Frontend displays uncertainty causes separately | PASS |
| XVII — Adaptive policies are calibrated | Frontend uses frozen backend calibration; no retraining | PASS |
| XVIII — Improvement changelog | Frontend references existing changelog | PASS |
| XIX — Agent trajectories | Frontend links to trajectory docs | PASS |
| XX — Baseline comparison | Frontend supports baseline/final comparison view | PASS |

**Gate Result**: PASS — frontend is a display-only layer over an already-compliant backend. No new medical logic, agents, or evidence handling introduced.

## Project Structure

### Documentation (this feature)

```text
specs/002-frontend-material/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api-contracts.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── app.py
├── config.py
├── utils.py
├── requirements.txt
├── Dockerfile
├── uat_test.py
└── components/
    ├── chatUI.py
    ├── upload.py
    └── history_download.py
```

**Structure Decision**: Reuse existing `frontend/` directory. Extend `chatUI.py` to display all CURA-Med response fields (doubt certificates, emergency responses, run artifact IDs). Add `uat_test.py` for end-to-end validation.

## Constitution Check (Post-Design)

*Re-evaluated after Phase 1 design.*

| Article | Relevance | Status |
|---------|-----------|--------|
| I — Evidence is the product boundary | Frontend displays sources and citations | PASS |
| II — Abstention is a valid successful outcome | Frontend renders doubt certificates | PASS |
| III — Human medical authority and review | Frontend shows disclaimer; no autonomous decisions | PASS |
| IV — Emergency safety behavior | Frontend displays emergency response within 2s | PASS |
| V — Corpus governance and time awareness | Frontend shows corpus provenance | PASS |
| VI — Privacy by construction | Frontend redacts PII in artifacts | PASS |
| VII — Untrusted-content isolation | Frontend renders evidence as text only | PASS |
| VIII — Structured, verifiable artifacts | Frontend displays schema-backed artifacts | PASS |
| IX — Fair and reproducible evaluation | Frontend includes UAT validation | PASS |
| X — Purposeful agentic complexity | Frontend adds no new agents | PASS |
| XI — Observability without surveillance | Frontend shows run IDs | PASS |
| XII — Disclaimer is not evidence | Frontend shows disclaimer without claiming correctness | PASS |
| XIII — Confidence names a testable event | Frontend displays calibration metadata | PASS |
| XIV — External evidence outranks confidence | Frontend emphasizes sources | PASS |
| XV — Ambiguity fails closed | Frontend shows doubt certificate for non-singleton sets | PASS |
| XVI — Uncertainty causes remain separate | Frontend displays uncertainty causes separately | PASS |
| XVII — Adaptive policies are calibrated | Frontend uses frozen backend calibration | PASS |
| XVIII — Improvement changelog | Frontend references existing changelog | PASS |
| XIX — Agent trajectories | Frontend links to trajectory docs | PASS |
| XX — Baseline comparison | Frontend supports baseline/final comparison | PASS |

**Post-Design Gate Result**: PASS — design introduces no new medical logic or evidence handling.

## Complexity Tracking

No constitution violations. Complexity is low: the frontend is a thin Streamlit wrapper over existing backend endpoints.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | — | — |
