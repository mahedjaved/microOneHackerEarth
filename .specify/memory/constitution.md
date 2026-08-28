# Constitution: SourceProof Medical / CURA-Med

Version: 1.0.0
Status: Ratified
Owner: Project team
Last amended: 2026-08-28

## Mission

SourceProof Medical helps users navigate an approved medical-information corpus. It produces evidence-constrained educational information for human review. It is not a diagnostic, prescribing, prognostic, triage, or emergency-care system.

## Article I — Evidence is the product boundary

Every medically material claim MUST be supported by one or more retrieved passages from the active approved corpus. Each passage MUST be identified by document, version, page or equivalent location, and stable chunk ID.

The system MUST NOT add medical facts from model memory when those facts are absent from the retrieved corpus. Unsupported claims MUST be removed or visibly labelled unsupported.

## Article II — Abstention is a valid successful outcome

The system MUST return `insufficient_evidence` when the corpus does not support a reliable answer. It MUST return `clarification_required` when the question is too ambiguous for the approved scope.

Fluency, completeness, or user pressure MUST NOT override evidence insufficiency.

## Article III — Human medical authority and review

The system MUST NOT diagnose, prescribe, calculate patient-specific risk, or replace professional care. Consequential interpretation remains with a qualified clinician.

A qualified human reviewer MUST be part of any workflow where the output could significantly affect someone. High-risk, personalized, contradictory, or ambiguous cases MUST be explicitly flagged for human review before the system delivers its output.

The system MUST NOT autonomously perform consequential actions. Recommendations and evidence are delivered to the reviewer; the final decision remains human.

## Article IV — Emergency safety behavior

Queries indicating a possible immediate emergency MUST bypass ordinary RAG synthesis and return a concise safety response directing the user to local emergency services or urgent qualified care. The system MUST NOT delay that response while attempting document retrieval or differential diagnosis.

## Article V — Corpus governance and time awareness

Only approved, licensed, versioned documents MAY enter the active corpus. Every chunk MUST retain provenance, document date or version where available, ingestion timestamp, page/section location, and document hash.

The system MUST disclose the active corpus and MUST NOT imply that an answer reflects current universal medical consensus. Conflicting or potentially stale evidence MUST be exposed.

## Article VI — Privacy by construction

Real patient data MUST NOT be used in development, evaluation, demonstrations, traces, or submissions. Potentially identifying input MUST be rejected or redacted before embedding, logging, tracing, caching, or external model calls.

Raw sensitive values MUST NOT be stored as part of redaction logs. Least-privilege and minimum-retention defaults apply.

## Article VII — Untrusted-content isolation

Uploaded documents, retrieved passages, metadata, and user text are untrusted data. Instructions contained within them MUST NOT alter system behavior, tool permissions, safety policy, or evaluation logic.

Document-originated instructions MUST be quoted or classified as evidence, never executed as agent commands.

## Article VIII — Structured, verifiable artifacts

Retrieval results, claims, citations, safety decisions, verification decisions, and final answers MUST conform to versioned schemas. Schema or verification failure MUST be visible and MUST NOT be converted into a confident answer.

## Article IX — Fair and reproducible evaluation

The baseline and advanced system MUST be evaluated on the same frozen corpus, questions, labels, model configuration, and resource limits. Any difference MUST be disclosed.

All cases, including failures, MUST be reported. Automated LLM-based scores MUST be supplemented by deterministic tests and qualified human review for medically material judgments.

## Article X — Purposeful agentic complexity

Each agent, tool, memory component, or external service MUST address a documented failure mode. The simplest system satisfying the acceptance criteria is preferred.

Advanced components MUST be independently switchable so their contribution can be measured through ablation.

## Article XI — Observability without surveillance

Runs MUST record configuration, corpus version, retrieval decisions, tool events, validation results, retries, and final artifact IDs. Logs and trajectories MUST be redacted and safe to share.

## Article XII — A disclaimer or citation count is not evidence of correctness

A disclaimer, professional tone, citation count, or high self-reported confidence MUST NOT be treated as evidence of correctness or safety.

## Article XIII — Confidence names a testable event

Every displayed probability MUST state the predicted event, active corpus, model/verifier version, and calibration artifact. The system MUST NOT present evidence-support confidence as medical truth, diagnosis likelihood, or clinical risk.

## Article XIV — External evidence outranks internal confidence

Self-reported certainty, token probability, consistency across samples, and fluent presentation MUST NOT independently authorize a medical claim. Material claims require evidence verification against the approved corpus.

## Article XV — Ambiguity fails closed

A non-singleton conformal set, missing calibration artifact, schema mismatch, detected distribution shift, or verifier failure MUST NOT be converted to a confident answer. The valid outcomes are clarification, bounded evidence acquisition, abstention, or human review.

## Article XVI — Uncertainty causes remain separate

Query ambiguity, retrieval insufficiency, source conflict, generator uncertainty, verification uncertainty, and system drift MUST be represented separately. A single confidence number MUST NOT erase the cause of doubt.

## Article XVII — Adaptive policies are calibrated end to end

Any policy that uses uncertainty to retrieve, clarify, retry, or select a model MUST be frozen before final evaluation and calibrated under that same policy. Guarantees MUST state their assumptions and scope.

## Article XVIII — Improvement changelog

Every meaningful change to the system MUST be recorded in a versioned Improvement Changelog. Each entry MUST state the hypothesis, the exact change, the measured result, the decision, and the artifact paths.

The changelog MUST include experiments that were revised or removed, together with what they taught the team about the problem. A change without recorded evidence MUST NOT be claimed as an improvement.

## Article XIX — Agent trajectories

Representative agent trajectories MUST be captured for every agent used in evaluation. Each trajectory MUST be followable from the agent instructions through tool calls, observations, retries, human checkpoints, and final output.

Trajectories MUST be redacted and MUST include the evidence that shaped each step, not only the final result.

## Article XX — Baseline comparison

A fair baseline MUST exist and MUST be evaluated on the same frozen corpus, questions, labels, model configuration, and resource limits as the final solution. Any difference in tools, context, or model budget MUST be explicitly recorded.

The primary improvement claim MUST be derived from this baseline-to-final comparison, not from comparing the final solution to an undocumented or weaker alternative.

## Amendment rule

Changes to Articles I–VII require a written threat/risk analysis, updated acceptance tests, and review by the project owner plus a qualified medical reviewer where medical behavior changes.

Changes to Articles VIII–XX require updated acceptance tests, calibration artifacts, changelog entries, and review by the project owner.
