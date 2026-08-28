# Data Model: SourceProof Medical / CURA-Med

**Purpose**: Define entities, fields, relationships, validation rules, and state transitions as extensions to the existing `backend/` schemas.
**Derived from**: `spec.md` Key Entities + `constitution.md` governance requirements + existing `backend/server/schemas.py`.

---

## Extension Strategy

The existing `backend/server/schemas.py` defines:
- `QuestionRequest` — validated user question
- `QuestionResponse` — response with sources, disclaimer, injection_detected, pii_redacted
- `UploadFileSchema` / `UploadResponse` — PDF upload

CURA-Med extends these with:

### New schemas added to `backend/server/schemas.py`

```python
class DoubtCertificate(BaseModel):
    status: Literal["insufficient_evidence", "clarification_required"]
    message: Literal["I do not know from the approved evidence."]
    support_probability: float
    probability_semantics: Literal["P(claim fully supported by active retrieved evidence)"]
    conformal_set: list[Verdict]
    coverage_target: float
    uncertainty_causes: list[UncertaintyCause]
    actions_taken: list[EAVAction]
    evidence_needed: str
    corpus_id: str
    calibration_id: str
    human_review_recommended: bool

class RunArtifact(BaseModel):
    run_id: UUID
    timestamp: datetime
    question: RedactedQuestion
    corpus_id: str
    corpus_hash: str
    model_version: str
    verifier_version: str
    calibration_id: str
    evidence_packet: EvidencePacket
    claims: list[Claim]
    evidence_features: list[EvidenceFeatureVector]
    verifier_outputs: list[VerifierResult]
    conformal_sets: list[ConformalDecisionSet]
    eav_actions: list[EAVAction]
    final_decision: Literal["answer", "doubt_certificate", "clarification", "safety_response"]
    latency_ms: int

class Claim(BaseModel):
    claim_id: UUID
    text: str
    citation_ids: list[str]
    verifier_output: VerifierResult | None

class VerifierResult(BaseModel):
    claim_id: UUID
    predicted_label: Verdict
    probabilities: dict[Verdict, float]
    calibrated: bool
    conformal_set: list[Verdict]
    coverage_target: float
    calibration_id: str

class EvidenceFeatureVector(BaseModel):
    claim_id: UUID
    local_entailment: LocalEntailment
    claim_coverage: float
    retrieval_quality: RetrievalQuality
    conflict: Conflict
    provenance: Provenance
    query_ambiguity: QueryAmbiguity
    system_state: SystemState

class EAVAction(BaseModel):
    action_id: UUID
    action_type: Literal["clarify", "retrieve"]
    description: str
    pre_conformal_set: list[Verdict]
    post_conformal_set: list[Verdict] | None
    productive: bool
    timestamp: datetime
```

### Extended `QuestionResponse`

```python
class QuestionResponse(BaseModel):
    response: str | None  # None if Doubt Certificate or safety response
    sources: list[str]
    disclaimer: str
    injection_detected: bool
    pii_redacted: bool
    doubt_certificate: DoubtCertificate | None  # NEW
    run_artifact_id: UUID | None  # NEW
```

---

## Entity Details

### Question (extends existing QuestionRequest)

**Existing fields**: `question: str` (validated, max length, null-char check)

**New fields**:
- `scope`: `SafetyScope` enum — `allowed`, `emergency`, `prohibited`
- `ambiguity_flags`: list of `AmbiguityFlag`
- `redacted_text`: str (PII-redacted version)

**Validation**:
- If `scope` is `emergency` or `prohibited`, retrieval and generation MUST NOT be called (Article IV).
- PII matches MUST be redacted before downstream processing (Article VI).

---

### EvidencePacket (new)

**Fields**:
- `packet_id`: UUID
- `corpus_id`: str
- `corpus_hash`: str (SHA-256)
- `retrieval_query`: str
- `passages`: list of `Passage`
- `retrieval_metadata`: `RetrievalMetadata`

**Validation**:
- All passages MUST have non-empty `text`, `chunk_id`, `document_id`, `document_version`.
- `corpus_hash` MUST match active corpus at retrieval time (Article V).

---

### Passage (new)

**Fields**:
- `chunk_id`: str
- `document_id`: str
- `document_version`: str
- `page_location`: str
- `text`: str
- `provenance_hash`: str (SHA-256)

**Validation**:
- `provenance_hash` MUST match computed hash (Article V).

---

### Claim (new)

**Fields**:
- `claim_id`: UUID
- `text`: str
- `citation_ids`: list[str] (references to `EvidencePacket.passages`)
- `verifier_output`: `VerifierResult | None`

**Validation**:
- Every medically material claim MUST have at least one `citation_id` (Article I).

---

### EvidenceFeatureVector (new)

**Fields**:
- `claim_id`: UUID
- `local_entailment`: `LocalEntailment` — max/mean support, contradiction, neutral
- `claim_coverage`: float (0.0–1.0)
- `retrieval_quality`: `RetrievalQuality` — top_score, score_margin, rank_dispersion, dense_lexical_agreement
- `conflict`: `Conflict` — max_contradiction, support_refute_coexist
- `provenance`: `Provenance` — document_version_valid, page_resolvable, citation_text_match_score
- `query_ambiguity`: `QueryAmbiguity` — missing_entities, unresolved_pronouns, underspecified_scope
- `system_state`: `SystemState` — corpus_id, model_version, verifier_version, calibration_age_days, drift_detected

---

### VerifierResult (new)

**Fields**:
- `claim_id`: UUID
- `predicted_label`: `Verdict` enum — `SUPPORTED`, `REFUTED`, `INSUFFICIENT`
- `probabilities`: dict[Verdict, float] (sum to 1.0)
- `calibrated`: bool
- `conformal_set`: list[Verdict]
- `coverage_target`: float
- `calibration_id`: str

**Validation**:
- `probabilities` MUST sum to 1.0.
- `conformal_set` MUST NOT be empty (Article XV).

---

### ConformalDecisionSet (new)

**Fields**:
- `claim_id`: UUID
- `set`: list[Verdict]
- `coverage_target`: float
- `is_singleton`: bool

**Decision mapping** (Article XV):
```
{SUPPORTED}           → show answer
{REFUTED}             → remove claim, report contradiction
{INSUFFICIENT}        → remove claim, abstain
Any 2-3 label set     → invoke EAV once, then abstain
```

---

### DoubtCertificate (new)

**Fields**:
- `status`: `insufficient_evidence` | `clarification_required`
- `message`: "I do not know from the approved evidence."
- `support_probability`: float
- `probability_semantics`: "P(claim fully supported by active retrieved evidence)"
- `conformal_set`: list[Verdict]
- `coverage_target`: float
- `uncertainty_causes`: list[UncertaintyCause]
- `actions_taken`: list[EAVAction]
- `evidence_needed`: str
- `corpus_id`: str
- `calibration_id`: str
- `human_review_recommended`: bool

---

### EAVAction (new)

**Fields**:
- `action_id`: UUID
- `action_type`: `clarify` | `retrieve`
- `description`: str
- `pre_conformal_set`: list[Verdict]
- `post_conformal_set`: list[Verdict] | None
- `productive`: bool
- `timestamp`: datetime

**Validation**:
- At most one EAV action per execution per claim (Article XV via spec FR-010).

---

### RunArtifact (new)

**Fields**:
- `run_id`: UUID
- `timestamp`: datetime
- `question`: `RedactedQuestion`
- `corpus_id`: str
- `corpus_hash`: str
- `model_version`: str
- `verifier_version`: str
- `calibration_id`: str
- `evidence_packet`: `EvidencePacket`
- `claims`: list[Claim]
- `evidence_features`: list[EvidenceFeatureVector]
- `verifier_outputs`: list[VerifierResult]
- `conformal_sets`: list[ConformalDecisionSet]
- `eav_actions`: list[EAVAction]
- `final_decision`: `answer` | `doubt_certificate` | `clarification` | `safety_response`
- `latency_ms`: int

**Validation**:
- All sensitive values MUST be redacted before storage or sharing (Article XI, Article VI).
- Artifact MUST be immutable after creation.

---

### CalibrationArtifact (new)

**Fields**:
- `calibration_id`: str
- `created_at`: datetime
- `verifier_model`: str
- `calibrator_type`: `temperature` | `isotonic` | `platt`
- `conformal_method`: `LAC` | `APS`
- `alpha`: float
- `feature_schema_version`: str
- `corpus_family`: str
- `quantile`: float

---

## Enums and Value Objects

### SafetyScope
- `allowed` — proceed with retrieval and generation
- `emergency` — bypass to safety response
- `prohibited` — reject with scope explanation

### Verdict
- `SUPPORTED` — evidence supports the claim
- `REFUTED` — evidence contradicts the claim
- `INSUFFICIENT` — evidence does not establish the claim

### AmbiguityFlag
- `missing_entity` — required entity not present
- `missing_date` — required date/time qualifier missing
- `unresolved_pronoun` — pronoun reference unclear
- `underspecified_scope` — question too broad

### UncertaintyCause
- `missing_evidence` — no passage establishes the claim
- `cross_source_conflict` — passages contradict each other
- `retrieval_instability` — dense and lexical retrieval returned disjoint results
- `query_ambiguity` — question lacks required qualifiers
- `verifier_uncertainty` — classifier probabilities near-uniform
- `system_drift` — calibration artifact stale or corpus shifted
- `budget_exhausted` — EAV action budget used without resolution
