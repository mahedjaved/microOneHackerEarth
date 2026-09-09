"""
Clarification action for EAV controller.

Generates bounded clarification questions for missing entities or ambiguous queries.
"""

from typing import Optional
from server.schemas import EAVAction, EAVActionType, QueryAmbiguity


class ClarificationGenerator:
    """Generates bounded clarification questions."""

    def generate(self, ambiguity: QueryAmbiguity, claim_text: str) -> str | None:
        """
        Generate a clarification question based on detected ambiguity.

        Returns None if no clarification is needed.
        """
        if ambiguity.missing_entities:
            return self._clarify_entities(claim_text)
        if ambiguity.underspecified_scope:
            return self._clarify_scope(claim_text)
        if ambiguity.unresolved_pronouns:
            return self._clarify_pronouns(claim_text)
        return None

    def _clarify_entities(self, claim_text: str) -> str:
        return "Could you specify which medication, condition, or patient population you are asking about?"

    def _clarify_scope(self, claim_text: str) -> str:
        return "Could you clarify what aspect you are interested in? For example, are you asking about efficacy, side effects, or dosage?"

    def _clarify_pronouns(self, claim_text: str) -> str:
        return "Could you clarify what 'it' or 'they' refers to in your question?"

    def build_action(self, question: str, pre_conformal_set: list) -> EAVAction:
        """Build EAV action record for clarification."""
        return EAVAction(
            action_type=EAVActionType.CLARIFY,
            description=f"Clarification requested: {question}",
            pre_conformal_set=pre_conformal_set,
        )

