# Implementation Plan: Bayesian Evidence Fusion for UQ-RAG

**Branch**: `001-bayesian-evidence-fusion` | **Date**: 2026-09-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-bayesian-evidence-fusion/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command; its definition describes the execution workflow.

## Summary

Replace the current `mean()`/`max()` evidence combination in the UQ-RAG verifier with
naive-Bayes log-odds combination over a stated prior. The change is a single
surgical edit to `_compute_support_probability` (per the expert analysis) plus
the supporting plumbing: probability clamping, claim relevance dampening,
conformal quantile minimization on a labeled calibration set, and backwards-compatible
`DoubtCertificate` schema updates. Also fixes the `ACCURACY_SUITE_IDS` stale-ID
bug in `generate_report.py` so the comparative study report's accuracy column
is internally consistent with the per-question table.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, Pydantic, scikit-learn, sentence-transformers, langchain (existing); no new dependencies (uses `math.log`/`math.exp` from stdlib)
**Storage**: Files (Pinecone for vector store, JSON files for results and the new calibration set)
**Testing**: pytest
**Target Platform**: Linux server (existing FastAPI backend)
**Project Type**: Web service (FastAPI backend)
**Performance Goals**: <5 ms per claim for the new log-odds fusion step (SC-007 regression check)
**Constraints**: Backwards-compatible DoubtCertificate schema (FR-010, FR-012); no new model artifacts
**Scale/Scope**: 30 questions in `suite=original`, scaling to `suite=uq_paper` + `suite=adversarial` (12 harder) for the falsification experiment

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Article I (Evidence is the product boundary)**: ✅ Feature directly enforces this by replacing ad-hoc max/mean with log-odds fusion over retrieved passages.
- **Article II (Abstention is a valid successful outcome)**: ✅ FR-006 + FR-013 (expected-loss-driven quantile) ensure abstention is principled, not arbitrary.
- **Article VIII (Structured, verifiable artifacts)**: ✅ FR-012 adds optional `prior`, `combined_posterior`, `relevance_weighted` fields; FR-014 records prior in every DoubtCertificate.
- **Article X (Purposeful agentic complexity)**: ✅ The new log-odds combiner is simpler than the RandomForest it's replacing in terms of the combination rule.
- **Article XIII (Confidence names a testable event)**: ✅ FR-002, FR-014 require prior to be recorded; FR-013 requires cost ratio to be recorded.
- **Article XV (Ambiguity fails closed)**: ✅ FR-009 forbids silent max/mean; the log-odds combiner with neutral passages correctly leaves posterior at prior (US2 scenario 3).
- **Article XVI (Uncertainty causes remain separate)**: ✅ `relevance_weighted` flag in DoubtCertificate (FR-012) records whether a low-relevance claim was down-weighted — preserving the cause.
- **Article XVIII (Improvement changelog)**: ✅ This plan and the resulting implementation will be recorded in the existing changelog workflow.
- **Article XX (Baseline comparison)**: ✅ The comparative study (`run_study.py` + `generate_report.py`) is the baseline. The fix corrects the report's accuracy column (FR-004, FR-005) so the baseline-to-final comparison is honest.

**No constitution violations. All gates pass.**

## Project Structure

### Documentation (this feature)

```text
specs/001-bayesian-evidence-fusion/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── contracts.md
├── checklists/
│   └── requirements.md
├── spec.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── server/
│   ├── modules/
│   │   ├── verifier/
│   │   │   ├── classifier.py       # Modified: relevance dampening
│   │   │   ├── conformal.py        # Modified: expected-loss-driven quantile
│   │   │   └── bayesian_fusion.py  # NEW: compute_support_probability
│   │   └── output/
│   │       └── doubt_certificate.py  # Modified: optional fields (prior, combined_posterior, relevance_weighted)
│   ├── routes/
│   │   └── ask_question.py          # Modified: feature flag UQ_USE_BAYESIAN_FUSION
│   └── config.py                    # Modified: read UQ_PRIOR, UQ_COST_RATIO
└── tests/                           # Existing test infrastructure

tests/comparative/
├── run_study.py                     # Unchanged (already correct after P1/P2)
├── generate_report.py               # Modified: import from test_dataset_enhanced (FR-004)
├── test_dataset_enhanced.py         # Existing — source of truth for suite IDs
├── test_dataset.py                  # Existing — legacy, do not delete
└── data/                            # NEW directory
    └── calibration_set.json         # NEW: labeled (claim, passage, support) triples (FR-011)

docs/
└── comparative_study_report.html    # Generated; corrected by FR-005
```

**Structure Decision**: Web service (backend FastAPI) — matches the existing
`backend/` layout. The new `bayesian_fusion.py` module lives under
`backend/server/modules/verifier/` alongside the existing `classifier.py` and
`conformal.py` modules. The calibration set lives under
`tests/comparative/data/` alongside the existing test datasets.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

No violations to track. The change is a simplification (mean/max → log-odds
combination) plus a backwards-compatible schema extension. No new dependencies,
no new agents, no new infrastructure.

## Generated Artifacts (Phase 0 + Phase 1)

- ✅ `research.md` — Phase 0: 6 design decisions, 0 unresolved questions
- ✅ `data-model.md` — Phase 1: 7 entities with field-level validation rules
- ✅ `contracts/contracts.md` — Phase 1: HTTP `/ask/` schema bump + module-level `compute_support_probability` contract
- ✅ `quickstart.md` — Phase 1: 6 validation scenarios with runnable commands

