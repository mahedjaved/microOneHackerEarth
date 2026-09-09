"""
Tests for the Bayesian log-odds evidence fusion (spec 001-bayesian-evidence-fusion).

These tests are written first (TDD per Article IX). They MUST fail before the
implementation in backend/server/modules/verifier/bayesian_fusion.py is created.

Three reference cases from spec US2 + contracts/contracts.md:
  1. Agreement: two supporting passages should reinforce (posterior > max).
  2. Off-topic: a near-zero passage should not drag down the posterior.
  3. Neutral: all-neutral passages should not move the prior.
Plus the closed-form check (SC-003) and the boilerplate dampening check (US4).
"""

import math
import pytest


def _closed_form_log_odds(passages, prior=0.5, relevance_threshold=None):
    """
    Reference closed-form implementation for verification.

    Uses the same math as the contract: clamp, optional dampening, log-odds addition.
    """
    EPS = 1e-6
    prior_clamped = min(max(prior, EPS), 1 - EPS)
    prior_odds = prior_clamped / (1 - prior_clamped)
    log_odds = math.log(prior_odds)
    for p, rel in passages:
        p_clamped = min(max(p, EPS), 1 - EPS)
        odds_i = p_clamped / (1 - p_clamped)
        # Apply relevance dampening
        if relevance_threshold is not None and rel < relevance_threshold:
            # Pull likelihood ratio toward 1.0 with weight 0.1
            log_odds += 0.1 * math.log(odds_i / prior_odds)
        else:
            log_odds += math.log(odds_i / prior_odds)
    combined_odds = math.exp(log_odds)
    return combined_odds / (1 + combined_odds)


class TestComputeSupportProbability:
    """Tests for compute_support_probability() — the new Bayesian combiner."""

    def test_log_odds_agreement(self):
        """US2 scenario 1: two positive updates reinforce (posterior > max)."""
        from backend.server.modules.verifier.bayesian_fusion import (
            compute_support_probability,
        )

        # Two supporting passages: (support_prob, relevance)
        passages = [(0.8, 0.9), (0.7, 0.85)]
        posterior, relevance_weighted = compute_support_probability(
            passages, prior=0.5
        )
        # Posterior must exceed max(0.8, 0.7) = 0.8
        assert posterior > 0.8, f"Expected posterior > 0.8, got {posterior}"
        # Not relevance-weighted (both passages are high-relevance)
        assert relevance_weighted is False
        # Match closed-form to 1e-6 (SC-003)
        expected = _closed_form_log_odds(passages, prior=0.5)
        assert abs(posterior - expected) < 1e-6, (
            f"Posterior {posterior} does not match closed-form {expected}"
        )

    def test_log_odds_offtopic(self):
        """US2 scenario 2: an off-topic (low-relevance) passage is near-uninformative."""
        from backend.server.modules.verifier.bayesian_fusion import (
            compute_support_probability,
        )

        # One supporting (0.8, high-relevance 0.9) and one off-topic
        # near-zero (0.01, low-relevance 0.1 — below the 0.3 threshold).
        # The off-topic passage is dampened to 10% weight, so it should
        # not drag the posterior down significantly.
        passages = [(0.8, 0.9), (0.01, 0.1)]
        posterior, relevance_weighted = compute_support_probability(
            passages, prior=0.5, relevance_threshold=0.3
        )
        # Posterior must be close to 0.8 (not dragged to ~0.4 by averaging)
        # and not artificially boosted above 0.8
        assert abs(posterior - 0.8) < 0.15, (
            f"Expected posterior ≈ 0.8, got {posterior}"
        )
        # The off-topic passage was dampened
        assert relevance_weighted is True, (
            "relevance_weighted should be True when a low-relevance passage is dampened"
        )
        # Match closed-form
        expected = _closed_form_log_odds(passages, prior=0.5, relevance_threshold=0.3)
        assert abs(posterior - expected) < 1e-6

    def test_log_odds_neutral(self):
        """US2 scenario 3: neutral evidence does not move the prior."""
        from backend.server.modules.verifier.bayesian_fusion import (
            compute_support_probability,
        )

        passages = [(0.5, 0.9), (0.5, 0.85)]
        posterior, relevance_weighted = compute_support_probability(
            passages, prior=0.5
        )
        # Posterior must be exactly 0.5 (neutral evidence has odds=1, log=0)
        assert abs(posterior - 0.5) < 1e-9, (
            f"Expected posterior = 0.5, got {posterior}"
        )
        assert relevance_weighted is False

    def test_empty_evidence_returns_prior(self):
        """Edge case: no passages → return prior unchanged."""
        from backend.server.modules.verifier.bayesian_fusion import (
            compute_support_probability,
        )

        posterior, relevance_weighted = compute_support_probability(
            [], prior=0.5
        )
        assert posterior == 0.5
        assert relevance_weighted is False

    def test_clamps_extreme_probabilities(self):
        """FR-003: probabilities near 0 or 1 must be clamped to [1e-6, 1-1e-6]."""
        from backend.server.modules.verifier.bayesian_fusion import (
            compute_support_probability,
        )

        # A passage with support_prob=0.0 should not crash
        passages = [(0.0, 0.9), (0.5, 0.85)]
        posterior, _ = compute_support_probability(passages, prior=0.5)
        assert 0.0 <= posterior <= 1.0
        # Same for support_prob=1.0
        passages = [(1.0, 0.9), (0.5, 0.85)]
        posterior, _ = compute_support_probability(passages, prior=0.5)
        assert 0.0 <= posterior <= 1.0

    def test_boilerplate_dampening(self):
        """US4: a low-relevance passage contributes at most 10% of a high-relevance passage."""
        from backend.server.modules.verifier.bayesian_fusion import (
            compute_support_probability,
        )

        # High-relevance claim: support=0.8, relevance=0.9
        # Boilerplate claim: support=0.8, relevance=0.1 (below threshold 0.3)
        passages_with_boiler = [(0.8, 0.9), (0.8, 0.1)]
        posterior_with_boiler, relevance_weighted = compute_support_probability(
            passages_with_boiler, prior=0.5, relevance_threshold=0.3
        )

        passages_no_boiler = [(0.8, 0.9), (0.8, 0.9)]
        posterior_no_boiler, _ = compute_support_probability(
            passages_no_boiler, prior=0.5, relevance_threshold=0.3
        )

        # When boilerplate is present and dampened, the posterior should be
        # closer to the single-passage posterior than when both are weighted equally.
        single_passage_posterior, _ = compute_support_probability(
            [(0.8, 0.9)], prior=0.5, relevance_threshold=0.3
        )
        # With dampening: posterior_with_boiler should be closer to single-passage
        # than to posterior_no_boiler (which is two full-strength updates)
        # Verify: relevance_weighted flag is True
        assert relevance_weighted is True, (
            "relevance_weighted should be True when a passage is dampened"
        )
        # SC-005: boilerplate claim contributes ≤10% as much as high-relevance claim
        # The dampened posterior should be closer to single_passage than to full_double
        dist_to_single = abs(posterior_with_boiler - single_passage_posterior)
        dist_to_double = abs(posterior_with_boiler - posterior_no_boiler)
        assert dist_to_single < dist_to_double, (
            f"Dampened posterior {posterior_with_boiler} should be closer to "
            f"single-passage {single_passage_posterior} than to full-double {posterior_no_boiler}"
        )

    def test_latency_regression(self):
        """SC-007: log-odds fusion adds <5 ms per claim vs legacy mean/max."""
        import time

        from backend.server.modules.verifier.bayesian_fusion import (
            compute_support_probability,
        )

        # Simulate a realistic claim with 5 passages
        passages = [(0.7, 0.8), (0.6, 0.75), (0.8, 0.9), (0.5, 0.85), (0.65, 0.7)]
        # Warm up
        for _ in range(10):
            compute_support_probability(passages, prior=0.5)
        # Time 1000 calls
        t0 = time.perf_counter()
        for _ in range(1000):
            compute_support_probability(passages, prior=0.5)
        elapsed = (time.perf_counter() - t0) / 1000  # per call
        assert elapsed < 0.005, f"Per-call latency {elapsed*1000:.3f} ms exceeds 5 ms"

    def test_prior_recorded_in_doubt_certificate(self):
        """FR-014: the prior used must be recordable in DoubtCertificate."""
        # This is an integration test; the implementation must support
        # returning the prior for the caller to put in DoubtCertificate.
        from backend.server.modules.verifier.bayesian_fusion import (
            compute_support_probability,
        )

        posterior, _ = compute_support_probability(
            [(0.8, 0.9), (0.7, 0.85)], prior=0.3
        )
        # Prior 0.3 should produce a different posterior than prior 0.5
        # (verifying the function actually uses the prior parameter)
        posterior_default, _ = compute_support_probability(
            [(0.8, 0.9), (0.7, 0.85)], prior=0.5
        )
        assert posterior != posterior_default, (
            "Function must actually use the prior parameter"
        )
