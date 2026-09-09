# Implementation Plan: abstention-measurement

**Branch**: `006-abstention-measurement` | **Date**: 2026-09-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-abstention-measurement/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Generate conference-ready evidence that the system's abstention mechanism is principled rather than arbitrary. The core artifact is a risk-coverage curve showing that higher confidence thresholds trade reduced coverage for lower error rate. Supporting artifacts include an adversarial perturbation comparison, an explicit-abstention ablation, and calibration metadata. All artifacts must be reproducible from a clean clone and must be generated only after the live pipeline uses calibrated Bayesian fusion rather than the legacy `max(probs)` path.

## Technical Context

**Language/Version**: Python 3.10 (backend), 3.13 (Docker)

**Primary Dependencies**: FastAPI, LangChain, Pinecone, scikit-learn, MAPIE, sentence-transformers, pytest, matplotlib, numpy

**Storage**: JSONL run artifacts in `data/runs/`, model artifacts in `data/models/`, index in `data/index/`

**Testing**: pytest for unit/integration tests; Playwright for regression/UI tests

**Target Platform**: Linux server / Docker container

**Project Type**: Web service (FastAPI backend + Streamlit frontend) with offline analysis scripts

**Performance Goals**: Risk-coverage curve generation from ~50 claims in under 5 seconds; abstention ablation on 30+ questions in under 2 minutes

**Constraints**: Conference deadline 2026-09-07; MVP is a pilot curve on ~30–50 claims, not a full benchmark. All artifacts must be reproducible from a clean clone with documented commands.

**Scale/Scope**: Single conference paper artifact; post-conference work expands to full benchmark.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Requirement | Status | Evidence |
|---------|-------------|--------|----------|
| I — Evidence is the product boundary | Every material claim MUST be supported by retrieved passages | PASS | Risk-coverage curve operates on per-claim `support_probability` derived from evidence features |
| II — Abstention is a valid successful outcome | System MUST return `insufficient_evidence` when corpus does not support reliable answer | PASS | Abstention is the explicit outcome being measured; curve quantifies the tradeoff |
| VIII — Structured, verifiable artifacts | Retrieval results, claims, verification decisions MUST conform to versioned schemas | PASS | `ClaimRecord` and `RiskCoverageArtifact` schemas defined in data-model.md |
| IX — Fair and reproducible evaluation | Baseline and advanced MUST be evaluated on same frozen corpus, questions, labels | PASS | Abstention ablation uses identical question set; calibration metadata recorded |
| XII — Disclaimer/citation count is not evidence of correctness | A disclaimer MUST NOT be treated as evidence of correctness | PASS | Curve measures actual `is_correct` labels, not surface confidence |
| XIII — Confidence names a testable event | Every probability MUST state predicted event, corpus, model/verifier version, calibration artifact | PASS | `CalibrationArtifact` includes verifier_model, calibrator_type, conformal_method, alpha, corpus_family, quantile |
| XIV — External evidence outranks internal confidence | Self-reported certainty MUST NOT independently authorize a medical claim | PASS | Risk-coverage curve is an offline diagnostic; it does not change runtime abstention policy |
| XV — Ambiguity fails closed | Non-singleton conformal set, missing calibration artifact, schema mismatch MUST NOT be converted to confident answer | PASS | Missing/stale calibration triggers fail-closed: display `uncalibrated` and abstain |
| XVI — Uncertainty causes remain separate | Query ambiguity, retrieval insufficiency, source conflict, generator uncertainty, verification uncertainty MUST be represented separately | PASS | `ClaimRecord` includes `perturbation_type` and `pipeline_mode` to separate causes |
| XVII — Adaptive policies are calibrated end to end | Any policy that uses uncertainty to retrieve, clarify, retry, or select a model MUST be frozen before final evaluation | PASS | Abstention ablation compares two frozen configurations on the same held-out set |
| XVIII — Improvement changelog | Every meaningful change MUST be recorded in versioned Improvement Changelog | PASS | This spec is itself a changelog entry; prior artifacts exist in `docs/` and `submission/` |
| XIX — Agent trajectories | Representative trajectories MUST be captured for every agent used in evaluation | PASS | `run_artifact_id` links claim records to full trajectories |
| XX — Baseline comparison | Fair baseline MUST exist and MUST be evaluated on same frozen corpus, questions, labels, model configuration, resource limits | PASS | Abstention ablation compares full UQ-RAG vs. abstention-suppressed on identical inputs |

**Gate Result**: PASS — all relevant articles satisfied. No violations require justification.

## Project Structure

### Documentation (this feature)

```text
specs/006-abstention-measurement/
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
│   ├── modules/
│   │   ├── verifier/
│   │   │   ├── bayesian_fusion.py      # Existing: compute_support_probability()
│   │   │   └── conformal.py            # Existing: ConformalPredictor
│   │   ├── query_handlers.py           # Live pipeline — must use Bayesian fusion
│   │   └── output/
│   │       ├── answer.py               # Existing: AnswerComposer
│   │       ├── doubt_certificate.py    # Existing: DoubtCertificate
│   │       └── safety_response.py      # Existing: SafetyResponse
│   ├── routes/
│   │   ├── ask_question.py             # UQ-RAG endpoint
│   │   ├── medrag_baseline.py          # Baseline endpoint
│   │   └── no_rag.py                   # No-RAG baseline endpoint
│   └── schemas.py                      # Pydantic models including DoubtCertificate
├── tests/
│   ├── comparative/
│   │   ├── test_dataset.py             # Existing test questions
│   │   ├── test_dataset_enhanced.py    # Existing adversarial cases
│   │   ├── scoring.py                  # Existing scorer (known bugs)
│   │   ├── test_comparison.py          # Existing comparison runner
│   │   ├── run_study.py                # Existing study runner
│   │   └── generate_report.py          # Existing HTML report generator
│   └── test_output_modules.py          # Existing output module tests
data/
├── models/                             # Prebuilt artifacts: verifier_gp.joblib, calibrator.joblib, conformal_quantile.json
├── corpus/
│   ├── mirage/mirage_pubmed_2000.jsonl # Existing corpus
│   └── adversarial/adversarial_cases.jsonl # Existing adversarial cases
└── runs/                               # [NEW] Exported claim records and risk-coverage artifacts
scripts/
├── train_verifier.py                   # Existing: trains verifier and calibrator
├── test_e2e.py                         # Existing: end-to-end UQ test
└── risk_coverage.py                    # [NEW] Generates risk-coverage curve from run artifacts
```

**Structure Decision**: This feature adds offline analysis scripts and JSONL export paths. No new backend routes or frontend components are required. All new code lives under `scripts/` and `data/runs/`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All constitution articles relevant to this feature pass without exception.
