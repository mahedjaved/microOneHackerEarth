# Implementation Plan: Comparative Study v2 - Rapid Remediation

**Branch:** `004-comparative-study-v2` | **Date:** 2026-08-30 | **Spec:** [spec.md](spec.md)

---

## Summary

Fix the comparative study framework to produce scientifically valid results by:
1. Making safety detection a gating criterion (not scored dimension)
2. Redesigning questions to be document-specific
3. Normalizing all scores to [0, 1] interval
4. Adding calibration metrics and variance reporting
5. Demonstrating UQ-RAG advantages clearly

## Technical Context

**Language/Version:** Python 3.10+ (existing project)
**Primary Dependencies:** FastAPI, requests, pytest (all already in project)
**Storage:** Local JSON for test results, HTML for reports
**Testing:** pytest, requests library
**Target Platform:** Local/Docker (existing environment)
**Project Type:** Test harness + scoring system
**Performance Goals:** Full test suite completes within 30 minutes
**Constraints:** Must complete by tomorrow (hackathon deadline)
**Scale/Scope:** 20 test questions, 3 systems, 3 test runs

## Constitution Check

| Article | Assessment | Status |
|---------|------------|--------|
| I — Evidence boundary | Document-specific questions enforce evidence requirement | PASS |
| II — Abstention valid | Doubt expression properly rewarded | PASS |
| III — Human authority | System provides evidence for reviewer | PASS |
| IV — Emergency safety | Safety as gating criterion | PASS |
| V — Corpus governance | Same frozen corpus for all systems | PASS |
| VI — Privacy | No real patient data in tests | PASS |
| VII — Untrusted isolation | Test questions are data, not instructions | PASS |
| VIII — Structured artifacts | JSON results + HTML report | PASS |
| IX — Fair evaluation | Same model, same questions for all | PASS |
| X — Purposeful complexity | Each fix addresses documented failure | PASS |
| XI — Observability | JSON artifacts with timestamps | PASS |
| XII — Disclaimer not evidence | Scoring based on observable behavior | PASS |
| XIII — Confidence names event | Calibration demonstration added | PASS |
| XIV — External evidence > confidence | Citation bonus in scoring | PASS |
| XV — Ambiguity fails closed | Doubt expression rewarded | PASS |
| XVI — Uncertainty causes separate | Safety/doubt/accuracy scored separately | PASS |
| XVII — Adaptive policies calibrated | N/A (no policy changes) | PASS |
| XVIII — Improvement changelog | This change will be documented | PASS |
| XIX — Agent trajectories | Full request/response captured | PASS |
| XX — Baseline comparison | Fair baselines, same conditions | PASS |

**Result:** All articles pass. No violations.

---

## Project Structure

### Documentation (this feature)

```text
specs/004-comparative-study-v2/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code Changes

```text
tests/comparative/
├── scoring.py           # REWRITE: New scoring system
├── test_dataset.py      # UPDATE: Document-specific questions
├── generate_report.py   # UPDATE: Calibration + variance
├── run_all.py           # UPDATE: Multiple runs with delays
└── results/             # JSON artifacts
```

---

## Complexity Tracking

> No Constitution violations — complexity tracking not required.

---
