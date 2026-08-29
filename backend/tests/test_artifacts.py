"""Tests for CURA-Med run artifacts module."""

import pytest
import uuid
from server.modules.artifacts.run_artifact import build_run_artifact, redact_text
from server.schemas import (
    RunArtifact,
    EvidencePacket,
    Passage,
    RetrievalMetadata,
    Claim,
    SafetyScope,
    FinalDecision,
)


class TestRedactText:
    def test_redact_ssn(self):
        text = "My SSN is 123-45-6789"
        redacted, was_redacted = redact_text(text)
        assert was_redacted is True
        assert "123-45-6789" not in redacted

    def test_redact_email(self):
        text = "Contact me at user@example.com"
        redacted, was_redacted = redact_text(text)
        assert was_redacted is True
        assert "@" not in redacted

    def test_redact_phone(self):
        text = "Call me at 555-123-4567"
        redacted, was_redacted = redact_text(text)
        assert was_redacted is True
        assert "555-123-4567" not in redacted

    def test_no_redaction_for_clean_text(self):
        text = "What is aspirin used for?"
        redacted, was_redacted = redact_text(text)
        assert was_redacted is False
        assert redacted == text


class TestBuildRunArtifact:
    def setup_method(self):
        self.passages = [
            Passage(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_version="v1",
                page_location="page-1",
                text="Aspirin is a pain reliever",
                provenance_hash="abc123",
            )
        ]
        self.evidence_packet = EvidencePacket(
            corpus_id="test-corpus",
            corpus_hash="test-hash",
            retrieval_query="test",
            passages=self.passages,
            retrieval_metadata=RetrievalMetadata(
                retriever_version="test",
                top_k=1,
                latency_ms=0,
            ),
        )

    def test_build_run_artifact_basic(self):
        artifact = build_run_artifact(
            original_question="What is aspirin?",
            scope=SafetyScope.ALLOWED,
            corpus_id="test-corpus",
            corpus_hash="test-hash",
            model_version="test-model",
            verifier_version="test-verifier",
            calibration_id="cal-1",
            evidence_packet=self.evidence_packet,
            claims=[],
            evidence_features=[],
            verifier_outputs=[],
            conformal_sets=[],
            eav_actions=[],
            final_decision=FinalDecision.ANSWER,
            latency_ms=100,
        )
        assert isinstance(artifact, RunArtifact)
        assert artifact.final_decision == FinalDecision.ANSWER
        assert artifact.latency_ms == 100

    def test_build_run_artifact_redacts_pii(self):
        artifact = build_run_artifact(
            original_question="My SSN is 123-45-6789, what is aspirin?",
            scope=SafetyScope.ALLOWED,
            corpus_id="test-corpus",
            corpus_hash="test-hash",
            model_version="test-model",
            verifier_version="test-verifier",
            calibration_id="cal-1",
            evidence_packet=self.evidence_packet,
            claims=[],
            evidence_features=[],
            verifier_outputs=[],
            conformal_sets=[],
            eav_actions=[],
            final_decision=FinalDecision.ANSWER,
            latency_ms=100,
        )
        assert "123-45-6789" not in artifact.question.redacted_text

    def test_build_run_artifact_with_claims(self):
        claims = [
            Claim(
                claim_id=uuid.uuid4(),
                text="Aspirin is a pain reliever",
                citation_ids=["chunk-1"],
            )
        ]
        artifact = build_run_artifact(
            original_question="What is aspirin?",
            scope=SafetyScope.ALLOWED,
            corpus_id="test-corpus",
            corpus_hash="test-hash",
            model_version="test-model",
            verifier_version="test-verifier",
            calibration_id="cal-1",
            evidence_packet=self.evidence_packet,
            claims=claims,
            evidence_features=[],
            verifier_outputs=[],
            conformal_sets=[],
            eav_actions=[],
            final_decision=FinalDecision.ANSWER,
            latency_ms=100,
        )
        assert len(artifact.claims) == 1
        assert artifact.claims[0].text == "Aspirin is a pain reliever"
