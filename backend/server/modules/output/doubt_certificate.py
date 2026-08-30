"""
Doubt Certificate construction.

Constructs structured abstention records per contract schema.
"""

from typing import Optional
from server.schemas import (
    DoubtCertificate,
    Verdict,
    UncertaintyCause,
    UncertaintyCauseType,
    EAVAction,
    CalibrationArtifact,
)


def build_doubt_certificate(
    conformal_set: list[Verdict],
    uncertainty_causes: list[UncertaintyCause],
    corpus_id: str,
    calibration_artifact: CalibrationArtifact,
    actions_taken: list[EAVAction] | None = None,
    evidence_needed: str = "",
    support_probability: float = 0.0,
) -> DoubtCertificate:
    """
    Build a Doubt Certificate for abstention.

    Per Article II and Article XV.
    """
    status = "insufficient_evidence" if Verdict.INSUFFICIENT in conformal_set else "clarification_required"

    return DoubtCertificate(
        status=status,
        support_probability=support_probability,
        conformal_set=conformal_set,
        coverage_target=calibration_artifact.alpha if calibration_artifact else 0.90,
        uncertainty_causes=uncertainty_causes,
        actions_taken=actions_taken or [],
        evidence_needed=evidence_needed,
        corpus_id=corpus_id,
        calibration_id=calibration_artifact.calibration_id if calibration_artifact else "unknown",
        human_review_recommended=True,
    )


def uncertainty_cause_from_type(cause_type: UncertaintyCauseType, detail: str) -> UncertaintyCause:
    """Create an UncertaintyCause from type and detail."""
    return UncertaintyCause(type=cause_type, detail=detail)

