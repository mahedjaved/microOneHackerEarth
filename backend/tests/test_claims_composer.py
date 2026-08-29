"""Tests for CURA-Med claims composer and feature vector modules."""

import uuid
import pytest
from server.modules.claims.composer import ClaimComposer
from server.modules.claims.feature_vector import compute_feature_vector, compute_simple_features
from server.schemas import EvidencePacket, Passage, RetrievalMetadata, Claim


class TestClaimComposer:
    def test_decompose_simple_answer(self):
        composer = ClaimComposer()
        answer = "Aspirin is used for pain relief. It reduces inflammation. It prevents blood clots."
        
        passages = [
            Passage(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_version="v1",
                page_location="page-1",
                text="Aspirin is used for pain relief",
                provenance_hash="abc123",
            )
        ]
        evidence_packet = EvidencePacket(
            corpus_id="test",
            corpus_hash="test-hash",
            retrieval_query="test",
            passages=passages,
            retrieval_metadata=RetrievalMetadata(
                retriever_version="test",
                top_k=1,
                latency_ms=0,
            ),
        )
        
        claims = composer.decompose(answer, evidence_packet)
        assert len(claims) == 3
        assert all(isinstance(c, Claim) for c in claims)
        assert all(c.claim_id for c in claims)

    def test_decompose_empty_answer(self):
        composer = ClaimComposer()
        passages = []
        evidence_packet = EvidencePacket(
            corpus_id="test",
            corpus_hash="test-hash",
            retrieval_query="test",
            passages=passages,
            retrieval_metadata=RetrievalMetadata(
                retriever_version="test",
                top_k=0,
                latency_ms=0,
            ),
        )
        claims = composer.decompose("", evidence_packet)
        assert len(claims) == 0

    def test_decompose_single_sentence(self):
        composer = ClaimComposer()
        answer = "Aspirin is a pain reliever."
        passages = []
        evidence_packet = EvidencePacket(
            corpus_id="test",
            corpus_hash="test-hash",
            retrieval_query="test",
            passages=passages,
            retrieval_metadata=RetrievalMetadata(
                retriever_version="test",
                top_k=0,
                latency_ms=0,
            ),
        )
        claims = composer.decompose(answer, evidence_packet)
        assert len(claims) == 1
        assert "Aspirin" in claims[0].text

    def test_match_citations(self):
        composer = ClaimComposer()
        passages = [
            Passage(
                chunk_id="chunk-1",
                document_id="doc-1",
                document_version="v1",
                page_location="page-1",
                text="Aspirin is used for pain relief",
                provenance_hash="abc123",
            ),
            Passage(
                chunk_id="chunk-2",
                document_id="doc-2",
                document_version="v1",
                page_location="page-2",
                text="Ibuprofen is an anti-inflammatory",
                provenance_hash="def456",
            ),
        ]
        evidence_packet = EvidencePacket(
            corpus_id="test",
            corpus_hash="test-hash",
            retrieval_query="test",
            passages=passages,
            retrieval_metadata=RetrievalMetadata(
                retriever_version="test",
                top_k=2,
                latency_ms=0,
            ),
        )
        
        sentence = "Aspirin is used for pain relief"
        citations = composer._match_citations(sentence, evidence_packet)
        assert "chunk-1" in citations
