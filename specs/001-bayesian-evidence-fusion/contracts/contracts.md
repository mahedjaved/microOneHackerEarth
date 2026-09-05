# Contracts: Bayesian Evidence Fusion for UQ-RAG

**Branch**: `001-bayesian-evidence-fusion`
**Date**: 2026-09-04
**Spec**: [../spec.md](../spec.md)
**Data model**: [../data-model.md](../data-model.md)

This feature exposes two contracts: a **public API contract** (the `/ask/` HTTP
endpoint, which the rest of the system and external integrators depend on) and a
**module-level contract** (the `compute_support_probability` function, which is
called by the verifier pipeline).

## Public API contract — `/ask/` HTTP endpoint

The `/ask/` endpoint signature is **unchanged** by this feature (FR-010). The
only change is in the response body: the `doubt_certificate` sub-object gains
three **optional** fields (`prior`, `combined_posterior`, `relevance_weighted`)
on the new code path. Existing clients that ignore unknown fields continue to
work; existing clients that strictly validate the schema need to opt in to
schema version `>= 1.1.0`.

### Request (unchanged)

```http
POST /ask/ HTTP/1.1
Content-Type: application/x-www-form-urlencoded

question=What%20is%20the%20maximum%20daily%20dose%20of%20aspirin%3F
```

### Response (new fields added in schema v1.1.0)

```json
{
  "response": "The maximum daily dose of aspirin for adults is 4 grams...",
  "sources": ["doc_id:aspirin_v1#page:3#chunk:42"],
  "doubt_certificate": {
    "errored": false,
    "conformal_set": [],
    "message": "Claim supported with high confidence.",
    "prior": 0.5,
    "combined_posterior": 0.87,
    "relevance_weighted": false
  }
}
```

**Field-level contract**:

| Field | Type | Required | Notes |
|---|---|---|---|
| `response` | `string` | yes | The final answer. May be `null` if abstained (Article II). |
| `sources` | `array<string>` | yes | Citation list (Article I, V). |
| `doubt_certificate` | `object` | yes | Verification outcome. |
| `doubt_certificate.errored` | `boolean` | yes | True if an exception occurred during verification. |
| `doubt_certificate.conformal_set` | `array<string>` | yes | Conformal prediction set; empty means abstained (Article XV). |
| `doubt_certificate.message` | `string` | yes | Human-readable explanation. |
| `doubt_certificate.prior` | `number \| null` | **new (v1.1.0)** | Prior probability used. `null` on legacy path. |
| `doubt_certificate.combined_posterior` | `number \| null` | **new (v1.1.0)** | Posterior after log-odds combination. `null` on legacy path. |
| `doubt_certificate.relevance_weighted` | `boolean \| null` | **new (v1.1.0)** | True if any passage was relevance-dampened. `null` on legacy path. |

**Schema version**: Bump `DoubtCertificate` schema to `1.1.0`. The change is
backwards-compatible (additive only). No request-side changes.

**Error responses** (unchanged):
- `422 Unprocessable Entity` — missing or invalid `question` field.
- `500 Internal Server Error` — backend pipeline error; `doubt_certificate.errored` will be `true`.

## Module-level contract — `compute_support_probability`

This is the function in `backend/server/modules/verifier/` (location TBD
during implementation) that combines per-passage support probabilities into a
final SUPPORTED probability for a claim.

### Function signature (new path)

```python
def compute_support_probability(
    passages: list[EvidencePassage],
    prior: float = 0.5,
    relevance_threshold: float = 0.3,
) -> tuple[float, bool]:
    """
    Combine per-passage SUPPORTED probabilities into a single posterior
    via naive-Bayes log-odds addition over a stated prior. Optionally
    dampen the contribution of low-relevance passages.

    Args:
        passages: Retrieved evidence passages with per-passage
            support_prob and relevance_to_question fields.
        prior: Probability of SUPPORTED before observing evidence.
            Default 0.5. Clamped to [1e-6, 1-1e-6] before log-odds.
        relevance_threshold: Passages with relevance_to_question
            below this value are dampened (likelihood ratio pulled
            toward 1.0). Default 0.3.

    Returns:
        (posterior, relevance_weighted):
            posterior: Combined support probability in [0, 1].
            relevance_weighted: True if any passage was dampened.
    """
```

### Behavioral contract (matches the three reference cases in spec US2)

| Inputs (passages) | Prior | Expected output | Notes |
|---|---|---|---|
| `[(0.8, 0.9), (0.7, 0.85)]` | 0.5 | `> 0.8` | Two independent positive updates reinforce. |
| `[(0.8, 0.9), (0.01, 0.85)]` | 0.5 | `≈ 0.8` | Off-topic passage is near-uninformative; posterior stays near the informative one. |
| `[(0.5, 0.9), (0.5, 0.85)]` | 0.5 | `= 0.5` | Neutral evidence doesn't move the prior. |
| `[]` | 0.5 | `= 0.5` | No evidence → return prior unchanged. |

### Property-based invariants

1. **Clamping**: For every `p` in `passages[i].support_prob`, the function MUST
   treat it as `clamp(p, 1e-6, 1-1e-6)` before log-odds (FR-003).
2. **Empty input**: If `passages` is empty, return `(prior, False)`.
3. **Monotonicity in informative evidence**: For all other inputs fixed, adding
   a passage with `support_prob > 0.5` MUST NOT decrease the posterior.
4. **Dampening**: A passage with `relevance_to_question < relevance_threshold`
   contributes a likelihood ratio of `exp(log((p / (1-p))) * 0.1)` (i.e., 10%
   weight) rather than the full ratio.
5. **Bounded output**: The returned `posterior` MUST be in `[0, 1]`.
6. **Reversibility**: The function is deterministic given the same inputs.

### Error handling

- `ValueError` if `prior` is not in `(0, 1)`.
- `ValueError` if `relevance_threshold` is not in `[0, 1]`.
- Per-passage `support_prob` or `relevance_to_question` outside `[0, 1]` is
  clamped silently (no exception).
- The function does not raise on empty `passages` (returns prior).

## Backwards compatibility

The new function coexists with the legacy `mean()` and `max()` combination
during a deprecation window. The legacy paths are removed once:
- All `EvidencePassage` records are produced by the new verifier (no
  upstream call sites still produce legacy-format records).
- All `DoubtCertificate` consumers (report generator, safety gate) read the
  new optional fields.

Until then, a feature flag `UQ_USE_BAYESIAN_FUSION` (env var) controls which
path is active:
- `UQ_USE_BAYESIAN_FUSION=1` (default) → new path with log-odds fusion and
  `DoubtCertificate.{prior, combined_posterior, relevance_weighted}` populated.
- `UQ_USE_BAYESIAN_FUSION=0` → legacy path with `mean()`/`max()` and
  `DoubtCertificate.{prior, combined_posterior, relevance_weighted} = None`.

## Test contracts

Three unit-test contracts (must pass before merge):

1. `test_log_odds_agreement`: `(0.8, 0.9), (0.7, 0.85), prior=0.5` → posterior
   strictly greater than `max(0.8, 0.7) = 0.8`. Tolerance: 1e-9.
2. `test_log_odds_offtopic`: `(0.8, 0.9), (0.01, 0.85), prior=0.5` → posterior
   within `0.1` of `0.8`. Tolerance: 0.1.
3. `test_log_odds_neutral`: `(0.5, 0.9), (0.5, 0.85), prior=0.5` → posterior
   exactly `0.5`. Tolerance: 1e-9.

Plus the closed-form check (SC-003): for any input, the returned posterior
MUST match the closed-form log-odds calculation to within `1e-6`.
