"""
Atomic claim decomposition from LLM answer.

Decomposes the answer into atomic claims with stable claim IDs and citation references.
"""

import uuid
import re
import json
from typing import List
from pydantic import BaseModel

from server.schemas import Claim, EvidencePacket


class ClaimComposer:
    """Decomposes LLM answers into atomic claims."""

    def __init__(self, llm=None):
        self.llm = llm

    def decompose(self, answer: str, evidence_packet: EvidencePacket) -> List[Claim]:
        """
        Decompose answer into atomic claims.

        For C0: simple sentence-level decomposition with citation matching.
        For A0: LLM-based decomposition with semantic grouping.
        """
        sentences = self._split_sentences(answer)
        claims = []
        for i, sentence in enumerate(sentences):
            if not sentence.strip():
                continue
            citation_ids = self._match_citations(sentence, evidence_packet)
            claim = Claim(
                claim_id=uuid.uuid4(),
                text=sentence.strip(),
                citation_ids=citation_ids,
            )
            claims.append(claim)
        return claims

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _match_citations(self, sentence: str, evidence_packet: EvidencePacket) -> List[str]:
        """
        Match sentence to evidence passages.

        For C0: simple keyword overlap.
        For A0: semantic similarity with embeddings.
        """
        matched = []
        sentence_words = set(sentence.lower().split())
        for passage in evidence_packet.passages:
            passage_words = set(passage.text.lower().split())
            overlap = len(sentence_words & passage_words)
            if overlap > 0:
                matched.append(passage.chunk_id)
        return matched[:3]  # Max 3 citations per claim

