# Research: Comparative Study Framework

**Feature**: 003-comparative-study
**Date**: 2026-08-30

## Overview

This document resolves all NEEDS CLARIFICATION items from the Technical Context and documents technology decisions for the comparative study framework.

## Research Items

### 1. MedRAG Baseline Implementation Pattern

**Decision**: Implement MedRAG-style RAG as a standalone endpoint using the same retrieval infrastructure (Pinecone) but without UQ components (safety gate, claim verification, conformal prediction, doubt certificates).

**Rationale**: The MedRAG paper (ACL 2024) defines a standard RAG pipeline: top-k retrieval → context concatenation → LLM generation. Our existing `simple_ask.py` already implements this pattern. The new `medrag_baseline.py` will replicate this with MedRAG-specific defaults (top-5 retrieval, standard medical prompt).

**Alternatives considered**:
- Clone actual MedRAG toolkit: Rejected due to dependency conflicts (ChromaDB, different LLM providers)
- Use existing `simple_ask.py` as-is: Rejected because spec requires explicit `/medrag_baseline/` endpoint with MedRAG-style configuration

### 2. No-RAG (Direct LLM) Baseline

**Decision**: Create `/no_rag/` endpoint that sends questions directly to Groq LLM without any retrieval or grounding.

**Rationale**: The existing `sota_ask.py` already implements this pattern. We create a new `no_rag.py` endpoint with the exact schema specified in FR-002 (response + system fields only, no sources/confidence).

**Alternatives considered**:
- Reuse `sota_ask.py`: Rejected because spec requires `/no_rag/` endpoint path
- Use a different model for baseline: Rejected per Article XX (same model configuration)

### 3. Test Dataset Design

**Decision**: 20+ questions across 4 categories with explicit expected keywords and behaviors.

**Rationale**: The existing test dataset has 12 questions. We expand to 20+ by adding:
- 2 more medical factual (dosage calculation, contraindications)
- 2 more safety-critical (pediatric emergency, drug interaction)
- 2 more unknown (alternative medicine, veterinary)
- 2 more hallucination probes (specific dates, manufacturer info)

**Alternatives considered**:
- Use MIRAGE benchmark questions: Rejected — requires 7,663 questions, too large for hackathon scope
- Use only existing 12 questions: Rejected — spec requires 20+

### 4. Scoring Algorithm

**Decision**: Category-specific scoring (0-3 scale) with keyword match ratio, safety detection, doubt expression, citation presence, and hallucination avoidance.

**Rationale**: Different question categories require different success criteria:
- Medical factual: keyword match + citation presence
- Safety-critical: emergency/prohibited detection
- Unknown: doubt expression
- Hallucination: abstention from answering

**Alternatives considered**:
- Single unified score: Rejected — cannot capture category-specific requirements
- LLM-as-judge scoring: Rejected per Constitution Article IX (deterministic tests required, LLM scores supplementary)

### 5. HTML Report Format

**Decision**: Static HTML with inline CSS, executive summary, per-question results table, aggregate metrics, and conclusions.

**Rationale**: Examiners need a self-contained evidence artifact that can be viewed in any browser. Static HTML requires no server, no JavaScript dependencies, and can be included in submission package.

**Alternatives considered**:
- Streamlit dashboard: Rejected — requires running server, not suitable for evidence package
- PDF report: Rejected — harder to generate programmatically, less interactive
- Jupyter notebook: Rejected — requires Python environment to view

### 6. Two Test Suites with Equal Weighting

**Decision**: Separate accuracy-prioritized and safety-prioritized test suites, final composite = average of both.

**Rationale**: Per spec clarifications and Constitution Article XX, safety and accuracy are equally important. The composite formula `(accuracy_suite_avg + safety_suite_avg) / 2` ensures neither dominates.

**Alternatives considered**:
- Single combined suite: Rejected — cannot demonstrate safety vs accuracy tradeoffs
- Weighted toward safety: Rejected — clarifications specify equal weighting
- Weighted toward accuracy: Rejected — clarifications specify equal weighting

### 7. Playwright E2E Test Coverage

**Decision**: Tests cover document upload → question submission → response verification → history download for all three systems.

**Rationale**: FR-006 requires complete user journey verification. Playwright tests must verify that the comparative study workflow works end-to-end through the Streamlit frontend.

**Alternatives considered**:
- API-only tests: Rejected — FR-006 explicitly requires E2E through frontend
- Separate tests per system: Rejected — single flow should test all systems

### 8. Endpoint Schema Consistency

**Decision**: All three endpoints return a common schema with optional fields for UQ-specific data.

**Rationale**: FR-007 requires `system` field. FR-001/FR-002 specify which fields are present/absent. Common schema simplifies scoring and comparison.

**Alternatives considered**:
- Completely different schemas per endpoint: Rejected — complicates scoring logic
- Minimal schema (only required fields): Rejected — examiners need full evidence

## Technology Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MedRAG implementation | Standalone endpoint with Pinecone | Avoids dependency conflicts |
| No-RAG implementation | Direct Groq LLM call | Matches spec FR-002 |
| Test dataset size | 20+ questions | Meets FR-003 minimum |
| Scoring scale | 0-3 per question | Granular enough for comparison |
| Report format | Static HTML | Self-contained evidence artifact |
| Test suite weighting | Equal (50/50) | Per clarifications |
| E2E test framework | Playwright | Already installed in project |
| Response schema | Common with optional fields | Simplifies scoring |

## Open Questions Resolved

All NEEDS CLARIFICATION items from the Technical Context have been resolved:

1. **Language/Version**: Python 3.11 (venv), Python 3.10 (system) — confirmed from existing project
2. **Primary Dependencies**: FastAPI, LangChain, Pinecone — all already in project
3. **Storage**: Pinecone + local JSON — confirmed from existing architecture
4. **Testing**: pytest + Playwright — both already installed
5. **Target Platform**: Local server deployment — confirmed from existing setup
6. **Performance Goals**: 30s per question, 5 min total — specified in SC-008/SC-009
7. **Constraints**: Local-only, no auth — confirmed from clarifications
8. **Scale/Scope**: 20+ questions, 3 systems — specified in FR-003

## References

- MedRAG Paper (ACL 2024): gzxiong/MedRAG
- MIRAGE Benchmark: gzxiong/MIRAGE
- Existing project: `backend/server/routes/` for endpoint patterns
- Existing tests: `tests/comparative/` for test patterns
