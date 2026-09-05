# Contract: Config Flag — UQ_SUPPRESS_DOUBT_CERTIFICATE

**Feature**: [spec.md](spec.md)  
**Date**: 2026-09-05  
**Status**: Draft

## Purpose

Define the behavior contract for the `UQ_SUPPRESS_DOUBT_CERTIFICATE` configuration flag used in the abstention ablation.

## Location

`backend/server/config.py` — add to `Settings` class.

## Behavior

| Flag Value | Runtime Behavior |
|------------|------------------|
| `False` (default) | Full UQ-RAG pipeline. When the conformal set is ambiguous or evidence is insufficient, the system returns a structured `DoubtCertificate` with `uncertainty_causes`, `actions_taken`, `evidence_needed`, and `human_review_recommended`. |
| `True` | Identical pipeline through claim verification and conformal prediction, but the final output replaces the `DoubtCertificate` with a generic non-committal response and sets `doubt_certificate=None` in the API response. All other fields (`response`, `sources`, `disclaimer`, `run_artifact_id`) remain unchanged. |

## Constraints

- The flag MUST NOT affect retrieval, claim decomposition, verifier probabilities, or conformal prediction. It MUST only affect the final output formatting.
- The flag MUST be read at runtime from `settings.UQ_SUPPRESS_DOUBT_CERTIFICATE`.
- The flag MUST be documented in `backend/server/.env.example` with a comment explaining its purpose.
- The flag MUST default to `False` to preserve existing behavior.

## Observability

When the flag is `True`, the run artifact MUST include `"doubt_certificate_suppressed": true` so that downstream analysis can distinguish "system decided to abstain" from "system was forced to suppress abstention output."

## Consumer

`backend/server/modules/query_handlers.py` — reads the flag before constructing the final response.
`backend/server/modules/output/answer.py` — applies the suppression logic.
