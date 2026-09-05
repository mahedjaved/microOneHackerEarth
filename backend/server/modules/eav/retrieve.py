"""
Targeted retrieval action for EAV controller.

Performs adjacent-page expansion or refined query when retrieval is insufficient.
"""

from typing import Optional
from server.schemas import EAVAction, EAVActionType


class TargetedRetriever:
    """Performs targeted retrieval or adjacent-page expansion."""

    def __init__(self, retriever_fn=None):
        self.retriever_fn = retriever_fn

    def retrieve(self, query: str, top_k: int = 5, adjacent_pages: bool = False) -> list[dict]:
        """
        Perform targeted retrieval.

        For C0: simple expanded query with higher top_k.
        For A0: adjacent-page expansion if document structure is available.
        """
        if self.retriever_fn:
            results = self.retriever_fn(query, top_k=top_k)
        else:
            results = []

        if adjacent_pages:
            results.extend(self._adjacent_page_expand(query, results))

        return results

    def _adjacent_page_expand(self, query: str, existing_results: list[dict]) -> list[dict]:
        """Expand retrieval to adjacent pages of top results."""
        # Placeholder: would need document structure metadata
        return []

    def build_action(self, query: str, pre_conformal_set: list, results: list[dict]) -> EAVAction:
        """Build EAV action record for retrieval."""
        return EAVAction(
            action_type=EAVActionType.RETRIEVE,
            description=f"Targeted retrieval for: {query}",
            pre_conformal_set=pre_conformal_set,
        )

