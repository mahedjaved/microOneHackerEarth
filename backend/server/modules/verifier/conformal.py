"""
Split conformal prediction using MAPIE.

Converts calibrated probabilities into prediction sets with coverage guarantees.
"""

import os
import sys
from typing import Optional
import numpy as np
from mapie.classification import SplitConformalClassifier

# Make the server package importable when this module is used in isolation
# (e.g., from tests/comparative/ without the backend on sys.path).
_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

try:
    from server.schemas import Verdict
except ImportError:
    # Verdict is only needed by the ConformalPredictor class; the
    # expected-loss quantile functions below don't depend on it.
    Verdict = None  # type: ignore


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
        self._quantile: Optional[float] = None

    @classmethod
    def from_quantile(cls, quantile: float, alpha: float = 0.10, method: str = "LAC") -> "ConformalPredictor":
        """
        Create a ConformalPredictor from a saved quantile value.

        This allows the predictor to be used for inference without re-fitting
        on calibration data. The quantile is computed during training and saved
        to conformal_quantile.json.
        """
        obj = cls(alpha=alpha, method=method)
        obj._quantile = quantile
        obj.is_fitted = True
        return obj

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
        self._quantile = float(np.quantile(self.predictor.conformity_scores, 1.0 - self.alpha))

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

    def predict_set_from_probs(self, prob_dict: dict[Verdict, float]) -> list[Verdict]:
        """
        Return prediction set from verifier probabilities using saved quantile.

        Uses the LAC (Least Adaptive to Coverage) score function:
        For each class c, include c in the prediction set if (1 - p(c)) <= quantile.

        Args:
            prob_dict: dict mapping Verdict -> probability (must sum to ~1.0)

        Returns:
            List of Verdict values in the prediction set
        """
        if not self.is_fitted or self._quantile is None:
            raise RuntimeError("Conformal predictor must be initialized with from_quantile() before prediction")

        included = [verdict for verdict, prob in prob_dict.items() if (1.0 - prob) <= self._quantile]

        if not included:
            return [Verdict.INSUFFICIENT]

        return included

    def predict_quantile(self) -> float:
        """Return the conformal quantile for this alpha level."""
        if not self.is_fitted:
            raise RuntimeError("Conformal predictor must be fitted")
        if self._quantile is not None:
            return self._quantile
        scores = self.predictor.conformity_scores
        quantile = float(np.quantile(scores, 1.0 - self.alpha))
        return quantile


# =============================================================================
# Expected-loss-driven quantile selection (spec 001-bayesian-evidence-fusion)
# FR-006, FR-007, FR-013
# =============================================================================


def _parse_cost_ratio(cost_ratio: str) -> tuple[float, float]:
    """Parse a "N:M" cost ratio string into (confident_wrong, over_abstain)."""
    try:
        n, m = cost_ratio.split(":")
        return (float(n), float(m))
    except (ValueError, AttributeError):
        return (10.0, 1.0)


def _expected_loss(
    entries: list[dict],
    cost_wrong: float,
    cost_abstain: float,
    q: float,
) -> float:
    """
    Compute expected loss at a given abstention threshold q.

    For each (claim, passage, ground_truth_support) entry, assume the
    per-passage support probability equals ground_truth_support (perfect
    calibration as a reference). Then:
      - If the verifier abstains (p < q), pay cost_abstain.
      - If the verifier doesn't abstain and the claim is unsupported,
        pay cost_wrong (confident-wrong).
      - If the verifier doesn't abstain and the claim is supported, pay 0.

    Returns the mean loss across entries.
    """
    if not entries:
        return 0.0
    total = 0.0
    for entry in entries:
        p = 1.0 if entry.get("ground_truth_support") else 0.0
        if p < q:
            total += cost_abstain
        elif not entry.get("ground_truth_support"):
            total += cost_wrong
    return total / len(entries)


def compute_quantile_from_calibration(
    calibration_set_path: str,
    cost_ratio: str = "10:1",
    step: float = 0.01,
) -> float:
    """
    Choose the conformal abstention quantile by minimizing expected loss
    on a labeled calibration set under a stated cost ratio.

    Spec: 001-bayesian-evidence-fusion FR-006, SC-004.
    Contract: contracts/contracts.md — reproducible from inputs.

    Args:
        calibration_set_path: Path to a JSON file with shape:
            {"entries": [{"ground_truth_support": bool, ...}, ...]}
        cost_ratio: "N:M" string (confident_wrong : over_abstain).
            Default "10:1" (medical-safety prior).
        step: Quantile sweep granularity. Default 0.01.

    Returns:
        The quantile q in [0, 1] that minimizes expected loss.
    """
    import json

    with open(calibration_set_path) as f:
        cal = json.load(f)
    entries = cal.get("entries", [])

    cost_wrong, cost_abstain = _parse_cost_ratio(cost_ratio)

    best_q = 0.0
    best_loss = float("inf")
    # Sweep q in [0, 1] at the given step granularity
    # Use a stable integer counter to avoid float accumulation
    n_steps = int(round(1.0 / step))
    for i in range(n_steps + 1):
        q = i * step
        if q > 1.0:
            q = 1.0
        loss = _expected_loss(entries, cost_wrong, cost_abstain, q)
        if loss < best_loss:
            best_loss = loss
            best_q = q

    return best_q


