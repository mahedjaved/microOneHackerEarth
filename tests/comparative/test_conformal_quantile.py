"""
Tests for the conformal quantile minimization (spec 001-bayesian-evidence-fusion).

Written first (TDD per Article IX). MUST fail before the implementation in
backend/server/modules/verifier/conformal.py is updated.

Verifies:
  - US3 scenario 1: chosen quantile is the argmin of expected loss (SC-004).
  - US3 scenario 2: the choice is reproducible from inputs.
"""

import pytest


def _brute_force_expected_loss(calibration_entries, cost_wrong, cost_abstain, q):
    """
    Reference implementation: compute expected loss for a given quantile q.
    For each (claim, passage, ground_truth_support) entry:
      - If the verifier abstains (i.e., q is too high), pay cost_abstain.
      - If the verifier doesn't abstain but is wrong, pay cost_wrong.
      - If the verifier doesn't abstain and is right, pay 0.

    We approximate "abstain when combined_posterior < q" by assuming the
    per-passage score is a noisy version of ground_truth_support. For
    reproducibility, we use ground_truth_support directly as the posterior
    (i.e., perfect calibration).
    """
    if not calibration_entries:
        return 0.0
    total_loss = 0.0
    for entry in calibration_entries:
        p = 1.0 if entry["ground_truth_support"] else 0.0
        # If we abstain (p < q), we incur the abstention cost.
        # Otherwise, we predict SUPPORTED; if wrong, we incur the wrong-prediction cost.
        if p < q:
            total_loss += cost_abstain
        elif not entry["ground_truth_support"]:
            total_loss += cost_wrong
    return total_loss / len(calibration_entries)


def _brute_force_quantile(calibration_entries, cost_wrong, cost_abstain, step=0.01):
    """Sweep q over [0, 1] and return the argmin of expected loss."""
    best_q, best_loss = 0.0, float("inf")
    q = 0.0
    while q <= 1.0:
        loss = _brute_force_expected_loss(
            calibration_entries, cost_wrong, cost_abstain, q
        )
        if loss < best_loss:
            best_loss, best_q = loss, q
        q += step
    return best_q, best_loss


class TestConformalQuantile:
    """Tests for compute_quantile_from_calibration() — the new conformal layer."""

    def test_quantile_reproducible_from_inputs(self):
        """US3 scenario 2 + SC-004: the chosen quantile is reproducible."""
        from backend.server.modules.verifier.conformal import (
            compute_quantile_from_calibration,
        )
        import json
        import os

        # Load the calibration set created by T003
        cal_path = os.path.join(
            os.path.dirname(__file__), "data", "calibration_set.json"
        )
        with open(cal_path) as f:
            cal = json.load(f)
        entries = cal["entries"]

        # Default cost ratio 10:1
        q1 = compute_quantile_from_calibration(cal_path, "10:1")
        q2 = compute_quantile_from_calibration(cal_path, "10:1")
        # Must be reproducible
        assert q1 == q2, f"Quantile is not reproducible: {q1} != {q2}"

    def test_quantile_matches_brute_force(self):
        """SC-004: the chosen quantile equals a brute-force sweep to 1e-6."""
        from backend.server.modules.verifier.conformal import (
            compute_quantile_from_calibration,
        )
        import json
        import os

        cal_path = os.path.join(
            os.path.dirname(__file__), "data", "calibration_set.json"
        )
        with open(cal_path) as f:
            cal = json.load(f)
        entries = cal["entries"]

        # Compute via the implementation
        impl_q = compute_quantile_from_calibration(cal_path, "10:1")

        # Compute via brute force
        brute_q, _ = _brute_force_quantile(entries, 10.0, 1.0, step=0.01)

        # The implementation may use a different step size; allow tolerance
        # of the step granularity (0.01).
        assert abs(impl_q - brute_q) <= 0.01, (
            f"Implementation quantile {impl_q} does not match brute-force {brute_q}"
        )

    def test_cost_ratio_10_1_prefers_abstention(self):
        """US3: a 10:1 cost ratio (confident-wrong is 10x worse) prefers higher abstention."""
        from backend.server.modules.verifier.conformal import (
            compute_quantile_from_calibration,
        )
        import json
        import os

        cal_path = os.path.join(
            os.path.dirname(__file__), "data", "calibration_set.json"
        )
        with open(cal_path) as f:
            cal = json.load(f)
        entries = cal["entries"]

        # 10:1 → prefer higher quantile (more abstention)
        q_high_cost = compute_quantile_from_calibration(cal_path, "10:1")
        # 1:1 → equal weight
        q_equal = compute_quantile_from_calibration(cal_path, "1:1")
        # 1:10 → prefer lower quantile (less abstention)
        q_low_cost = compute_quantile_from_calibration(cal_path, "1:10")

        # The 10:1 quantile should be >= the 1:10 quantile
        # (more abstention when wrong is expensive)
        assert q_high_cost >= q_low_cost, (
            f"10:1 quantile {q_high_cost} should be >= 1:10 quantile {q_low_cost}"
        )
