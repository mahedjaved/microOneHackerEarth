# Data Model: Bayesian Evidence Fusion for UQ-RAG

**Branch**: `001-bayesian-evidence-fusion`
**Date**: 2026-09-04
**Spec**: [../spec.md](../spec.md)
**Research**: [../research.md](../research.md)

## Entities

### 1. EvidencePassage

A retrieved passage from the active corpus, with the verifier's per-passage
SUPPORTED probability and a relevance score against the question.

| Field | Type | Description | Validation |
|---|---|---|---|
| `text` | `str` | The passage text. | Non-empty. |
| `support_prob` | `float` | Per-passage SUPPORTED probability from the verifier (e.g., ThreeWayVerifier). | `0.0 <= support_prob <= 1.0`; clamped to `[1e-6, 1-1e-6]` before log-odds. |
| `relevance_to_question` | `float` | Cosine similarity between passage and question embedding. | `0.0 <= relevance_to_question <= 1.0`. |
| `source_doc_id` | `str` | Document ID from the active corpus. | Required (Article V provenance). |
| `chunk_id` | `str` | Stable chunk ID within the source document. | Required (Article V provenance). |
| `page_or_section` | `str \| None` | Page number or section heading. | Optional but recommended. |

**Relationships**:
- Belongs to one `Claim` (many-to-one).
- Many passages per claim, fused via log-odds.

---

### 2. Claim

An atomic factual statement extracted from the LLM's draft response, to be
verified against retrieved `EvidencePassage` records.

| Field | Type | Description | Validation |
|---|---|---|---|
| `claim_text` | `str` | The claim sentence. | Non-empty. |
| `support_posterior` | `float` | Final SUPPORTED probability after log-odds combination. | `0.0 <= support_posterior <= 1.0`; equals `prior` if no passages. |
| `prior` | `float` | Prior probability used as the log-odds starting point. | `0.0 <= prior <= 1.0`; default 0.5. |
| `passages` | `list[EvidencePassage]` | Retrieved evidence for this claim. | Length 0+; if length 0, posterior = prior. |
| `relevance_weighted` | `bool` | True if any passage's contribution was dampened due to low relevance. | Computed. |
| `doubt_certificate` | `DoubtCertificate` | The verification outcome for this claim. | See below. |

**State transitions**:
1. **Created** — `prior` is set (from config); `passages` is empty; `support_posterior = prior`.
2. **Passages added** — For each passage, apply log-odds update (with relevance dampening if `relevance_to_question < 0.3`); recompute `support_posterior`.
3. **Finalized** — `support_posterior` is the input to the conformal predictor; `doubt_certificate` is attached.

**Lifecycle**: Claims are created during the per-claim verification phase and destroyed
after the response is finalized. They are not persisted; only the `DoubtCertificate`
is recorded in the run artifact.

---

### 3. DoubtCertificate (schema-bumped, backwards-compatible)

A structured record attached to a `Claim` describing its verification outcome.
This is the audit artifact for the Bayesian reasoning.

| Field | Type | Description | Validation |
|---|---|---|---|
| `errored` | `bool` | True if verification raised an exception. | **Existing** — preserved unchanged. |
| `conformal_set` | `list[str]` | Conformal prediction set; empty if abstained. | **Existing** — preserved unchanged. |
| `message` | `str` | Human-readable explanation. | **Existing** — preserved unchanged. |
| `prior` | `float \| None` | **New (FR-012)** — Prior probability used. | `None` on legacy path; `0.0 <= prior <= 1.0` on new path. |
| `combined_posterior` | `float \| None` | **New (FR-012)** — Posterior after log-odds combination. | `None` on legacy path; `0.0 <= combined_posterior <= 1.0` on new path. |
| `relevance_weighted` | `bool \| None` | **New (FR-012)** — True if any passage was relevance-dampened. | `None` on legacy path; `True/False` on new path. |

**Schema version**: Bump to `1.1.0` (additive only; semver-compatible with `1.0.x`).
Existing consumers that ignore unknown fields continue to work.

---

### 4. Prior (configuration)

A stated probability of SUPPORTED, used as the starting point for log-odds updates.

| Field | Type | Description | Validation |
|---|---|---|---|
| `value` | `float` | The prior probability. | `0.0 < value < 1.0`; default `0.5`. |
| `source` | `str` | Where the value came from. | One of `"default"`, `"env:UQ_PRIOR"`, `"config:backend/server/config.py"`. |
| `recorded_at` | `datetime` | When the value was resolved (per-request or at startup). | ISO 8601. |

**Storage**: Config file (`backend/server/config.py`) or environment variable
(`UQ_PRIOR`). Recorded in every `DoubtCertificate.prior` for auditability.

---

### 5. ConformalQuantile (configuration)

The abstention threshold chosen by expected-loss minimization.

| Field | Type | Description | Validation |
|---|---|---|---|
| `value` | `float` | The chosen quantile. | `0.0 < value < 1.0`; reproducible from inputs (SC-004). |
| `cost_ratio` | `tuple[float, float]` | `(confident_wrong_cost, over_abstain_cost)`. | Both > 0; default `(10.0, 1.0)`. |
| `source` | `str` | Where the cost ratio came from. | One of `"default"`, `"env:UQ_COST_RATIO"`, `"config:..."`. |
| `calibration_set_path` | `str` | Path to the labeled set used for minimization. | Required (FR-011). |
| `recorded_at` | `datetime` | When the quantile was computed. | ISO 8601. |

**Storage**: Same as `Prior`. Recorded in run artifacts that contain
`conformal_set` so reviewers can reproduce the chosen quantile (FR-013, SC-004).

---

### 6. CalibrationSet (file)

A labeled set of `(claim_text, passage_text, ground_truth_support: bool)`
triples, used to compute the conformal quantile via expected-loss minimization.

| Field | Type | Description | Validation |
|---|---|---|---|
| `version` | `str` | Schema version of the file. | `"1.0"`. |
| `created_at` | `datetime` | When the file was created. | ISO 8601. |
| `entries` | `list[CalibrationEntry]` | The labeled triples. | Length ≥ 30 (FR-011). |
| `category_coverage` | `dict[str, int]` | Count of entries per `test_dataset_enhanced` category. | Each of `medical_factual`, `safety`, `unknown/hallucination` must have ≥ 5 entries. |

**CalibrationEntry**:
| Field | Type | Description | Validation |
|---|---|---|---|
| `claim_text` | `str` | The claim being verified. | Non-empty. |
| `passage_text` | `str` | The retrieved passage. | Non-empty. |
| `ground_truth_support` | `bool` | `True` if the passage supports the claim. | Required. |
| `category` | `str` | `medical_factual` \| `safety` \| `unknown` \| `hallucination`. | Required. |

**Path**: `tests/comparative/data/calibration_set.json` (created by this feature).

---

### 7. ComparativeStudyReport (existing, with corrections)

The HTML report produced by `generate_report.py`. This entity is not changed
by this feature, but the bug fix (FR-004, FR-005) corrects its data sourcing.

| Field | Type | Description | Validation |
|---|---|---|---|
| `aggregate_metrics` | `dict[system_name, AggregateMetrics]` | One entry per system. | See below. |
| `per_question_results` | `list[PerQuestionRow]` | One row per (question, system). | Length matches `test_dataset_enhanced` for the suite. |

**AggregateMetrics**:
| Field | Type | Description | Validation |
|---|---|---|---|
| `accuracy_avg` | `float` | Mean score on accuracy-suite questions. | Source: `test_dataset_enhanced` `ACCURACY_SUITE_IDS` (D1–D6 for original). **Fixed by FR-004.** |
| `safety_suite_avg` | `float` | Mean score on safety-suite questions. | Source: `test_dataset_enhanced` `SAFETY_SUITE_IDS` (S1–S4 for original). |
| `composite_score` | `float` | `(accuracy_avg + safety_suite_avg) / 2`. | Derived. |
| `error_count` | `int` | Number of errored API calls. | From `errored=True` entries. **New in P2.** |
| `error_rate` | `float` | `error_count / total_questions`. | From `error_count`. **New in P2.** |

**Invariant after FR-004 fix**: `accuracy_avg` MUST equal the hand-computed mean
of the D1–D6 per-question accuracy scores (SC-001, SC-002).

---

## Relationships

```
ComparativeStudyReport
  └── aggregate_metrics[system]
        ├── accuracy_avg   ← computed from per_question_results filtered by test_dataset_enhanced.ACCURACY_SUITE_IDS
        ├── safety_suite_avg
        ├── composite_score
        ├── error_count
        └── error_rate

  └── per_question_results
        └── PerQuestionRow (question_id, system, score)

Claim (transient, per-request)
  ├── prior             ← from config (Prior)
  ├── passages          ← list[EvidencePassage]
  └── doubt_certificate
        ├── errored
        ├── conformal_set ← from ConformalQuantile
        ├── message
        ├── prior             ← mirror of Claim.prior (FR-012, FR-014)
        ├── combined_posterior ← from log-odds combination
        └── relevance_weighted
```

## Validation rules (from spec)

- FR-002: `Prior.value` MUST be reported in every `DoubtCertificate` (per `DoubtCertificate.prior`).
- FR-003: `EvidencePassage.support_prob` MUST be clamped to `[1e-6, 1-1e-6]` before log-odds.
- FR-004: `aggregate_metrics.accuracy_avg` MUST be sourced from `test_dataset_enhanced.ACCURACY_SUITE_IDS`.
- FR-005: `ComparativeStudyReport.accuracy_avg` MUST match the hand-computed mean of D1–D6 scores.
- FR-006: `ConformalQuantile.value` MUST be reproducible from `(calibration_set, cost_ratio)`.
- FR-009: No silent mean/max anywhere in the claim-verification pipeline.
- FR-011: `CalibrationSet.entries` MUST have ≥ 30 triples spanning `medical_factual`, `safety`, and `unknown/hallucination`.
- FR-012: `DoubtCertificate.prior`, `combined_posterior`, `relevance_weighted` MUST be populated on the new path; `None` on the legacy path.
- FR-013: `ConformalQuantile.cost_ratio` MUST be sourced from config/env at startup.
- FR-014: `Prior.value` MUST be sourced from config/env at startup.
