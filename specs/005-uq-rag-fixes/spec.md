# Feature Specification: UQ-RAG Critical Bug Fixes & Evaluation Overhaul

**Feature Branch:** `005-uq-rag-fixes`
**Created:** 2026-08-30
**Status:** Draft
**Priority:** P0 (Submission deadline - fixes critical bugs blocking valid evaluation)

---

## Overview

Fix critical bugs identified by expert review that prevent UQ-RAG from demonstrating its true capabilities. These bugs cause UQ-RAG to score artificially low and, in some cases, prevent the UQ pipeline from executing at all.

---

## Problem Statement

Expert review identified four critical bugs:

1. **Gitignore excludes UQ source**: `backend/.gitignore:99` has `output/` rule that excludes `backend/server/modules/output/` from git. Fresh clones cannot initialize UQ pipeline.

2. **Scorer crashes on None responses**: `response_data.get("response", "").lower()` crashes when `response` key is present with value `None` (safety-gated UQ-RAG replies). The crash destroys the original API response data.

3. **Disclaimer field invisible to scorer**: UQ-RAG puts refusal/safety language in `disclaimer` field, but scorer only reads `response`. Correct safety refusals are marked as violations.

4. **Conformal predictor never runs**: `ConformalPredictor` is never fitted (`conformal.is_fitted = True` is a stub). Every non-safety query crashes silently and falls back to baseline RAG. The entire UQ pipeline (claim verification, conformal prediction, doubt certificates) never executes.

---

## User Stories

### User Story 1: Gitignore Fix (Priority: P0)

**As a** judge cloning the repo,
**I want to** have all source files present,
**So that** the UQ pipeline initializes correctly.

**Acceptance Criteria:**
- [ ] `backend/server/modules/output/` is tracked in git
- [ ] `.gitignore` rule scoped correctly to only exclude generated reports
- [ ] Fresh clone passes `test_output_modules.py`

---

### User Story 2: Scorer None-Crash Fix (Priority: P0)

**As a** system evaluating safety responses,
**I want to** handle `None` response fields gracefully,
**So that** safety-gated responses are scored correctly instead of crashing.

**Acceptance Criteria:**
- [ ] Score union of `response` + `disclaimer` + `doubt_certificate` fields
- [ ] API call and scoring call in separate try/except blocks
- [ ] Crashed responses tagged as `errored: True` (excluded from averages)
- [ ] Original API response preserved even if scoring fails

---

### User Story 3: Conformal Predictor Fix (Priority: P0)

**As a** system with UQ capabilities,
**I want to** execute the full UQ pipeline (claim verification, conformal prediction),
**So that** doubt certificates and verified answers are produced.

**Acceptance Criteria:**
- [ ] Add `ConformalPredictor.from_quantile()` classmethod
- [ ] Add `predict_set_from_probs()` using verifier probabilities
- [ ] Replace `conformal.is_fitted = True` stub with proper initialization
- [ ] `run_artifact_id` is populated (not None) on UQ-RAG factual answers

---

### User Story 4: Rate Limit Handling (Priority: P1)

**As a** test harness running multiple API calls,
**I want to** retry on 429/500 errors,
**So that** rate limits don't masquerade as wrong answers.

**Acceptance Criteria:**
- [ ] Retry-with-backoff around Groq API calls
- [ ] HTTP 429/500 treated as `errored` (excluded from behavioral average)
- [ ] Error rate reported separately from behavioral scores

---

## Functional Requirements

### FR-001: Gitignore Correction
System MUST track `backend/server/modules/output/` in git. The `.gitignore` rule MUST be scoped to only exclude actual generated output directories (e.g., `/backend/eval_reports/`).

### FR-002: Robust Scoring
Score union of all user-facing text fields (`response`, `disclaimer`, `doubt_certificate`). Handle `None` values gracefully. Tag system errors separately from behavioral failures.

### FR-003: Conformal Prediction
`ConformalPredictor` MUST be properly initialized from saved quantile. `predict_set_from_probs()` MUST use verifier probabilities for prediction.

### FR-004: Error Isolation
API calls and scoring MUST be in separate try/except blocks. Original API responses MUST be preserved regardless of scoring failures.

---

## Success Criteria

### Must Pass
- [ ] `git ls-files` includes `backend/server/modules/output/answer.py`
- [ ] Fresh clone initializes UQ pipeline without ModuleNotFoundError
- [ ] Scorer handles `None` response without crashing
- [ ] `run_artifact_id` is non-None for UQ-RAG factual answers
- [ ] S4 scored as 3 (correct refusal) not -1 (safety violation)

### Should Pass
- [ ] Error rate < 10% (rate limits handled gracefully)
- [ ] UQ-RAG composite score > 2.0 (statistically tied with baselines)

---

## Technical Approach

### Gitignore Fix
```bash
# Remove broad output/ rule, scope to specific directory
# In backend/.gitignore, replace:
#   output/
# With:
#   /backend/eval_reports/
git add -f backend/server/modules/output/
```

### Scorer Fix
```python
def get_scored_text(response_data: dict) -> str:
    """Score union of all user-facing text fields."""
    doubt_cert = response_data.get("doubt_certificate")
    doubt_text = ""
    if isinstance(doubt_cert, dict):
        doubt_text = doubt_cert.get("reason") or ""
    return " ".join(v for v in [
        response_data.get("response"),
        response_data.get("disclaimer"),
        doubt_text,
    ] if v).lower()
```

### Conformal Fix
```python
# ConformalPredictor.from_quantile()
@classmethod
def from_quantile(cls, quantile, alpha=0.10, method="LAC"):
    obj = cls(alpha=alpha, method=method)
    obj._quantile = quantile
    obj.is_fitted = True
    return obj

def predict_set_from_probs(self, prob_dict):
    included = [c for c, p in prob_dict.items() if (1.0 - p) <= self._quantile]
    return included or [Verdict.INSUFFICIENT]
```

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Conformal quantile too conservative | Medium | High | Plot risk-coverage curve, consider loosening alpha |
| Still lose to baselines on accuracy | Low | Medium | Document as findings, show improvement path |
| Rate limits persist | Low | Medium | Add longer delays, reduce test count |

---

## Out of Scope

- Full REFUTED class re-implementation (lower priority)
- EAVController action execution wiring
- ROC-informed retrieval threshold

---

*End of specification*
