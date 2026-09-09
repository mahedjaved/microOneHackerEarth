"""
EAV (Evidence Acquisition Value) controller.

Deterministic policy that decides whether one bounded action
(clarify or retrieve) is likely to collapse an ambiguous conformal set.
"""

import uuid
from typing import Literal
from server.schemas import Verdict, EAVAction, EAVActionType, EvidenceFeatureVector


class EAVController:
    """
    Evidence Acquisition Value controller.

    For C0: deterministic policy based on feature vector heuristics.
    For A0: learned policy if labeled EAV data is available.
    """

    def __init__(self, action_budget: int = 1):
        self.action_budget = action_budget
        self.actions_used = 0

    def decide(self, feature_vector: EvidenceFeatureVector, conformal_set: list[Verdict]) -> EAVActionType | None:
        """
        Decide whether to take an action and which type.

        Returns EAVActionType.CLARIFY, EAVActionType.RETRIEVE, or None.
        """
        if self.actions_used >= self.action_budget:
            return None

        if len(conformal_set) == 1:
            return None  # Singleton - no action needed

        # Priority 1: Clarify for query ambiguity
        qa = feature_vector.query_ambiguity
        if qa.missing_entities or qa.underspecified_scope:
            return EAVActionType.CLARIFY

        # Priority 2: Retrieve for insufficient evidence or retrieval issues
        rq = feature_vector.retrieval_quality
        if rq.top_score < 0.5 or feature_vector.claim_coverage < 0.3:
            return EAVActionType.RETRIEVE

        # Priority 3: Retrieve for conflict
        if feature_vector.conflict.support_refute_coexist:
            return EAVActionType.RETRIEVE

        # Default: no action if uncertainty is not reducible
        return None

    def record_action(self, action_type: EAVActionType, pre_set: list[Verdict], post_set: list[Verdict] | None = None) -> EAVAction:
        """Record an EAV action."""
        self.actions_used += 1
        productive = False
        if post_set:
            productive = len(post_set) == 1 or post_set == [Verdict.INSUFFICIENT]

        return EAVAction(
            action_id=uuid.uuid4(),
            action_type=action_type,
            description=f"EAV action: {action_type.value}",
            pre_conformal_set=pre_set,
            post_conformal_set=post_set,
            productive=productive,
        )

    def reset(self):
        """Reset action budget for new execution."""
        self.actions_used = 0

