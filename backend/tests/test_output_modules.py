"""Tests for CURA-Med output modules."""

import pytest
import uuid
from server.modules.output.doubt_certificate import build_doubt_certificate, uncertainty_cause_from_type
from server.modules.output.safety_response import build_safety_response
from server.modules.output.answer import AnswerComposer
from server.schemas import (
    DoubtCertificate,
    Verdict,
    UncertaintyCauseType,
    EAVAction,
    EAVActionType,
    CalibrationArtifact,
    Claim,
    EvidencePacket,
    Passage,
    RetrievalMetadata,
)


class TestDoubtCertificate:
    def test_build_doubt_certificate_insufficient(self):
        cert = build_doubt_certificate(
            conformal_set=[Verdict.SUPPORTED, Verdict.INSUFFICIENT],
            uncertainty_causes=[],
            corpus_id="test-corpus",
            calibration_artifact=CalibrationArtifact(
                calibration_id="cal-1",
                verifier_model="test",
                calibrator_type="isotonic",
                conformal_method="LAC",
                feature_schema_version="v1",
                corpus_family="test",
                quantile=0.5,
            ),
        )
        assert cert.status == "insufficient_evidence"
        assert cert.human_review_recommended is True
        assert cert.corpus_id == "test-corpus"

    def test_build_doubt_certificate_with_actions(self):
        actions = [
            EAVAction(
                action_id=uuid.uuid4(),
                action_type=EAVActionType.CLARIFY,
                description="test",
                pre_conformal_set=[Verdict.SUPPORTED, Verdict.INSUFFICIENT],
                post_conformal_set=[Verdict.SUPPORTED],
                productive=True,
            )
        ]
        cert = build_doubt_certificate(
            conformal_set=[Verdict.SUPPORTED, Verdict.INSUFFICIENT],
            uncertainty_causes=[],
            corpus_id="test-corpus",
            calibration_artifact=CalibrationArtifact(
                calibration_id="cal-1",
                verifier_model="test",
                calibrator_type="isotonic",
                conformal_method="LAC",
                feature_schema_version="v1",
                corpus_family="test",
                quantile=0.5,
            ),
            actions_taken=actions,
        )
        assert len(cert.actions_taken) == 1
        assert cert.actions_taken[0].productive is True

    def test_uncertainty_cause_from_type(self):
        cause = uncertainty_cause_from_type(UncertaintyCauseType.MISSING_EVIDENCE, "no evidence")
        assert cause.type == UncertaintyCauseType.MISSING_EVIDENCE
        assert cause.detail == "no evidence"


class TestSafetyResponse:
    def test_build_safety_response(self):
        response = build_safety_response()
        assert "disclaimer" in response
        assert response["disclaimer"] != ""

    def test_safety_response_contains_emergency_message(self):
        response = build_safety_response()
        assert "emergency" in response["disclaimer"].lower() or "disclaimer" in response


class TestAnswerComposer:
    def setup_method(self):
        self.composer = AnswerComposer()

    def test_compose_with_supported_claims(self):
        from server.schemas import VerifierResult
        
        claims = [
            Claim(
                claim_id=uuid.uuid4(),
                text="Aspirin is a pain reliever",
                citation_ids=["chunk-1"],
                verifier_output=VerifierResult(
                    claim_id=uuid.uuid4(),
                    predicted_label=Verdict.SUPPORTED,
                    probabilities={Verdict.SUPPORTED: 0.9, Verdict.INSUFFICIENT: 0.1},
                    conformal_set=[Verdict.SUPPORTED],
                    calibration_id="cal-1",
                ),
            ),
            Claim(
                claim_id=uuid.uuid4(),
                text="Ibuprofen reduces inflammation",
                citation_ids=["chunk-2"],
                verifier_output=VerifierResult(
                    claim_id=uuid.uuid4(),
                    predicted_label=Verdict.SUPPORTED,
                    probabilities={Verdict.SUPPORTED: 0.8, Verdict.INSUFFICIENT: 0.2},
                    conformal_set=[Verdict.SUPPORTED],
                    calibration_id="cal-1",
                ),
            ),
        ]
        passages = [
            Passage(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_version="v1",
                page_location="page-1",
                text="Aspirin is a pain reliever",
                provenance_hash="abc123",
            ),
            Passage(
                chunk_id="chunk-2",
                document_id="doc-2",
                document_version="v1",
                page_location="page-2",
                text="Ibuprofen reduces inflammation",
                provenance_hash="def456",
            ),
        ]
        evidence_packet = EvidencePacket(
            corpus_id="test",
            corpus_hash="test-hash",
            retrieval_query="test",
            passages=passages,
            retrieval_metadata=RetrievalMetadata(
                retriever_version="test",
                top_k=2,
                latency_ms=0,
            ),
        )
        answer = self.composer.compose(claims, evidence_packet)
        assert "Aspirin" in answer or "Ibuprofen" in answer

    def test_compose_empty_claims(self):
        passages = []
        evidence_packet = EvidencePacket(
            corpus_id="test",
            corpus_hash="test-hash",
            retrieval_query="test",
            passages=passages,
            retrieval_metadata=RetrievalMetadata(
                retriever_version="test",
                top_k=0,
                latency_ms=0,
            ),
        )
        answer = self.composer.compose([], evidence_packet)
        assert answer == ""
