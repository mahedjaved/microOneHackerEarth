"""Quick end-to-end test of the UQ pipeline."""

import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from server.main import _init_uq_pipeline
from server.modules.query_handlers import run_uq_pipeline
from server.modules.corpus.loader import build_evidence_packet
from server.schemas import Passage

# Initialize UQ pipeline
_init_uq_pipeline()
print("UQ pipeline initialized")

# Create a test evidence packet
passages = [
    Passage(
        chunk_id="chunk-1",
        document_id="medical-doc-1",
        document_version="v1",
        page_location="page-1",
        text="Aspirin is a common pain reliever used to treat mild to moderate pain.",
        provenance_hash="abc123",
    )
]

evidence_packet = build_evidence_packet(
    corpus_id="medical-corpus-v1",
    corpus_hash="test-hash",
    retrieval_query="What is aspirin used for?",
    passages=passages,
    retriever_version="test-v1",
    latency_ms=0,
)

# Run UQ pipeline
question = "What is aspirin used for?"
response, artifact = run_uq_pipeline(
    question=question,
    evidence_packet=evidence_packet,
)

print(f"Response: {response}")
print(f"Final decision: {artifact.final_decision}")
print(f"Run ID: {artifact.run_id}")
print("End-to-end test passed!")
