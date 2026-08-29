import re
from pathlib import Path
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
import uuid
from datetime import datetime

from .constants.K import (
    MEDICAL_DISCLAIMER,
    MAX_QUESTION_LENGTH,
    MAX_ANSWER_LENGTH,
    MAX_SOURCE_LENGTH,
    MAX_UPLOAD_FILES,
    ALLOWED_FILE_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    MAX_SOURCES,
)

class Verdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INSUFFICIENT = "INSUFFICIENT"

class SafetyScope(str, Enum):
    ALLOWED = "allowed"
    EMERGENCY = "emergency"
    PROHIBITED = "prohibited"


class SafetyResult(BaseModel):
    scope: SafetyScope
    reason: str
    emergency_detected: bool = False
    diagnosis_detected: bool = False
    prescription_detected: bool = False
    patient_specific_risk_detected: bool = False


class EAVActionType(str, Enum):
    CLARIFY = "clarify"
    RETRIEVE = "retrieve"

class FinalDecision(str, Enum):
    ANSWER = "answer"
    DOUBT_CERTIFICATE = "doubt_certificate"
    CLARIFICATION = "clarification"
    SAFETY_RESPONSE = "safety_response"

class UncertaintyCauseType(str, Enum):
    MISSING_EVIDENCE = "missing_evidence"
    CROSS_SOURCE_CONFLICT = "cross_source_conflict"
    RETRIEVAL_INSTABILITY = "retrieval_instability"
    QUERY_AMBIGUITY = "query_ambiguity"
    VERIFIER_UNCERTAINTY = "verifier_uncertainty"
    SYSTEM_DRIFT = "system_drift"
    BUDGET_EXHAUSTED = "budget_exhausted"

class UncertaintyCause(BaseModel):
    type: UncertaintyCauseType
    detail: str

class EAVAction(BaseModel):
    action_id: uuid.UUID
    action_type: EAVActionType
    description: str
    pre_conformal_set: list[Verdict]
    post_conformal_set: list[Verdict] | None = None
    productive: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class VerifierResult(BaseModel):
    claim_id: uuid.UUID
    predicted_label: Verdict
    probabilities: dict[Verdict, float]
    calibrated: bool = False
    conformal_set: list[Verdict]
    coverage_target: float = 0.90
    calibration_id: str

class Claim(BaseModel):
    claim_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    text: str
    citation_ids: list[str] = Field(default_factory=list)
    verifier_output: VerifierResult | None = None

class LocalEntailment(BaseModel):
    max_support: float = 0.0
    mean_support: float = 0.0
    max_contradiction: float = 0.0
    mean_neutral: float = 0.0

class RetrievalQuality(BaseModel):
    top_score: float = 0.0
    score_margin: float = 0.0
    rank_dispersion: float = 0.0
    dense_lexical_agreement: float = 0.0

class Conflict(BaseModel):
    max_contradiction_score: float = 0.0
    support_refute_coexist: bool = False

class Provenance(BaseModel):
    document_version_valid: bool = True
    page_resolvable: bool = True
    citation_text_match_score: float = 0.0

class QueryAmbiguity(BaseModel):
    missing_entities: bool = False
    unresolved_pronouns: bool = False
    underspecified_scope: bool = False

class SystemState(BaseModel):
    corpus_id: str = ""
    model_version: str = ""
    verifier_version: str = ""
    calibration_age_days: int = 0
    drift_detected: bool = False

class EvidenceFeatureVector(BaseModel):
    claim_id: uuid.UUID
    local_entailment: LocalEntailment
    claim_coverage: float = 0.0
    retrieval_quality: RetrievalQuality
    conflict: Conflict
    provenance: Provenance
    query_ambiguity: QueryAmbiguity
    system_state: SystemState

class Passage(BaseModel):
    chunk_id: str
    document_id: str
    document_version: str
    page_location: str
    text: str
    provenance_hash: str

class RetrievalMetadata(BaseModel):
    retriever_version: str
    top_k: int
    latency_ms: int
    top_score: float | None = None
    score_margin: float | None = None
    rank_dispersion: float | None = None

class EvidencePacket(BaseModel):
    packet_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    corpus_id: str
    corpus_hash: str
    retrieval_query: str
    passages: list[Passage]
    retrieval_metadata: RetrievalMetadata

class DoubtCertificate(BaseModel):
    status: Literal["insufficient_evidence", "clarification_required"]
    message: Literal["I do not know from the approved evidence."] = "I do not know from the approved evidence."
    support_probability: float
    probability_semantics: Literal["P(claim fully supported by active retrieved evidence)"] = "P(claim fully supported by active retrieved evidence)"
    conformal_set: list[Verdict]
    coverage_target: float = 0.90
    uncertainty_causes: list[UncertaintyCause] = Field(default_factory=list)
    actions_taken: list[EAVAction] = Field(default_factory=list)
    evidence_needed: str = ""
    corpus_id: str
    calibration_id: str
    human_review_recommended: bool = False

class RedactedQuestion(BaseModel):
    run_id: uuid.UUID
    redacted_text: str
    scope: SafetyScope
    ambiguity_flags: list[str] = Field(default_factory=list)

class RunArtifact(BaseModel):
    run_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    question: RedactedQuestion
    corpus_id: str
    corpus_hash: str
    model_version: str
    verifier_version: str
    calibration_id: str
    evidence_packet: EvidencePacket
    claims: list[Claim] = Field(default_factory=list)
    evidence_features: list[EvidenceFeatureVector] = Field(default_factory=list)
    verifier_outputs: list[VerifierResult] = Field(default_factory=list)
    conformal_sets: list[dict] = Field(default_factory=list)
    eav_actions: list[EAVAction] = Field(default_factory=list)
    final_decision: FinalDecision
    latency_ms: int = 0

class CalibrationArtifact(BaseModel):
    calibration_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    verifier_model: str
    calibrator_type: Literal["temperature", "isotonic", "platt"]
    conformal_method: Literal["LAC", "APS"]
    alpha: float = 0.10
    feature_schema_version: str
    corpus_family: str
    quantile: float

class ExtendedQuestionResponse(BaseModel):
    response: str | None = None
    sources: list[str] = Field(default_factory=list, max_length=MAX_SOURCES)
    disclaimer: str = MEDICAL_DISCLAIMER
    injection_detected: bool = False
    pii_redacted: bool = False
    doubt_certificate: DoubtCertificate | None = None
    run_artifact_id: uuid.UUID | None = None

    model_config = ConfigDict(extra="forbid")


class UploadFileSchema(BaseModel):
    filename: str
    content_type: str
    size: int


class UploadResponse(BaseModel):
    message: str
    uploaded_files: list[str]
    index_name: str


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_LENGTH)


class QuestionResponse(BaseModel):
    response: str
    sources: list[str]
