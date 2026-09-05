"""
Cited answer composer for singleton {SUPPORTED} path.
"""

import json
import os
from pathlib import Path
from typing import Optional
from server.schemas import Claim, EvidencePacket, ClaimRecord, PerturbationType, PipelineMode


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


class ClaimExporter:
    """Exports per-claim records to JSONL for offline abstention analysis."""

    def __init__(self, output_dir: str = "data/runs"):
        self.output_path = Path(output_dir) / "claims.jsonl"
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        claims: list[Claim],
        question_id: str,
        run_artifact_id: str,
        perturbation_type: PerturbationType = PerturbationType.CLEAN,
        pipeline_mode: PipelineMode = PipelineMode.FULL,
        correctness_labels: Optional[dict[str, bool]] = None,
    ) -> None:
        """Write one JSON line per claim to the output JSONL file.

        Args:
            claims: List of Claim objects from the pipeline.
            question_id: Identifier for the question being processed.
            run_artifact_id: UUID linking to the full run artifact.
            perturbation_type: Whether the question was clean or adversarially perturbed.
            pipeline_mode: Whether the full pipeline or abstention-suppressed mode was used.
            correctness_labels: Optional mapping of claim_id -> is_correct for offline annotation.
        """
        correctness_labels = correctness_labels or {}
        records = []
        for claim in claims:
            if claim.verifier_output is None:
                continue
            support_probability = claim.verifier_output.probabilities.get("SUPPORTED", 0.0)
            conformal_set = [v.name for v in claim.verifier_output.conformal_set]
            is_correct = correctness_labels.get(str(claim.claim_id), False)
            record = ClaimRecord(
                claim_id=str(claim.claim_id),
                question_id=question_id,
                support_probability=support_probability,
                conformal_set=conformal_set,
                is_correct=is_correct,
                perturbation_type=perturbation_type,
                pipeline_mode=pipeline_mode,
                run_artifact_id=run_artifact_id,
            )
            records.append(record.model_dump(mode="json"))

        with open(self.output_path, "a") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")


