"""
Evidence feature vector computation.

Computes 8-block evidence feature vector for each claim-passage pair:
1. Local entailment (max/mean support, contradiction, neutral)
2. Claim coverage (fraction of material clauses with supporting passage)
3. Retrieval quality (top score, score margin, rank dispersion, dense/lexical agreement)
4. Conflict (max contradiction, support/refute coexist)
5. Provenance (document version valid, page resolvable, citation-text match)
6. Query ambiguity (missing entities, unresolved pronouns, underspecified scope)
7. System state (corpus ID, model version, verifier version, calibration age, drift)
8. Optional: grey-box log-probabilities, white-box Feature-Gap directions
"""

import uuid
from typing import Optional
from server.schemas import (
    EvidenceFeatureVector,
    LocalEntailment,
    RetrievalQuality,
    Conflict,
    Provenance,
    QueryAmbiguity,
    SystemState,
    EvidencePacket,
    Claim,
)


def compute_feature_vector(
    claim: Claim,
    evidence_packet: EvidencePacket,
    model_version: str = "",
    verifier_version: str = "",
    calibration_id: str = "",
    calibration_age_days: int = 0,
) -> EvidenceFeatureVector:
    """
    Compute evidence feature vector for a claim against retrieved evidence.

    For C0: deterministic heuristics.
    For A0: add embedding-based entailment and Feature-Gap signals.
    """
    passages = evidence_packet.passages
    citation_texts = [p.text for p in passages if p.chunk_id in claim.citation_ids]

    # Block 1: Local entailment
    local_entailment = _compute_local_entailment(claim.text, citation_texts)

    # Block 2: Claim coverage
    claim_coverage = _compute_claim_coverage(claim.text, citation_texts)

    # Block 3: Retrieval quality
    retrieval_quality = _compute_retrieval_quality(evidence_packet)

    # Block 4: Conflict
    conflict = _compute_conflict(claim.text, citation_texts)

    # Block 5: Provenance
    provenance = _compute_provenance(evidence_packet)

    # Block 6: Query ambiguity
    query_ambiguity = _compute_query_ambiguity(claim.text)

    # Block 7: System state
    system_state = SystemState(
        corpus_id=evidence_packet.corpus_id,
        model_version=model_version,
        verifier_version=verifier_version,
        calibration_age_days=calibration_age_days,
        drift_detected=calibration_age_days > 90,
    )

    return EvidenceFeatureVector(
        claim_id=claim.claim_id,
        local_entailment=local_entailment,
        claim_coverage=claim_coverage,
        retrieval_quality=retrieval_quality,
        conflict=conflict,
        provenance=provenance,
        query_ambiguity=query_ambiguity,
        system_state=system_state,
    )


def compute_simple_features(
    claim_text: str,
    evidence_text: str,
    embedding_model,
) -> "np.ndarray":
    """
    Compute 3-dim features for verifier (C0 prototype).

    Features: cosine_sim, l2_dist, word_overlap
    """
    import numpy as np

    claim_emb = embedding_model.encode(claim_text, show_progress_bar=False)
    evidence_emb = embedding_model.encode(evidence_text, show_progress_bar=False)

    cosine_sim = float(np.dot(claim_emb, evidence_emb) / (np.linalg.norm(claim_emb) * np.linalg.norm(evidence_emb)))
    l2_dist = float(np.linalg.norm(claim_emb - evidence_emb))

    claim_words = set(claim_text.lower().split())
    evidence_words = set(evidence_text.lower().split())
    overlap = len(claim_words & evidence_words)
    total = len(claim_words) + len(evidence_words)
    word_overlap = overlap / total if total > 0 else 0.0

    return np.array([cosine_sim, l2_dist, word_overlap], dtype=np.float64)


def _compute_local_entailment(claim_text: str, passage_texts: list[str]) -> LocalEntailment:
    """Compute entailment scores between claim and passages."""
    if not passage_texts:
        return LocalEntailment()

    claim_words = set(claim_text.lower().split())
    support_scores = []
    contradiction_scores = []
    neutral_scores = []

    contradiction_markers = {"not", "no", "never", "false", "incorrect", "contradicts"}
    support_markers = {"yes", "true", "correct", "indicates", "shows", "demonstrates"}

    for passage in passage_texts:
        passage_words = set(passage.lower().split())
        overlap = len(claim_words & passage_words)
        total = len(claim_words) + len(passage_words)
        similarity = overlap / total if total > 0 else 0.0

        has_contradiction = bool(claim_words & contradiction_markers & passage_words)
        has_support = bool(claim_words & support_markers & passage_words)

        if has_contradiction:
            contradiction_scores.append(similarity)
        elif has_support:
            support_scores.append(similarity)
        else:
            neutral_scores.append(similarity)

    return LocalEntailment(
        max_support=max(support_scores) if support_scores else 0.0,
        mean_support=sum(support_scores) / len(support_scores) if support_scores else 0.0,
        max_contradiction=max(contradiction_scores) if contradiction_scores else 0.0,
        mean_neutral=sum(neutral_scores) / len(neutral_scores) if neutral_scores else 0.0,
    )


def _compute_claim_coverage(claim_text: str, passage_texts: list[str]) -> float:
    """Compute fraction of claim content covered by passages."""
    if not passage_texts:
        return 0.0

    claim_words = set(w.lower() for w in claim_text.split() if len(w) > 3)
    if not claim_words:
        return 0.0

    covered = set()
    for passage in passage_texts:
        passage_words = set(w.lower() for w in passage.split() if len(w) > 3)
        covered.update(claim_words & passage_words)

    return len(covered) / len(claim_words)


def _compute_retrieval_quality(evidence_packet: EvidencePacket) -> RetrievalQuality:
    """Compute retrieval quality metrics from evidence packet metadata."""
    metadata = evidence_packet.retrieval_metadata
    scores = []
    if metadata:
        if metadata.top_score is not None:
            scores.append(metadata.top_score)
        if metadata.score_margin is not None:
            scores.append(metadata.score_margin)

    if not scores and evidence_packet.passages:
        scores = [1.0 / len(evidence_packet.passages)] * len(evidence_packet.passages)

    top_score = max(scores) if scores else 0.0
    score_margin = (scores[0] - scores[1]) if len(scores) > 1 else 0.0
    rank_dispersion = (max(scores) - min(scores)) if len(scores) > 1 else 0.0

    return RetrievalQuality(
        top_score=top_score,
        score_margin=score_margin,
        rank_dispersion=rank_dispersion,
        dense_lexical_agreement=1.0,  # Placeholder for hybrid retrieval comparison
    )


def _compute_conflict(claim_text: str, passage_texts: list[str]) -> Conflict:
    """Detect conflicts between passages."""
    if len(passage_texts) < 2:
        return Conflict()

    contradiction_markers = {"not", "no", "never", "false", "incorrect", "contradicts", "opposite"}
    max_contradiction = 0.0
    support_refute_coexist = False

    for i, p1 in enumerate(passage_texts):
        for p2 in passage_texts[i + 1:]:
            p1_words = set(p1.lower().split())
            p2_words = set(p2.lower().split())
            contradiction_overlap = len(p1_words & contradiction_markers & p2_words)
            if contradiction_overlap > 0:
                max_contradiction = max(max_contradiction, contradiction_overlap / max(len(p1_words), len(p2_words)))
                support_refute_coexist = True

    return Conflict(
        max_contradiction_score=max_contradiction,
        support_refute_coexist=support_refute_coexist,
    )


def _compute_provenance(evidence_packet: EvidencePacket) -> Provenance:
    """Compute provenance quality metrics."""
    passages = evidence_packet.passages
    if not passages:
        return Provenance()

    all_valid = all(p.document_version for p in passages)
    all_resolvable = all(p.page_location for p in passages)

    citation_match_scores = []
    for p in passages:
        if p.page_location and p.document_version:
            citation_match_scores.append(1.0)
        else:
            citation_match_scores.append(0.0)

    avg_match = sum(citation_match_scores) / len(citation_match_scores) if citation_match_scores else 0.0

    return Provenance(
        document_version_valid=all_valid,
        page_resolvable=all_resolvable,
        citation_text_match_score=avg_match,
    )


def _compute_query_ambiguity(claim_text: str) -> QueryAmbiguity:
    """Detect query ambiguity indicators."""
    lowered = claim_text.lower()

    missing_entities = bool(
        re.search(r"\b(drug|medication|treatment|dosage|amount)\b", lowered)
        and not re.search(r"\b(\d+\s*(mg|g|mcg|ml|units?))\b", lowered)
    )

    unresolved_pronouns = bool(re.search(r"\b(it|this|that|they|them)\b", lowered))

    underspecified_scope = bool(
        re.search(r"\b(how|what|why|when|where|who)\b", lowered)
        and len(lowered.split()) < 10
    )

    return QueryAmbiguity(
        missing_entities=missing_entities,
        unresolved_pronouns=unresolved_pronouns,
        underspecified_scope=underspecified_scope,
    )

