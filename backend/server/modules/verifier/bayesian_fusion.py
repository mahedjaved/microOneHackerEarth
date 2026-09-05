"""
Bayesian log-odds evidence fusion for UQ-RAG.

Spec: 001-bayesian-evidence-fusion (FR-001, FR-002, FR-003, FR-008)

Replaces the legacy mean()/max() combination of per-passage SUPPORTED
probabilities with naive-Bayes log-odds addition over a stated prior.

Each per-passage probability is treated as an independent likelihood-ratio
update to a shared prior. This is the mathematically correct treatment when
evidence pieces are independent conditional on the claim being true.

Properties (from contracts/contracts.md):
  - Probability clamping to [1e-6, 1-1e-6] before log-odds (FR-003).
  - Empty evidence -> return prior unchanged.
  - Optional relevance dampening: passages with cosine similarity to the
    question below `relevance_threshold` are down-weighted (FR-008).
  - Returns (posterior, relevance_weighted) for the caller to record in
    DoubtCertificate (FR-012, FR-014).
"""

from __future__ import annotations

import math
from typing import Iterable

# Numerical-stability epsilon (FR-003). Probabilities are clamped to
# [EPS, 1 - EPS] before any log-odds computation.
EPS: float = 1e-6

# Default dampening weight for low-relevance passages (FR-008). A passage
# with relevance_to_question < relevance_threshold contributes only
# DAMPENING_WEIGHT of its full likelihood ratio.
DAMPENING_WEIGHT: float = 0.1

# Default relevance threshold (FR-008). Passages with cosine similarity
# below this value are considered "off-topic" and are dampened.
DEFAULT_RELEVANCE_THRESHOLD: float = 0.3

# Default prior (FR-014). Conservative: "no prior reason to believe or
# disbelieve." Configurable via settings.UQ_PRIOR.
DEFAULT_PRIOR: float = 0.5


def _clamp(p: float, lo: float = EPS, hi: float = 1.0 - EPS) -> float:
    """Clamp p into [lo, hi]. Used for numerical stability in log-odds."""
    if p < lo:
        return lo
    if p > hi:
        return hi
    return p


def _log_odds(p: float) -> float:
    """Convert a probability to log-odds, with EPS clamping."""
    p = _clamp(p)
    return math.log(p / (1.0 - p))


def compute_support_probability(
    passages: Iterable[tuple[float, float]],
    prior: float = DEFAULT_PRIOR,
    relevance_threshold: float = DEFAULT_RELEVANCE_THRESHOLD,
    dampening_weight: float = DAMPENING_WEIGHT,
) -> tuple[float, bool]:
    """
    Combine per-passage SUPPORTED probabilities into a single posterior
    via naive-Bayes log-odds addition over a stated prior.

    Args:
        passages: Iterable of (support_prob, relevance_to_question) pairs.
            - support_prob: per-passage SUPPORTED probability in [0, 1].
            - relevance_to_question: cosine similarity to the question,
                in [0, 1].
        prior: Probability of SUPPORTED before observing evidence. Default
            0.5 (no prior bias). Clamped to [EPS, 1-EPS] before log-odds.
        relevance_threshold: Passages with relevance_to_question below this
            value have their likelihood ratio pulled toward 1.0 with weight
            `dampening_weight` (FR-008). Default 0.3.
        dampening_weight: Weight applied to a low-relevance passage's
            likelihood ratio. 0.1 = "contributes at most 10% of full
            evidence." Default 0.1.

    Returns:
        (posterior, relevance_weighted):
            posterior: Combined support probability in [0, 1].
            relevance_weighted: True if any passage was relevance-dampened.

    Contract (contracts/contracts.md):
        - Three reference cases: agreement > max, offtopic ≈ informative,
          neutral = prior.
        - Clamps probabilities to [EPS, 1-EPS] before log-odds.
        - Empty passages -> (prior, False).
        - Bounded output: posterior in [0, 1].
    """
    # Clamp the prior (FR-014 + numerical stability)
    prior = _clamp(prior)
    prior_log_odds = _log_odds(prior)

    log_odds = prior_log_odds  # start at the prior (then re-add the prior's
    # contribution once per passage, so neutral evidence cancels to 0)

    relevance_weighted = False
    passage_count = 0
    for support_prob, relevance in passages:
        passage_count += 1
        # Clamp the per-passage probability (FR-003)
        p = _clamp(support_prob)
        passage_log_odds = _log_odds(p)
        # Likelihood-ratio contribution: log(p / prior)
        lr_contribution = passage_log_odds - prior_log_odds

        if relevance < relevance_threshold:
            # Dampen the contribution (FR-008)
            lr_contribution *= dampening_weight
            relevance_weighted = True

        log_odds += lr_contribution

    if passage_count == 0:
        # Empty evidence: return prior unchanged (edge case)
        return (prior, False)

    # Convert back to probability
    combined_odds = math.exp(log_odds)
    posterior = combined_odds / (1.0 + combined_odds)

    # Clamp the final posterior to [0, 1] for safety
    if posterior < 0.0:
        posterior = 0.0
    elif posterior > 1.0:
        posterior = 1.0

    return (posterior, relevance_weighted)
