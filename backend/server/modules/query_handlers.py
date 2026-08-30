"""
UQ pipeline orchestration for query handling.

Extends the existing query_handlers.py with the CURA-Med UQ layer:
safety gate → retrieval → claim decomposition → verifier → conformal →
{answer | doubt | EAV | safety}
"""

from typing import Optional
import time

from server.schemas import (
    SafetyScope,
    SafetyResult,
    EvidencePacket,
    Claim,
    EvidenceFeatureVector,
    VerifierResult,
    EAVAction,
    FinalDecision,
    RunArtifact,
    ExtendedQuestionResponse,
    DoubtCertificate,
    CalibrationArtifact,
)
from server.modules.safety.gate import classify_scope
from server.modules.safety.isolation import detect_injection, sanitize
from server.modules.claims.composer import ClaimComposer
from server.modules.claims.feature_vector import compute_feature_vector, compute_simple_features
from server.modules.verifier.classifier import ThreeWayVerifier
from server.modules.verifier.conformal import ConformalPredictor
from server.modules.eav.controller import EAVController
from server.modules.output.answer import AnswerComposer
from server.modules.output.doubt_certificate import build_doubt_certificate
from server.modules.output.safety_response import build_safety_response
from server.modules.artifacts.run_artifact import build_run_artifact
from server.logger import logger


# Global instances (loaded at startup)
_claim_composer: Optional[ClaimComposer] = None
_verifier: Optional[ThreeWayVerifier] = None
_conformal_predictor: Optional[ConformalPredictor] = None
_eav_controller: Optional[EAVController] = None
_answer_composer: Optional[AnswerComposer] = None
_calibration_artifact: Optional[CalibrationArtifact] = None
_embedding_model = None


def init_uq_pipeline(
    claim_composer: ClaimComposer,
    verifier: ThreeWayVerifier,
    conformal_predictor: ConformalPredictor,
    eav_controller: EAVController,
    answer_composer: AnswerComposer,
    calibration_artifact: CalibrationArtifact,
    embedding_model=None,
):
    """Initialize UQ pipeline components."""
    global _claim_composer, _verifier, _conformal_predictor, _eav_controller, _answer_composer, _calibration_artifact, _embedding_model
    _claim_composer = claim_composer
    _verifier = verifier
    _conformal_predictor = conformal_predictor
    _eav_controller = eav_controller
    _answer_composer = answer_composer
    _calibration_artifact = calibration_artifact
    _embedding_model = embedding_model


def run_uq_pipeline(
    question: str,
    evidence_packet: EvidencePacket,
    model_version: str = "groq/compound-mini",
    verifier_version: str = "gp-v1",
    llm_answer: str = "",
) -> tuple[ExtendedQuestionResponse, RunArtifact]:
    """
    Run the full UQ pipeline on a question with retrieved evidence.

    Returns (response, run_artifact).
    """
    start_time = time.time()

    # Step 1: Safety gate
    safety_result = classify_scope(question)
    if safety_result.scope == SafetyScope.EMERGENCY:
        safety_response = build_safety_response()
        artifact = build_run_artifact(
            original_question=question,
            scope=SafetyScope.EMERGENCY,
            corpus_id=evidence_packet.corpus_id,
            corpus_hash=evidence_packet.corpus_hash,
            model_version=model_version,
            verifier_version=verifier_version,
            calibration_id=_calibration_artifact.calibration_id if _calibration_artifact else "unknown",
            evidence_packet=evidence_packet,
            claims=[],
            evidence_features=[],
            verifier_outputs=[],
            conformal_sets=[],
            eav_actions=[],
            final_decision=FinalDecision.SAFETY_RESPONSE,
            latency_ms=int((time.time() - start_time) * 1000),
        )
        return ExtendedQuestionResponse(
            response=None,
            sources=[],
            doubt_certificate=None,
            run_artifact_id=artifact.run_id,
            disclaimer=safety_response["disclaimer"],
        ), artifact

    if safety_result.scope == SafetyScope.PROHIBITED:
        response = ExtendedQuestionResponse(
            response=None,
            sources=[],
            doubt_certificate=None,
            run_artifact_id=None,
            disclaimer=safety_result.reason,
        )
        artifact = build_run_artifact(
            original_question=question,
            scope=SafetyScope.PROHIBITED,
            corpus_id=evidence_packet.corpus_id,
            corpus_hash=evidence_packet.corpus_hash,
            model_version=model_version,
            verifier_version=verifier_version,
            calibration_id=_calibration_artifact.calibration_id if _calibration_artifact else "unknown",
            evidence_packet=evidence_packet,
            claims=[],
            evidence_features=[],
            verifier_outputs=[],
            conformal_sets=[],
            eav_actions=[],
            final_decision=FinalDecision.DOUBT_CERTIFICATE,
            latency_ms=int((time.time() - start_time) * 1000),
        )
        return response, artifact

    # Step 2: Claim decomposition (from LLM answer if available, else from evidence)
    claims = _claim_composer.decompose(llm_answer, evidence_packet)

    # Step 3: Evidence feature vector + verifier + conformal
    verifier_outputs = []
    conformal_sets = []
    evidence_features = []

    for claim in claims:
        # For C0 prototype: use simple embedding features for verifier
        evidence_text = " ".join(p.text for p in evidence_packet.passages) if evidence_packet.passages else ""
        simple_features = compute_simple_features(
            claim_text=claim.text,
            evidence_text=evidence_text,
            embedding_model=_embedding_model,
        )

        # Build EvidenceFeatureVector for artifact (production schema)
        feature_vector = compute_feature_vector(
            claim=claim,
            evidence_packet=evidence_packet,
            model_version=model_version,
            verifier_version=verifier_version,
            calibration_id=_calibration_artifact.calibration_id if _calibration_artifact else "unknown",
        )
        evidence_features.append(feature_vector)

        verifier_result = _verifier.predict_text(claim.text, evidence_text)
        verifier_outputs.append(verifier_result)

        conformal_set = _conformal_predictor.predict_set(simple_features.reshape(1, -1))[0]
        conformal_sets.append({"claim_id": str(claim.claim_id), "set": [v.name for v in conformal_set]})

    # Step 4: Decision logic
    all_singleton_supported = all(
        len(cs["set"]) == 1 and cs["set"][0] == "SUPPORTED"
        for cs in conformal_sets
    )

    if all_singleton_supported:
        # Cited answer path
        answer_text, sources = _answer_composer.compose_with_sources(claims, evidence_packet)
        artifact = build_run_artifact(
            original_question=question,
            scope=SafetyScope.ALLOWED,
            corpus_id=evidence_packet.corpus_id,
            corpus_hash=evidence_packet.corpus_hash,
            model_version=model_version,
            verifier_version=verifier_version,
            calibration_id=_calibration_artifact.calibration_id if _calibration_artifact else "unknown",
            evidence_packet=evidence_packet,
            claims=claims,
            evidence_features=evidence_features,
            verifier_outputs=verifier_outputs,
            conformal_sets=conformal_sets,
            eav_actions=[],
            final_decision=FinalDecision.ANSWER,
            latency_ms=int((time.time() - start_time) * 1000),
        )
        return ExtendedQuestionResponse(
            response=answer_text,
            sources=sources,
            doubt_certificate=None,
            run_artifact_id=artifact.run_id,
        ), artifact

    # Non-singleton or non-supported: Doubt Certificate or EAV
    uncertainty_causes = _infer_uncertainty_causes(evidence_features, conformal_sets)
    support_probability = _compute_support_probability(verifier_outputs)

    # Check EAV budget
    eav_action = _eav_controller.decide(
        evidence_features[0] if evidence_features else None,
        conformal_sets[0]["set"] if conformal_sets else [],
    )

    eav_actions = []
    post_conformal_set = None

    if eav_action:
        # Record EAV action (actual implementation would execute it)
        eav_record = _eav_controller.record_action(
            action_type=eav_action,
            pre_set=conformal_sets[0]["set"] if conformal_sets else [],
        )
        eav_actions.append(eav_record)
        # post_conformal_set would be computed after EAV action execution

    doubt_certificate = build_doubt_certificate(
        conformal_set=conformal_sets[0]["set"] if conformal_sets else ["INSUFFICIENT"],
        uncertainty_causes=uncertainty_causes,
        corpus_id=evidence_packet.corpus_id,
        calibration_artifact=_calibration_artifact,
        actions_taken=eav_actions,
        support_probability=support_probability,
    )

    artifact = build_run_artifact(
        original_question=question,
        scope=SafetyScope.ALLOWED,
        corpus_id=evidence_packet.corpus_id,
        corpus_hash=evidence_packet.corpus_hash,
        model_version=model_version,
        verifier_version=verifier_version,
        calibration_id=_calibration_artifact.calibration_id if _calibration_artifact else "unknown",
        evidence_packet=evidence_packet,
        claims=claims,
        evidence_features=evidence_features,
        verifier_outputs=verifier_outputs,
        conformal_sets=conformal_sets,
        eav_actions=eav_actions,
        final_decision=FinalDecision.DOUBT_CERTIFICATE,
        latency_ms=int((time.time() - start_time) * 1000),
    )

    return ExtendedQuestionResponse(
        response=None,
        sources=[],
        doubt_certificate=doubt_certificate,
        run_artifact_id=artifact.run_id,
    ), artifact


def _infer_uncertainty_causes(evidence_features: list[EvidenceFeatureVector], conformal_sets: list[dict]) -> list:
    """Infer uncertainty causes from evidence features and conformal sets."""
    from server.schemas import UncertaintyCause, UncertaintyCauseType
    causes = []

    if not evidence_features:
        causes.append(UncertaintyCause(type=UncertaintyCauseType.MISSING_EVIDENCE, detail="No evidence retrieved"))
        return causes

    fv = evidence_features[0]

    if fv.claim_coverage < 0.3:
        causes.append(UncertaintyCause(type=UncertaintyCauseType.MISSING_EVIDENCE, detail="Low claim coverage in retrieved passages"))

    if fv.conflict.support_refute_coexist:
        causes.append(UncertaintyCause(type=UncertaintyCauseType.CROSS_SOURCE_CONFLICT, detail="Retrieved passages contain conflicting information"))

    if fv.query_ambiguity.missing_entities or fv.query_ambiguity.underspecified_scope:
        causes.append(UncertaintyCause(type=UncertaintyCauseType.QUERY_AMBIGUITY, detail="Question lacks required qualifiers or entities"))

    if fv.retrieval_quality.top_score < 0.5:
        causes.append(UncertaintyCause(type=UncertaintyCauseType.RETRIEVAL_INSTABILITY, detail="Weak retrieval scores"))

    if fv.system_state.drift_detected:
        causes.append(UncertaintyCause(type=UncertaintyCauseType.SYSTEM_DRIFT, detail="Calibration artifact is stale"))

    if not causes:
        causes.append(UncertaintyCause(type=UncertaintyCauseType.VERIFIER_UNCERTAINTY, detail="Verifier probabilities are near-uniform"))

    return causes


def _compute_support_probability(verifier_outputs: list[VerifierResult]) -> float:
    """Compute average support probability across claims."""
    if not verifier_outputs:
        return 0.0
    probs = [vo.probabilities.get("SUPPORTED", 0.0) for vo in verifier_outputs]
    return sum(probs) / len(probs)


def query_chain(chain, user_input: str):
    """Legacy query chain helper - preserved for backward compatibility."""
    try:
        logger.debug(f"Running query chain for user input: {user_input}")
        result = chain({"query": user_input})
        response = {
            "response": result["result"],
            "sources": [
                doc.metadata.get("source", "Unknown")
                for doc in result["source_documents"]
            ],
        }
        logger.debug(f"Chain response: {result}")
        return response
    except Exception as e:
        logger.error(f"Error in query chain: {e}")
        return {
            "error": "An error occurred while processing your query. Please try again later."
        }

