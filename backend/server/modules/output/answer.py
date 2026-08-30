"""
Cited answer composer for singleton {SUPPORTED} path.
"""

from typing import Optional
from server.schemas import Claim, EvidencePacket


class AnswerComposer:
    """Composes cited answers from supported claims."""

    def compose(self, claims: list[Claim], evidence_packet: EvidencePacket) -> str:
        """
        Compose a cited answer from supported claims.

        For C0: simple text composition with citation IDs.
        For A0: structured answer with claim-level citations.
        """
        supported_claims = [c for c in claims if c.verifier_output and c.verifier_output.predicted_label.name == "SUPPORTED"]

        if not supported_claims:
            return ""

        parts = []
        for claim in supported_claims:
            citation_refs = ", ".join(f"[{cid}]" for cid in claim.citation_ids)
            parts.append(f"{claim.text} {citation_refs}")

        return "\n\n".join(parts)

    def compose_with_sources(self, claims: list[Claim], evidence_packet: EvidencePacket) -> tuple[str, list[str]]:
        """Compose answer and return source list."""
        answer = self.compose(claims, evidence_packet)
        sources = []
        for passage in evidence_packet.passages:
            source = f"{passage.document_id}:{passage.page_location}"
            if source not in sources:
                sources.append(source)
        return answer, sources

