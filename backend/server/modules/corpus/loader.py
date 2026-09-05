"""
Corpus loader and versioning.

Loads and versions corpus chunks with provenance.
Part 1: MIRAGE/PubMed abstract subset.
Part 2: Synthetic adversarial case set.
"""

import hashlib
import json
from pathlib import Path
from typing import Iterator

from server.schemas import Passage, EvidencePacket, RetrievalMetadata


def sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_string(s: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def compute_corpus_hash(corpus_dir: Path) -> str:
    """Compute aggregate hash of all files in corpus directory."""
    h = hashlib.sha256()
    for filepath in sorted(corpus_dir.rglob("*")):
        if filepath.is_file():
            h.update(filepath.name.encode("utf-8"))
            h.update(sha256_file(filepath).encode("utf-8"))
    return h.hexdigest()


def load_corpus_chunks(corpus_dir: Path) -> Iterator[dict]:
    """Load corpus chunks from JSONL files."""
    for jsonl_path in corpus_dir.rglob("*.jsonl"):
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


def build_evidence_packet(
    corpus_id: str,
    corpus_hash: str,
    retrieval_query: str,
    passages: list[Passage],
    retriever_version: str,
    latency_ms: int,
    top_score: float | None = None,
    score_margin: float | None = None,
    rank_dispersion: float | None = None,
) -> EvidencePacket:
    """Build a versioned evidence packet from retrieved passages."""
    metadata = RetrievalMetadata(
        retriever_version=retriever_version,
        top_k=len(passages),
        latency_ms=latency_ms,
        top_score=top_score,
        score_margin=score_margin,
        rank_dispersion=rank_dispersion,
    )
    return EvidencePacket(
        corpus_id=corpus_id,
        corpus_hash=corpus_hash,
        retrieval_query=retrieval_query,
        passages=passages,
        retrieval_metadata=metadata,
    )
