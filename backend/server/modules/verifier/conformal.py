"""
Split conformal prediction using MAPIE.

Converts calibrated probabilities into prediction sets with coverage guarantees.
"""

from typing import Optional
import numpy as np
from mapie.classification import SplitConformalClassifier

from server.schemas import Verdict


class ConformalPredictor:
    """
    Split conformal classifier for three-way verifier.

    For C0: LAC score function, 90% coverage.
    For A0: APS score function for smaller prediction sets.
    """

    def __init__(self, alpha: float = 0.10, method: str = "LAC"):
        self.alpha = alpha
        self.method = method
        self.predictor: Optional[SplitConformalClassifier] = None
        self.is_fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray, estimator=None):
        """
        Fit conformal predictor on calibration set.

        Args:
            X: (n_calib, n_features) calibration features
            y: (n_calib,) calibration labels
            estimator: pre-fitted classifier (from training set)
        """
        confidence_level = 1.0 - self.alpha
        self.predictor = SplitConformalClassifier(
            estimator=estimator,
            confidence_level=confidence_level,
            conformity_score=self.method.lower(),
            prefit=True,
        )
        self.predictor.conformalize(X, y)
        self.is_fitted = True

    def predict_set(self, X: np.ndarray) -> list[list[Verdict]]:
        """
        Return prediction sets for input features.

        Returns list of prediction sets, one per sample.
        """
        if not self.is_fitted:
            raise RuntimeError("Conformal predictor must be fitted before prediction")

        _, coverage_mask = self.predictor.predict_set(X)
        estimator = self.predictor._estimator
        classes = estimator.classes_

        verdict_sets = []
        for i in range(len(X)):
            mask = coverage_mask[i].flatten()
            class_indices = np.where(mask)[0]
            verdict_set = [Verdict(str(classes[idx])) for idx in class_indices]
            if not verdict_set:
                verdict_set = [Verdict.INSUFFICIENT]
            verdict_sets.append(verdict_set)

        return verdict_sets

    def predict_quantile(self) -> float:
        """Return the conformal quantile for this alpha level."""
        if not self.is_fitted:
            raise RuntimeError("Conformal predictor must be fitted")
        scores = self.predictor.conformity_scores
        quantile = float(np.quantile(scores, 1.0 - self.alpha))
        return quantile


