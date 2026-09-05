"""Tests for CURA-Med verifier modules."""

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
