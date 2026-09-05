"""
Corpus hashing and versioning.

Ensures corpus integrity and version tracking for Article V compliance.
"""

import hashlib
from pathlib import Path
from typing import Optional

from .loader import compute_corpus_hash


class CorpusVersion:
    """Tracks corpus version and hash."""

    def __init__(self, corpus_id: str, corpus_dir: Path):
        self.corpus_id = corpus_id
        self.corpus_dir = corpus_dir
        self._hash: Optional[str] = None

    @property
    def hash(self) -> str:
        """Compute or return cached corpus hash."""
        if self._hash is None:
            self._hash = compute_corpus_hash(self.corpus_dir)
        return self._hash

    def verify(self, expected_hash: str) -> bool:
        """Verify corpus hash matches expected value."""
        return self.hash == expected_hash

    def info(self) -> dict:
        """Return corpus version info."""
        return {
            "corpus_id": self.corpus_id,
            "corpus_hash": self.hash,
            "corpus_dir": str(self.corpus_dir),
        }
