# Implementation Plan: SourceProof Medical / CURA-Med

**Branch**: `001-sourceproof-medical` | **Date**: 2026-08-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-sourceproof-medical/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Build an evidence-constrained medical information assistant by extending the existing `backend/` FastAPI + Streamlit medical RAG system. The existing foundation provides PDF ingestion, LangChain RAG chain (Groq/Llama), Pinecone/Qdrant vector stores, Presidio PII detection, prompt-injection guards, LangSmith tracing, RAGAS evaluation, Prometheus/Grafana metrics, PostgreSQL logging, Docker/Compose, and CI/CD.

CURA-Med adds a UQ layer on top: medical-scope safety gate → claim decomposition → evidence feature vector → three-way verifier (GP + MAPIE) → split conformal prediction → Doubt Certificate / cited answer → optional EAV controller → structured run artifact.

Baseline is the existing `backend/` RAG pipeline unchanged. Advanced adds the verifier, conformal prediction, and EAV.

## Technical Context

**Language/Version**: Python 3.13 (backend/.python-version; pyproject.toml requires >=3.13)

**Primary Dependencies**: 
- Existing: FastAPI, Streamlit, LangChain, Groq, Pinecone, Presidio, LangSmith, RAGAS, Prometheus, PostgreSQL, pytest
- Add: scikit-learn (GaussianProcessClassifier), mapie (conformal prediction), sentence-transformers (embeddings), pydantic (schemas)

**Storage**: Existing: Pinecone (production), Qdrant (local dev), PostgreSQL (query logging). Add: JSONL for corpus chunks, JSON for run artifacts and calibration artifacts.

**Testing**: Existing: pytest with async tests. Add: unit tests for verifier, conformal prediction, EAV controller, safety gate.

**Target Platform**: Existing: Docker/Compose, Render/Fly.io deployment. Add: offline-capable after corpus download.

**Project Type**: Extend existing FastAPI backend + Streamlit frontend with new domain modules.

**Performance Goals**: Existing: rate-limited to 10 req/min. Add: emergency/safety responses <2s with no retrieval/generation calls.

**Constraints**: Existing: Presidio PII redaction, prompt-injection detection, rate limiting. Add: no real patient data, sandboxed execution, feature-gap signals optional.

**Scale/Scope**: Existing: 51-pair medical Q&A evaluation set. Add: PubMedQA (1,000 questions), MIRAGE (7,663 questions), synthetic adversarial set (30-50 cases), ~10k corpus chunks.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Check | Status |
|---------|-------|--------|
| I — Evidence is the product boundary | Verifier gates all material claims; unsupported claims removed or labelled. | PASS |
| II — Abstention is a valid successful outcome | Conformal set is the gate; non-singleton never produces answer. | PASS |
| III — Human medical authority and review | Reviewer required for ambiguous/high-risk cases; system delivers evidence only. | PASS |
| IV — Emergency safety behavior | Safety gate bypasses RAG; returns safety response in <2s. | PASS |
| V — Corpus governance and time awareness | Frozen two-part corpus with versioning, hashing, provenance. | PASS |
| VI — Privacy by construction | No real patient data; PII redaction before embedding/logging/caching. | PASS |
| VII — Untrusted-content isolation | Retrieved passages and user text treated as data; prompt injection blocked. | PASS |
| VIII — Structured, verifiable artifacts | All outputs (evidence packets, claims, doubt certificates, run artifacts) schema-validated. | PASS |
| IX — Fair and reproducible evaluation | Baseline and advanced on same frozen corpus, questions, config, resource limits. | PASS |
| X — Purposeful agentic complexity | Each component addresses a documented failure mode; independently switchable. | PASS |
| XI — Observability without surveillance | Run artifacts record all decisions; redacted before sharing. | PASS |
| XII — Disclaimer is not correctness | Doubt Certificate explicitly structured; fluency never overrides evidence. | PASS |
| XIII — Confidence names a testable event | Doubt Certificate includes probability semantics, corpus, model, calibration IDs. | PASS |
| XIV — External evidence outranks internal confidence | Verifier is authority; model self-reported confidence never authorizes claims. | PASS |
| XV — Ambiguity fails closed | Non-singleton set → abstain or EAV; never fallback to top-probability label. | PASS |
| XVI — Uncertainty causes remain separate | Evidence feature vector tracks separate channels; no collapsed confidence score. | PASS |
| XVII — Adaptive policies are calibrated end to end | Four disjoint splits; EAV frozen before evaluation. | PASS |
| XVIII — Improvement changelog | Required deliverable; every change recorded with evidence. | PASS |
| XIX — Agent trajectories | Required deliverable; captured for every agent. | PASS |
| XX — Baseline comparison | Fair baseline required; improvement claim derived from baseline-to-final. | PASS |

## Project Structure

### Documentation (this feature)

```text
specs/001-sourceproof-medical/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (extend existing backend)

```text
backend/
├── server/
│   ├── main.py                        # EXISTING - FastAPI app
│   ├── config.py                      # EXISTING - Pydantic settings
│   ├── schemas.py                     # EXTEND - add DoubtCertificate, RunArtifact, EAVAction schemas
│   ├── logger.py                      # EXISTING
│   ├── Dockerfile                     # EXISTING
│   ├── requirements.txt               # EXTEND - add scikit-learn, mapie, sentence-transformers
│   ├── modules/
│   │   ├── llm.py                     # EXISTING - Groq/Llama RetrievalQA chain
│   │   ├── load_vectorstore.py        # EXISTING - Pinecone/Qdrant
│   │   ├── pii_detector.py            # EXISTING - Presidio
│   │   ├── prompt_injection_detector.py # EXISTING - heuristic
│   │   ├── rate_limiter.py            # EXISTING
│   │   ├── metrics.py                 # EXISTING - Prometheus
│   │   ├── db_logger.py               # EXISTING - PostgreSQL
│   │   ├── langsmith_tracing.py       # EXISTING
│   │   ├── cache.py                   # EXISTING
│   │   ├── corpus/
│   │   │   ├── loader.py              # NEW - load and version corpus chunks with provenance
│   │   │   └── hash.py                # NEW - corpus hashing and versioning
│   │   ├── query_handlers.py          # EXTEND - add claim decomposition, verifier, EAV pipeline
│   │   ├── safety/
│   │   │   ├── gate.py                # NEW - medical-scope gate, emergency detection
│   │   │   └── isolation.py           # NEW - untrusted-content isolation
│   │   ├── claims/
│   │   │   ├── composer.py            # NEW - atomic claim decomposition from LLM answer
│   │   │   └── feature_vector.py      # NEW - 8-block evidence feature vector
│   │   ├── verifier/
│   │   │   ├── classifier.py          # NEW - GP classifier + CalibratedClassifierCV
│   │   │   ├── calibration.py         # NEW - probability calibration
│   │   │   └── conformal.py           # NEW - MAPIE split conformal prediction
│   │   ├── eav/
│   │   │   ├── controller.py          # NEW - EAV deterministic policy
│   │   │   ├── clarify.py             # NEW - clarification action
│   │   │   └── retrieve.py            # NEW - targeted retrieval action
│   │   ├── output/
│   │   │   ├── answer.py              # NEW - cited answer composer
│   │   │   ├── doubt_certificate.py   # NEW - Doubt Certificate construction
│   │   │   └── safety_response.py     # NEW - emergency safety response
│   │   └── artifacts/
│   │       └── run_artifact.py        # NEW - structured run artifact with redaction
│   ├── routes/
│   │   ├── ask_question.py            # EXTEND - insert UQ pipeline after retrieval
│   │   ├── upload_pdfs.py             # EXISTING
│   │   ├── health.py                  # EXISTING
│   │   ├── metrics.py                 # EXISTING
│   │   └── langsmith_health.py        # EXISTING
│   └── middlewares/
│       └── exceptionHandlers.py       # EXISTING
├── frontend/                          # EXISTING - Streamlit frontend
├── tests/                             # EXTEND - add tests for new modules
├── docker-compose.yml                 # EXISTING
├── pyproject.toml                     # EXISTING
├── requirements.txt                   # EXTEND
└── README.md                          # UPDATE
```

**Structure Decision**: Extend the existing `backend/` directory. New CURA-Med modules live under `backend/server/modules/` in new subdirectories (`safety/`, `claims/`, `verifier/`, `eav/`, `output/`, `artifacts/`). Existing modules (`llm.py`, `query_handlers.py`, `schemas.py`, `requirements.txt`) are extended in place.

**Integration point (Q6):** The `/ask/` route inserts the UQ pipeline after retrieval but before the existing RAG chain. The new `QuestionResponse` extends with optional `doubt_certificate` and `run_artifact_id` fields; `response` becomes nullable when a Doubt Certificate or safety response is returned. The existing LangChain `RetrievalQA` chain is preserved as the answer composer for the `{SUPPORTED}` path; the UQ layer wraps around it.

## Complexity Tracking

> No violations. All gates pass. Complexity is justified by constitution requirements.

