"""
Generate labeled claim-evidence pairs for verifier training.

Uses MIRAGE corpus questions + answers to create SUPPORTED/REFUTED/INSUFFICIENT labels.
"""

import json
import random
import sys
from pathlib import Path
from typing import List, Dict, Tuple

# Ensure backend and parent are importable
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent.resolve()
REPO_ROOT = BACKEND_DIR.parent.resolve()
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

import numpy as np
from sentence_transformers import SentenceTransformer

from server.modules.verifier.classifier import ThreeWayVerifier
from server.modules.verifier.calibration import ProbabilityCalibrator
from server.modules.verifier.conformal import ConformalPredictor
from server.schemas import Verdict


random.seed(42)
np.random.seed(42)

DATA_DIR = REPO_ROOT / "data"
CORPUS_PATH = DATA_DIR / "corpus" / "mirage" / "mirage_pubmed_2000.jsonl"
TRAIN_OUTPUT = DATA_DIR / "training" / "verifier_train.jsonl"
CALIBRATION_OUTPUT = DATA_DIR / "training" / "verifier_calibration.jsonl"
MODEL_OUTPUT = DATA_DIR / "models" / "verifier_gp.joblib"
CALIBRATOR_OUTPUT = DATA_DIR / "models" / "calibrator.joblib"
CONFORMAL_OUTPUT = DATA_DIR / "models" / "conformal_quantile.json"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TRAIN_SPLIT = 0.60
CALIB_SPLIT = 0.15
VAL_SPLIT = 0.15
TEST_SPLIT = 0.10


def load_corpus_chunks(path: Path, max_chunks: int = 500) -> List[dict]:
    """Load corpus chunks from JSONL."""
    chunks = []
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= max_chunks:
                break
            line = line.strip()
            if line:
                chunks.append(json.loads(line))
    return chunks


def create_positive_pair(question: str, chunk: dict) -> Tuple[str, str, Verdict]:
    """Create a SUPPORTED pair where the chunk contains the answer."""
    answer = chunk.get("answer", chunk.get("text", ""))
    claim_text = f"{question} The answer is {answer}"
    evidence_text = chunk.get("text", "")
    return claim_text, evidence_text, Verdict.SUPPORTED


def create_negative_pair(question: str, chunks: List[dict], wrong_idx: int) -> Tuple[str, str, Verdict]:
    """Create an INSUFFICIENT pair using an irrelevant chunk."""
    wrong_chunk = chunks[wrong_idx]
    claim_text = question
    evidence_text = wrong_chunk.get("text", "")
    return claim_text, evidence_text, Verdict.INSUFFICIENT


def create_contradiction_pair(question: str, chunk: dict) -> Tuple[str, str, Verdict]:
    """Create a NOT_SUPPORTED pair using a different chunk's answer."""
    wrong_idx = (hash(question) + 13) % len(chunks) if 'chunks' in dir() else 0
    # For now, treat as INSUFFICIENT since we can't generate true contradictions
    # In production, this would use a corpus with contradictory passages
    return "", "", Verdict.INSUFFICIENT


def generate_training_data(chunks: List[dict], n_pairs: int = 1000) -> List[dict]:
    """Generate labeled claim-evidence pairs (binary: SUPPORTED vs INSUFFICIENT)."""
    pairs = []
    n_chunks = len(chunks)

    for i in range(min(n_pairs, n_chunks)):
        chunk = chunks[i]
        question = chunk.get("question", chunk.get("text", "")[:200])
        answer = chunk.get("answer", "")

        if not question or not answer:
            continue

        pos_claim, pos_evidence, pos_label = create_positive_pair(question, chunk)
        pairs.append({
            "claim_text": pos_claim,
            "evidence_text": pos_evidence,
            "label": pos_label.value,
            "chunk_id": chunk.get("chunk_id", f"chunk-{i}"),
        })

        wrong_idx = (i + 7) % n_chunks
        neg_claim, neg_evidence, neg_label = create_negative_pair(question, chunks, wrong_idx)
        pairs.append({
            "claim_text": neg_claim,
            "evidence_text": neg_evidence,
            "label": neg_label.value,
            "chunk_id": chunks[wrong_idx].get("chunk_id", f"chunk-{wrong_idx}"),
        })

    return pairs


def extract_features(claim_text: str, evidence_text: str, embedding_model: SentenceTransformer) -> np.ndarray:
    """Extract 3-dim features: cosine_sim, l2_dist, word_overlap."""
    claim_emb = embedding_model.encode(claim_text, show_progress_bar=False)
    evidence_emb = embedding_model.encode(evidence_text, show_progress_bar=False)

    cosine_sim = float(np.dot(claim_emb, evidence_emb) / (np.linalg.norm(claim_emb) * np.linalg.norm(evidence_emb)))
    l2_dist = float(np.linalg.norm(claim_emb - evidence_emb))

    claim_words = set(claim_text.lower().split())
    evidence_words = set(evidence_text.lower().split())
    overlap = len(claim_words & evidence_words)
    total = len(claim_words) + len(evidence_words)
    word_overlap = overlap / total if total > 0 else 0.0

    features = np.array([cosine_sim, l2_dist, word_overlap], dtype=np.float64)
    return features


def train_verifier():
    """Train the three-way verifier on generated data."""
    print("Loading corpus chunks...")
    chunks = load_corpus_chunks(CORPUS_PATH, max_chunks=2000)
    print(f"Loaded {len(chunks)} chunks")

    print("Generating training data...")
    pairs = generate_training_data(chunks, n_pairs=min(1000, len(chunks)))
    print(f"Generated {len(pairs)} labeled pairs")
    labels_count = {}
    for p in pairs:
        labels_count[p["label"]] = labels_count.get(p["label"], 0) + 1
    print(f"Label distribution: {labels_count}")

    print("Loading embedding model...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    print("Extracting features...")
    X = []
    y = []
    for pair in pairs:
        features = extract_features(pair["claim_text"], pair["evidence_text"], embedding_model)
        X.append(features)
        y.append(pair["label"])

    X = np.array(X)
    y = np.array(y)

    # Split data
    n = len(X)
    indices = np.random.permutation(n)
    train_size = int(n * TRAIN_SPLIT)
    calib_size = int(n * CALIB_SPLIT)
    val_size = int(n * VAL_SPLIT)

    train_idx = indices[:train_size]
    calib_idx = indices[train_size:train_size + calib_size]
    val_idx = indices[train_size + calib_size:train_size + calib_size + val_size]
    test_idx = indices[train_size + calib_size + val_size:]

    X_train, y_train = X[train_idx], y[train_idx]
    X_calib, y_calib = X[calib_idx], y[calib_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    print(f"Train: {len(X_train)}, Calib: {len(X_calib)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # Train verifier
    print("Training GP classifier...")
    verifier = ThreeWayVerifier(embedding_model=embedding_model)
    verifier.train(X_train, y_train)

    # Save model
    MODEL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    verifier.save(str(MODEL_OUTPUT))
    print(f"Model saved to {MODEL_OUTPUT}")

    # Calibrate probabilities (verifier.pipeline already includes CalibratedClassifierCV)
    print("Calibrating probabilities...")
    calib_probs = verifier.pipeline.predict_proba(X_calib)
    calibrator = ProbabilityCalibrator(method="isotonic")
    calibrator.fit(calib_probs, y_calib)
    calibrator.save(str(CALIBRATOR_OUTPUT))
    print(f"Calibrator saved to {CALIBRATOR_OUTPUT}")

    # Compute conformal quantile
    print("Computing conformal quantile...")
    conformal = ConformalPredictor(alpha=0.10, method="LAC")
    conformal.fit(X_calib, y_calib, estimator=verifier.pipeline)
    quantile = float(conformal.predict_quantile())
    print(f"Conformal quantile at alpha=0.10: {quantile:.4f}")

    # Save conformal quantile
    CONFORMAL_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFORMAL_OUTPUT, 'w') as f:
        json.dump({
            "quantile": quantile,
            "alpha": 0.10,
            "method": "LAC",
            "calib_size": len(X_calib),
            "train_size": len(X_train),
        }, f, indent=2)
    print(f"Conformal quantile saved to {CONFORMAL_OUTPUT}")

    # Evaluate on test set
    print("Evaluating on test set...")
    test_preds = verifier.pipeline.predict(X_test)
    test_classes = verifier.pipeline.classes_
    test_pred_labels = test_preds

    accuracy = float(np.mean(test_pred_labels == y_test))
    print(f"Test accuracy: {accuracy:.3f}")

    # Save training metadata
    metadata = {
        "model_path": str(MODEL_OUTPUT),
        "calibrator_path": str(CALIBRATOR_OUTPUT),
        "conformal_path": str(CONFORMAL_OUTPUT),
        "train_size": int(len(X_train)),
        "calib_size": int(len(X_calib)),
        "val_size": int(len(X_val)),
        "test_size": int(len(X_test)),
        "test_accuracy": accuracy,
        "label_distribution": labels_count,
        "embedding_model": EMBEDDING_MODEL,
        "feature_dim": int(X.shape[1]),
        "feature_type": "cosine_l2_overlap_3",
        "description": "3-dim features: cosine_sim, l2_dist, word_overlap",
        "classifier": "RandomForest",
        "classification_type": "binary",
        "classes": ["SUPPORTED", "INSUFFICIENT"],
    }

    metadata_path = DATA_DIR / "models" / "training_metadata.json"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Training metadata saved to {metadata_path}")

    # Save train/calib/val/test splits
    import os
    splits_path = DATA_DIR / "training" / "splits.json"
    os.makedirs(DATA_DIR / "training", exist_ok=True)
    splits = {
        "train": [{"features": x.tolist(), "label": y} for x, y in zip(X_train, y_train)],
        "calib": [{"features": x.tolist(), "label": y} for x, y in zip(X_calib, y_calib)],
        "val": [{"features": x.tolist(), "label": y} for x, y in zip(X_val, y_val)],
        "test": [{"features": x.tolist(), "label": y} for x, y in zip(X_test, y_test)],
    }
    with open(splits_path, 'w') as f:
        json.dump(splits, f)
    print(f"Data splits saved to {splits_path}")

    print("Training complete!")
    return verifier, calibrator, conformal


if __name__ == "__main__":
    train_verifier()
