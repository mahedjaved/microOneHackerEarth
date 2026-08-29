"""
Probability calibration for verifier.

Fits probability calibration on held-out calibration set.
"""

import numpy as np
from typing import Optional
from sklearn.isotonic import IsotonicRegression
from joblib import dump, load

from server.schemas import Verdict


class ProbabilityCalibrator:
    """
    Calibrates verifier probabilities using isotonic regression.

    For C0: isotonic regression on validation set.
    For A0: temperature scaling or platt scaling if needed.
    """

    def __init__(self, method: str = "isotonic"):
        self.method = method
        self.calibrators: dict[str, IsotonicRegression] = {}
        self.is_fitted = False

    def fit(self, probabilities: np.ndarray, labels: np.ndarray):
        """
        Fit calibrators for each class.

        Args:
            probabilities: (n_samples, n_classes) raw probabilities
            labels: (n_samples,) integer class labels
        """
        n_classes = probabilities.shape[1]
        for cls_idx in range(n_classes):
            binary_labels = (labels == cls_idx).astype(int)
            cls_probs = probabilities[:, cls_idx]
            calibrator = IsotonicRegression(out_of_bounds="clip")
            calibrator.fit(cls_probs, binary_labels)
            self.calibrators[str(cls_idx)] = calibrator
        self.is_fitted = True

    def transform(self, probabilities: np.ndarray) -> np.ndarray:
        """Calibrate probabilities."""
        if not self.is_fitted:
            raise RuntimeError("Calibrator must be fitted before transform")

        calibrated = np.zeros_like(probabilities)
        for cls_idx in range(probabilities.shape[1]):
            calibrator = self.calibrators.get(str(cls_idx))
            if calibrator:
                calibrated[:, cls_idx] = calibrator.predict(probabilities[:, cls_idx])
            else:
                calibrated[:, cls_idx] = probabilities[:, cls_idx]

        # Renormalize
        row_sums = calibrated.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return calibrated / row_sums

    def save(self, path: str):
        """Save calibrator to disk."""
        dump({"calibrators": self.calibrators, "method": self.method}, path)

    @classmethod
    def load(cls, path: str) -> "ProbabilityCalibrator":
        """Load calibrator from disk."""
        data = load(path)
        instance = cls(method=data["method"])
        instance.calibrators = data["calibrators"]
        instance.is_fitted = True
        return instance

