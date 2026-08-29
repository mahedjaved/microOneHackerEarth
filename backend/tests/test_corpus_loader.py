"""Tests for CURA-Med corpus loader and hash modules."""

import json
import pytest
from pathlib import Path
from server.modules.corpus.loader import (
    sha256_file,
    sha256_string,
    compute_corpus_hash,
    load_corpus_chunks,
    build_evidence_packet,
)
from server.schemas import Passage, RetrievalMetadata


class TestCorpusHash:
    def test_sha256_file(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")
        hash_value = sha256_file(test_file)
        assert len(hash_value) == 64
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert hash_value == expected

    def test_sha256_string(self):
        hash_value = sha256_string("hello world")
        assert len(hash_value) == 64
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert hash_value == expected

    def test_compute_corpus_hash(self, tmp_path):
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        (corpus_dir / "chunk1.jsonl").write_text('{"text": "chunk 1"}')
        (corpus_dir / "chunk2.jsonl").write_text('{"text": "chunk 2"}')
        
        hash_value = compute_corpus_hash(corpus_dir)
        assert len(hash_value) == 64

    def test_compute_corpus_hash_empty(self, tmp_path):
        corpus_dir = tmp_path / "empty_corpus"
        corpus_dir.mkdir()
        hash_value = compute_corpus_hash(corpus_dir)
        assert len(hash_value) == 64


class TestCorpusLoader:
    def test_load_corpus_chunks(self, tmp_path):
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        (corpus_dir / "chunks.jsonl").write_text(
            '{"chunk_id": "1", "text": "Aspirin is a pain reliever"}\n'
            '{"chunk_id": "2", "text": "Ibuprofen is an anti-inflammatory"}\n'
        )
        chunks = list(load_corpus_chunks(corpus_dir))
        assert len(chunks) == 2
        assert chunks[0]["chunk_id"] == "1"
        assert chunks[1]["chunk_id"] == "2"

    def test_load_corpus_chunks_empty(self, tmp_path):
        corpus_dir = tmp_path / "empty"
        corpus_dir.mkdir()
        chunks = list(load_corpus_chunks(corpus_dir))
        assert len(chunks) == 0

    def test_build_evidence_packet(self):
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
        packet = build_evidence_packet(
            corpus_id="test-corpus",
            corpus_hash="test-hash",
            retrieval_query="What is aspirin?",
            passages=passages,
            retriever_version="test-v1",
            latency_ms=100,
            top_score=0.95,
            score_margin=0.1,
            rank_dispersion=0.2,
        )
        assert packet.corpus_id == "test-corpus"
        assert len(packet.passages) == 1
        assert packet.passages[0].chunk_id == "chunk-1"
