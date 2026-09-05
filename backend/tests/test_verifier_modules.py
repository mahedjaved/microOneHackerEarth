"""Tests for CURA-Med verifier modules."""

import uuid
import numpy as np
import pytest
from server.modules.verifier.classifier import ThreeWayVerifier
from server.modules.verifier.calibration import ProbabilityCalibrator
from server.modules.verifier.conformal import ConformalPredictor


class TestThreeWayVerifier:
    def test_train_and_predict_binary(self):
        verifier = ThreeWayVerifier()
        X = np.array([
            [0.9, 0.1, 0.5],
            [0.8, 0.2, 0.6],
            [0.7, 0.3, 0.5],
            [0.2, 0.9, 0.3],
            [0.1, 0.8, 0.4],
            [0.3, 0.7, 0.2],
        ])
        y = np.array(["SUPPORTED", "SUPPORTED", "SUPPORTED", "INSUFFICIENT", "INSUFFICIENT", "INSUFFICIENT"])
        verifier.train(X, y)
        assert verifier.is_trained is True

    def test_predict_returns_verifier_result(self):
        verifier = ThreeWayVerifier()
        X = np.array([
            [0.9, 0.1, 0.5],
            [0.8, 0.2, 0.6],
            [0.7, 0.3, 0.5],
            [0.2, 0.9, 0.3],
            [0.1, 0.8, 0.4],
            [0.3, 0.7, 0.2],
        ])
        y = np.array(["SUPPORTED", "SUPPORTED", "SUPPORTED", "INSUFFICIENT", "INSUFFICIENT", "INSUFFICIENT"])
        verifier.train(X, y)
        
        class MockEmbeddingModel:
            def encode(self, text, show_progress_bar=False):
                return np.array([0.5, 0.5, 0.5])
        
        verifier.embedding_model = MockEmbeddingModel()
        result = verifier.predict_text("test claim", "test evidence")
        assert result.predicted_label in ["SUPPORTED", "INSUFFICIENT"]
        assert result.calibrated is True
        assert result.claim_id is not None

    def test_predict_without_embedding_model_raises(self):
        verifier = ThreeWayVerifier()
        X = np.array([
            [0.9, 0.1, 0.5],
            [0.8, 0.2, 0.6],
            [0.7, 0.3, 0.5],
            [0.2, 0.9, 0.3],
            [0.1, 0.8, 0.4],
            [0.3, 0.7, 0.2],
        ])
        y = np.array(["SUPPORTED", "SUPPORTED", "SUPPORTED", "INSUFFICIENT", "INSUFFICIENT", "INSUFFICIENT"])
        verifier.train(X, y)
        with pytest.raises(RuntimeError):
            verifier.predict_text("test", "test")

    def test_predict_without_training_raises(self):
        verifier = ThreeWayVerifier()
        with pytest.raises(RuntimeError):
            verifier.predict_text("test", "test")

    def test_save_and_load(self, tmp_path):
        verifier = ThreeWayVerifier()
        X = np.array([
            [0.9, 0.1, 0.5],
            [0.8, 0.2, 0.6],
            [0.7, 0.3, 0.5],
            [0.2, 0.9, 0.3],
            [0.1, 0.8, 0.4],
            [0.3, 0.7, 0.2],
        ])
        y = np.array(["SUPPORTED", "SUPPORTED", "SUPPORTED", "INSUFFICIENT", "INSUFFICIENT", "INSUFFICIENT"])
        verifier.train(X, y)
        
        model_path = str(tmp_path / "verifier.joblib")
        verifier.save(model_path)
        
        loaded = ThreeWayVerifier(model_path=model_path)
        assert loaded.is_trained is True


class TestProbabilityCalibrator:
    def test_fit_and_transform(self):
        calibrator = ProbabilityCalibrator(method="isotonic")
        probs = np.array([[0.9, 0.1], [0.2, 0.8], [0.7, 0.3]])
        labels = np.array([0, 1, 0])
        calibrator.fit(probs, labels)
        assert calibrator.is_fitted is True

    def test_transform_normalizes(self):
        calibrator = ProbabilityCalibrator(method="isotonic")
        probs = np.array([[0.9, 0.1], [0.2, 0.8]])
        labels = np.array([0, 1])
        calibrator.fit(probs, labels)
        
        calibrated = calibrator.transform(probs)
        assert calibrated.shape == probs.shape
        assert np.allclose(calibrated.sum(axis=1), 1.0)

    def test_save_and_load(self, tmp_path):
        calibrator = ProbabilityCalibrator(method="isotonic")
        probs = np.array([[0.9, 0.1], [0.2, 0.8]])
        labels = np.array([0, 1])
        calibrator.fit(probs, labels)
        
        path = str(tmp_path / "calibrator.joblib")
        calibrator.save(path)
        
        loaded = ProbabilityCalibrator.load(path)
        assert loaded.is_fitted is True
        assert loaded.method == "isotonic"


class TestConformalPredictor:
    def test_fit_and_predict_set(self):
        verifier = ThreeWayVerifier()
        X = np.array([
            [0.9, 0.1, 0.5],
            [0.8, 0.2, 0.6],
            [0.7, 0.3, 0.5],
            [0.2, 0.9, 0.3],
            [0.1, 0.8, 0.4],
            [0.3, 0.7, 0.2],
        ])
        y = np.array(["SUPPORTED", "SUPPORTED", "SUPPORTED", "INSUFFICIENT", "INSUFFICIENT", "INSUFFICIENT"])
        verifier.train(X, y)
        
        conformal = ConformalPredictor(alpha=0.10, method="LAC")
        conformal.fit(X, y, estimator=verifier.pipeline)
        assert conformal.is_fitted is True

    def test_predict_set_returns_sets(self):
        verifier = ThreeWayVerifier()
        X = np.array([
            [0.9, 0.1, 0.5],
            [0.8, 0.2, 0.6],
            [0.7, 0.3, 0.5],
            [0.2, 0.9, 0.3],
            [0.1, 0.8, 0.4],
            [0.3, 0.7, 0.2],
            [0.6, 0.4, 0.5],
            [0.5, 0.5, 0.5],
            [0.95, 0.05, 0.5],
            [0.15, 0.85, 0.3],
        ])
        y = np.array(["SUPPORTED", "SUPPORTED", "SUPPORTED", "INSUFFICIENT", "INSUFFICIENT", "INSUFFICIENT", "SUPPORTED", "INSUFFICIENT", "SUPPORTED", "INSUFFICIENT"])
        verifier.train(X, y)
        
        conformal = ConformalPredictor(alpha=0.10, method="LAC")
        conformal.fit(X, y, estimator=verifier.pipeline)
        
        X_test = np.array([[0.9, 0.1, 0.5], [0.2, 0.9, 0.3]])
        sets = conformal.predict_set(X_test)
        assert len(sets) == 2
        assert all(len(s) >= 1 for s in sets)

    def test_predict_quantile(self):
        verifier = ThreeWayVerifier()
        X = np.array([
            [0.9, 0.1, 0.5],
            [0.8, 0.2, 0.6],
            [0.7, 0.3, 0.5],
            [0.2, 0.9, 0.3],
            [0.1, 0.8, 0.4],
            [0.3, 0.7, 0.2],
        ])
        y = np.array(["SUPPORTED", "SUPPORTED", "SUPPORTED", "INSUFFICIENT", "INSUFFICIENT", "INSUFFICIENT"])
        verifier.train(X, y)
        
        conformal = ConformalPredictor(alpha=0.10, method="LAC")
        conformal.fit(X, y, estimator=verifier.pipeline)
        
        quantile = conformal.predict_quantile()
        assert 0.0 <= quantile <= 1.0

    def test_predict_set_without_fit_raises(self):
        conformal = ConformalPredictor(alpha=0.10, method="LAC")
        with pytest.raises(RuntimeError):
            conformal.predict_set(np.array([[0.5, 0.5, 0.5]]))


class TestQueryHandlersBayesianFusion:
    """T007: Assert the live claim-verification path calls compute_support_probability()."""

    def test_compute_support_probability_delegates_to_bayesian_fusion(self):
        from unittest.mock import patch, MagicMock
        from server.modules.query_handlers import _compute_support_probability
        from server.schemas import VerifierResult, Verdict

        mock_verifier_outputs = [
            VerifierResult(
                claim_id=uuid.uuid4(),
                predicted_label=Verdict.SUPPORTED,
                probabilities={"SUPPORTED": 0.9, "REFUTED": 0.05, "INSUFFICIENT": 0.05},
                calibrated=True,
                conformal_set=[Verdict.SUPPORTED],
                coverage_target=0.90,
                calibration_id="calibration-v1",
            ),
            VerifierResult(
                claim_id=uuid.uuid4(),
                predicted_label=Verdict.SUPPORTED,
                probabilities={"SUPPORTED": 0.7, "REFUTED": 0.2, "INSUFFICIENT": 0.1},
                calibrated=True,
                conformal_set=[Verdict.SUPPORTED],
                coverage_target=0.90,
                calibration_id="calibration-v1",
            ),
        ]

        with patch("server.modules.query_handlers.compute_support_probability") as mock_bayesian:
            mock_bayesian.return_value = (0.85, False)
            result = _compute_support_probability(mock_verifier_outputs)
            mock_bayesian.assert_called_once()
            call_args = mock_bayesian.call_args[0][0]
            assert len(call_args) == 2
            assert call_args[0] == (0.9, 1.0)
            assert call_args[1] == (0.7, 1.0)
            assert result == 0.85


class TestQueryHandlersConformalWiring:
    """T008: Assert ConformalPredictor.predict_set_from_probs() is called at runtime."""

    def test_predict_set_from_probs_called_at_runtime(self):
        from unittest.mock import MagicMock, patch
        from server.modules.query_handlers import run_uq_pipeline
        from server.schemas import (
            Verdict, EvidencePacket, Passage, SafetyResult, SafetyScope,
            VerifierResult, ExtendedQuestionResponse, RunArtifact,
        )
        import uuid

        # Build a minimal conformal predictor mock
        mock_conformal = MagicMock()
        mock_conformal.is_fitted = True
        mock_conformal.predict_set_from_probs.return_value = [Verdict.SUPPORTED]

        # Build a minimal verifier result
        mock_verifier_result = VerifierResult(
            claim_id=uuid.uuid4(),
            predicted_label=Verdict.SUPPORTED,
            probabilities={"SUPPORTED": 0.9, "REFUTED": 0.05, "INSUFFICIENT": 0.05},
            calibrated=True,
            conformal_set=[Verdict.SUPPORTED],
            coverage_target=0.90,
            calibration_id="calibration-v1",
        )

        # Build a minimal evidence packet
        mock_passage = MagicMock(spec=Passage)
        mock_passage.text = "test evidence"
        mock_evidence_packet = MagicMock(spec=EvidencePacket)
        mock_evidence_packet.passages = [mock_passage]
        mock_evidence_packet.corpus_id = "test-corpus"
        mock_evidence_packet.corpus_hash = "abc123"

        # Mock claim
        mock_claim = MagicMock()
        mock_claim.claim_id = uuid.uuid4()
        mock_claim.text = "test claim"

        with patch.dict("server.modules.query_handlers.__dict__", {
            "_conformal_predictor": mock_conformal,
            "_claim_composer": MagicMock(),
            "_verifier": MagicMock(),
            "_answer_composer": MagicMock(),
            "_calibration_artifact": None,
            "_embedding_model": None,
        }):
            # Patch dependencies
            with patch("server.modules.query_handlers.classify_scope") as mock_classify, \
                 patch("server.modules.query_handlers.compute_simple_features") as mock_simple, \
                 patch("server.modules.query_handlers.compute_feature_vector") as mock_feature, \
                 patch("server.modules.query_handlers.build_run_artifact") as mock_artifact, \
                 patch("server.modules.query_handlers.build_doubt_certificate") as mock_doubt:
                
                mock_classify.return_value = SafetyResult(scope=SafetyScope.ALLOWED, reason="")
                mock_simple.return_value = MagicMock()
                mock_feature.return_value = MagicMock()
                mock_artifact.return_value = MagicMock(spec=RunArtifact, run_id=uuid.uuid4())
                mock_doubt.return_value = MagicMock()

                # Set up claim composer and verifier mocks
                import server.modules.query_handlers as qh
                qh._claim_composer.decompose.return_value = [mock_claim]
                qh._verifier.predict_text.return_value = mock_verifier_result
                qh._answer_composer.compose_with_sources.return_value = ("answer text", ["source1"])

                response, artifact = run_uq_pipeline(
                    question="test question",
                    evidence_packet=mock_evidence_packet,
                )

                mock_conformal.predict_set_from_probs.assert_called_once()
                call_args = mock_conformal.predict_set_from_probs.call_args[0][0]
                assert "SUPPORTED" in call_args
