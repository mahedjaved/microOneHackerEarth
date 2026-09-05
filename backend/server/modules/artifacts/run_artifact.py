"""
Run artifact construction and redaction.

Constructs immutable run artifacts per Article XI.
Redacts PII and sensitive values before storage/sharing.
"""

import uuid
import re
from datetime import datetime
from typing import Optional
from server.schemas import (
    RunArtifact,
    RedactedQuestion,
    EvidencePacket,
    Claim,
    EvidenceFeatureVector,
    VerifierResult,
    EAVAction,
    FinalDecision,
    SafetyScope,
)


_PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]"),  # SSN
    (r"\b\d{16}\b", "[CARD REDACTED]"),  # Credit card
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL REDACTED]"),  # Email
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE REDACTED]"),  # Phone
]


def redact_text(text: str) -> tuple[str, bool]:
    """Redact PII from text. Returns (redacted_text, was_redacted)."""
    redacted = text
    for pattern, replacement in _PII_PATTERNS:
        if re.search(pattern, redacted):
            redacted = re.sub(pattern, replacement, redacted)
    was_redacted = redacted != text
    return redacted, was_redacted


def build_run_artifact(
    original_question: str,
    scope: SafetyScope,
    corpus_id: str,
    corpus_hash: str,
    model_version: str,
    verifier_version: str,
    calibration_id: str,
    evidence_packet: EvidencePacket,
    claims: list[Claim],
    evidence_features: list[EvidenceFeatureVector],
    verifier_outputs: list[VerifierResult],
    conformal_sets: list[dict],
    eav_actions: list[EAVAction],
    final_decision: FinalDecision,
    latency_ms: int,
    ambiguity_flags: list[str] | None = None,
    doubt_certificate_suppressed: bool = False,
) -> RunArtifact:
    """Build a complete run artifact with PII redaction."""
    redacted_text, pii_redacted = redact_text(original_question)

    question = RedactedQuestion(
        run_id=uuid.uuid4(),
        redacted_text=redacted_text,
        scope=scope,
        ambiguity_flags=ambiguity_flags or [],
    )

    return RunArtifact(
        run_id=question.run_id,
        timestamp=datetime.utcnow(),
        question=question,
        corpus_id=corpus_id,
        corpus_hash=corpus_hash,
        model_version=model_version,
        verifier_version=verifier_version,
        calibration_id=calibration_id,
        evidence_packet=evidence_packet,
        claims=claims,
        evidence_features=evidence_features,
        verifier_outputs=verifier_outputs,
        conformal_sets=conformal_sets,
        eav_actions=eav_actions,
        final_decision=final_decision,
        latency_ms=latency_ms,
        doubt_certificate_suppressed=doubt_certificate_suppressed,
    )

