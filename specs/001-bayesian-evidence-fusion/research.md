# Research: Bayesian Evidence Fusion for UQ-RAG

**Branch**: `001-bayesian-evidence-fusion`
**Date**: 2026-09-04
**Spec**: [../spec.md](../spec.md)

## Summary

This document consolidates the technical research and decisions for implementing the
Bayesian log-odds evidence fusion in the UQ-RAG claim-verification pipeline, replacing
the current mean/max combination. All Phase 0 unknowns from the plan have been
resolved; no clarification loops required.

## Decisions

### Decision 1: Use naive-Bayes log-odds (multinomial-style) combination over a stated prior

**Rationale**: The expert analysis from the conversation thread directly recommended
this — it is the simplest Bayesian combination rule that treats each per-passage
probability as an independent likelihood-ratio update to a shared prior. The math
is closed-form, O(n) in the number of passages, and requires only `math.log` and
`math.exp` from the Python stdlib. No new dependencies, no new model artifacts.
Matches the user's intent and the spec's FR-001, FR-002, FR-003.

**Alternatives considered**:
- Bayesian logistic regression with hand-specified priors on feature weights
  (recommended in the expert analysis as a *future* refactor of ThreeWayVerifier):
  explicitly out of scope for this iteration per the spec's Assumptions.
- Geometric mean of odds: equivalent to log-odds with a uniform prior, but doesn't
  generalize to non-uniform priors and is less principled when the prior matters
  (e.g., medical-safety default 0.5).
- Vote-counting with confidence weighting: ad hoc, no prior, no auditability.

### Decision 2: Probability clamping at `[1e-6, 1 - 1e-6]` before log-odds

**Rationale**: `log(0)` is undefined and `log(p / (1-p))` for p near 0 or 1
explodes numerically. Clamping at `1e-6` keeps the dynamic range bounded
(~±13.8 nats) and matches the spec's edge case requirement (FR-003) and
the "Numerical underflow" edge case.

**Alternatives considered**:
- Laplace smoothing (`(p * n + 1) / (n + 2)`): Bayesian-motivated, but requires
  a sample-size assumption per passage that we don't have; clamping is simpler
  and has the same numerical effect for our use case.
- No clamping: would crash on real data where any individual classifier
  might output 0.0 or 1.0.

### Decision 3: Conformal quantile from expected-loss minimization on a labeled set

**Rationale**: Matches the spec's FR-006, FR-007 and SC-004. The implementation
is a one-dimensional sweep over `[0, 1]` at coarse granularity (e.g., 0.01 steps)
to find the argmin of expected loss. Cost ratio default 10:1 (confident-wrong :
over-abstain) is defensible for medical-safety per Article XV. The labeled
set is created as part of this feature per FR-011 (Q1 clarification).

**Alternatives considered**:
- Keep the hand-tuned 0.5 quantile: explicitly called out as ad hoc in the
  expert analysis; rejected because it doesn't generalize beyond the specific
  cases it was tuned against.
- Use a Bayesian decision-theoretic threshold (minimize posterior expected loss):
  equivalent mathematically, but requires the labeled set anyway and is harder
  to explain to a reviewer.

### Decision 4: DoubtCertificate optional fields (backwards-compatible)

**Rationale**: Per Q3 clarification, add `prior: float | None`,
`combined_posterior: float | None`, `relevance_weighted: bool | None` as
**optional** fields. Existing consumers ignore them; new consumers can audit
the Bayesian reasoning. Article VIII (structured, verifiable artifacts) is
satisfied: every DoubtCertificate carries a record of what prior and posterior
were used.

**Alternatives considered**:
- Bump the schema version and require all fields: rejected (Q3 Option B) as a
  breaking change for downstream consumers.
- No schema change: rejected (Q3 Option A) because reviewers lose the ability
  to audit the prior choice per claim (Article XIII).

### Decision 5: Claim relevance via cosine similarity against the question

**Rationale**: The existing `ThreeWayVerifier` already produces per-claim
similarity-like features; cosine similarity to the question is the cheapest
proxy for "is this claim about the question at all" and matches the
expert's recommendation of down-weighting boilerplate. Threshold 0.3
(default, per Q3 not asked but consistent with Assumptions).

**Alternatives considered**:
- BM25 or keyword overlap: more expensive, not meaningfully better for
  detecting "Always consult a healthcare provider" boilerplate.
- LLM-based relevance scoring: more accurate but adds latency and a model
  dependency; rejected per SC-007's <5 ms budget.

### Decision 6: Calibration set format — JSON file, schema-versioned

**Rationale**: A simple JSON file of `(claim_text, passage_text, ground_truth_support: bool)`
triples is the minimum viable format. Path: `tests/comparative/data/calibration_set.json`,
schema version 1.0. Per Q1 clarification, this set is created as part of this
feature's deliverables (FR-011). It must cover medical_factual, safety, and
unknown/hallucination categories from `test_dataset_enhanced.py` (≥30 pairs).

**Alternatives considered**:
- CSV: less self-describing, harder to add metadata later.
- SQLite: overkill for ~30 rows; adds a dependency.
- Reuse the existing 1,200-example training set the ThreeWayVerifier was
  trained on: rejected because that set doesn't have (claim, passage, ground_truth_support)
  tuples; it's a classifier training set, not a calibration set.

## Open Questions (none blocking)

None. The five clarifications from `/speckit.clarify` resolved the highest-impact
categories, and the remaining implementation details (probability-clamp epsilon,
JSON file path, etc.) are documented above as decisions.

## Cross-references

- **Spec**: `../spec.md`
- **Constitution**: `../../../.specify/memory/constitution.md` — Articles I, II, VIII, X, XIII, XV, XVI, XVIII, XX
- **Plan template**: `../plan.md`
