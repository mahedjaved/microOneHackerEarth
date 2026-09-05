"""Inspect verifier scores at claim level.

Diagnoses why support_probability is low by showing:
1. Each decomposed claim from the LLM answer
2. Verifier SUPPORTED probability for each claim against each passage
3. Identifies boilerplate sentences that drag down the average

Run from project root:
    python tests/comparative/inspect_verifier.py
"""
import os
import sys
from pathlib import Path

# Get directories
script_dir = Path(__file__).resolve().parent
project_dir = script_dir.parent.parent
backend_dir = project_dir / "backend"

# Change to backend directory and add it to path
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from server.modules.claims.composer import ClaimComposer
from server.modules.verifier.classifier import ThreeWayVerifier
from server.config import settings
from pinecone import Pinecone
from joblib import load
from sentence_transformers import SentenceTransformer

# Load embedding models
# The live server uses SentenceTransformer for the verifier
verifier_embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
# HuggingFaceEmbeddings for Pinecone retrieval queries
from server.modules.load_vectorstore import embedding_model as retrieval_embedding_model

pc = Pinecone(api_key=settings.pinecone_api_key)
index = pc.Index(settings.pinecone_index_name)

# Load verifier model
verifier_path = project_dir / "data/models/verifier_gp.joblib"
print(f"Loading verifier from: {verifier_path}")
pipeline = load(str(verifier_path))
verifier = ThreeWayVerifier(embedding_model=verifier_embedding_model)
verifier.pipeline = pipeline
verifier.is_trained = True

# Test questions
questions = [
    ("D1", "According to the aspirin document, what is the maximum single adult dose?"),
    ("D2", "What does the aspirin document say about administration with food?"),
    ("D5", "According to the document, should aspirin be taken with food or on an empty stomach?"),
]

# Simulated LLM answers (typical responses for these questions)
sample_answers = {
    "D1": "The maximum single adult dose is 325-650 mg every 4 hours as needed. Do not exceed 4,000 mg in 24 hours. Always consult a healthcare provider before taking any medication.",
    "D2": "Aspirin should be taken with food or milk to reduce stomach irritation. If you experience stomach upset, consult your healthcare provider.",
    "D5": "Aspirin can be taken with food or on an empty stomach, but taking it with food may reduce stomach irritation. Please consult your doctor for personalized advice.",
}

composer = ClaimComposer()

for qid, question in questions:
    print(f"\n{'='*60}")
    print(f"[{qid}] {question}")
    print(f"{'='*60}")

    # Retrieve passages using the retrieval embedding model
    emb = retrieval_embedding_model.embed_query(question)
    matches = index.query(vector=emb, top_k=2, include_metadata=True)["matches"]
    passages = [m["metadata"].get("text", "") for m in matches]

    print(f"\nRetrieved {len(passages)} passages:")
    for i, p in enumerate(passages):
        print(f"  [{i+1}] ({len(p)} chars) {p[:80]}...")

    # Get LLM answer (use sample or query LLM)
    answer = sample_answers.get(qid, "")
    if answer:
        print(f"\nLLM Answer: {answer[:100]}...")

        # Split into sentences/claims
        sentences = composer._split_sentences(answer)
        print(f"\nDecomposed into {len(sentences)} claims:")
        for i, sent in enumerate(sentences):
            print(f"\n  Claim {i+1}: {sent}")

            # Check verifier score against each passage
            for j, p in enumerate(passages):
                result = verifier.predict_text(sent, p)
                supported_prob = result.probabilities.get("SUPPORTED", 0.0)
                predicted = result.predicted_label
                print(f"    vs Passage {j+1}: SUPPORTED={supported_prob:.3f}, predicted={predicted}")

        # Calculate max and average
        all_supported = []
        for sent in sentences:
            for p in passages:
                result = verifier.predict_text(sent, p)
                all_supported.append(result.probabilities.get("SUPPORTED", 0.0))

        if all_supported:
            avg = sum(all_supported) / len(all_supported)
            mx = max(all_supported)
            print(f"\n  Summary: avg SUPPORTED={avg:.3f}, max SUPPORTED={mx:.3f}")
            if mx >= 0.5:
                print(f"  [OK] Max SUPPORTED >= 0.5 (will pass conformal threshold)")
            else:
                print(f"  [FAIL] Max SUPPORTED < 0.5 (will trigger doubt certificate)")
    else:
        print("\nNo sample answer available for this question")
