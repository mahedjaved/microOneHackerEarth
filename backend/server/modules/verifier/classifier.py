"""
Three-way verifier classifier.

Uses RandomForestClassifier + CalibratedClassifierCV for SUPPORTED / REFUTED / INSUFFICIENT.
For C0: uses 4-dim features (cosine_sim, l2_dist, word_overlap, numeric_containment).
For A0: upgrade to fine-tuned biomedical NLI model if data permits.
"""

import re
import uuid
import numpy as np
from typing import Optional, List, Dict
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from joblib import dump, load

from server.schemas import Verdict, VerifierResult, EvidenceFeatureVector


EMBEDDING_DIM = 384


def _extract_numbers(text: str) -> list[float]:
    """Extract numeric values from text.
    
    Handles:
    - Integers: 325, 650, 4000
    - Decimals: 0.5, 2.5
    - Ranges: 325-650, 325 to 650
    - Fractions: 1/2
    """
    numbers = []
    
    # Extract ranges like "325-650" or "325 to 650"
    range_pattern = r'(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)'
    for match in re.finditer(range_pattern, text):
        numbers.append(float(match.group(1)))
        numbers.append(float(match.group(2)))
    
    # Extract individual numbers
    number_pattern = r'\b(\d+(?:\.\d+)?)\b'
    for match in re.finditer(number_pattern, text):
        num = float(match.group(1))
        if num not in numbers:  # Avoid duplicates from range extraction
            numbers.append(num)
    
    return numbers


def _numeric_containment(claim_text: str, evidence_text: str) -> float:
    """Check if numbers in the claim are contained in the evidence.
    
    Returns 1.0 if all claim numbers appear in evidence, 0.0 otherwise.
    For ranges, checks if claim number falls within evidence range.
    """
    claim_numbers = _extract_numbers(claim_text)
    evidence_numbers = _extract_numbers(evidence_text)
    
    if not claim_numbers:
        return 1.0  # No numbers to check, neutral
    
    if not evidence_numbers:
        return 0.0  # Claim has numbers but evidence has none
    
    # Check each claim number
    contained_count = 0
    for cn in claim_numbers:
        # Direct match
        if cn in evidence_numbers:
            contained_count += 1
            continue
        
        # Range containment: check if claim number falls within any evidence range
        # Look for range patterns in evidence
        range_pattern = r'(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)'
        for match in re.finditer(range_pattern, evidence_text):
            low = float(match.group(1))
            high = float(match.group(2))
            if low <= cn <= high:
                contained_count += 1
                break
    
    return contained_count / len(claim_numbers)


def _compute_embedding_features(claim_text: str, evidence_text: str, embedding_model) -> np.ndarray:
    """Compute 4-dim features for claim-evidence pair."""
    # Live server uses SentenceTransformer which has .encode()
    claim_emb = embedding_model.encode(claim_text, show_progress_bar=False)
    evidence_emb = embedding_model.encode(evidence_text, show_progress_bar=False)

    cosine_sim = float(np.dot(claim_emb, evidence_emb) / (np.linalg.norm(claim_emb) * np.linalg.norm(evidence_emb)))
    l2_dist = float(np.linalg.norm(claim_emb - evidence_emb))

    claim_words = set(claim_text.lower().split())
    evidence_words = set(evidence_text.lower().split())
    overlap = len(claim_words & evidence_words)
    total = len(claim_words) + len(evidence_words)
    word_overlap = overlap / total if total > 0 else 0.0

    numeric_containment = _numeric_containment(claim_text, evidence_text)

    return np.array([cosine_sim, l2_dist, word_overlap, numeric_containment], dtype=np.float64)


class ThreeWayVerifier:
    """
    Three-way claim-evidence verifier.

    For C0: RandomForestClassifier with isotonic calibration on 3-dim features (cosine_sim, l2_dist, word_overlap).
    For A0: upgrade to fine-tuned biomedical NLI model if data permits.
    """

    def __init__(self, model_path: Optional[str] = None, embedding_model=None):
        self.embedding_model = embedding_model
        if model_path:
            self.pipeline = load(model_path)
            self.is_trained = True
        else:
            rf = RandomForestClassifier(n_estimators=200, max_depth=None, random_state=42, n_jobs=-1)
            self.pipeline = Pipeline([
                ("scaler", StandardScaler()),
                ("classifier", CalibratedClassifierCV(rf, method="isotonic", cv=3)),
            ])
            self.is_trained = False

    def train(self, X: np.ndarray, y: np.ndarray):
        """Train the verifier on labeled claim-evidence pairs."""
        self.pipeline.fit(X, y)
        self.is_trained = True

    def predict_text(self, claim_text: str, evidence_text: str) -> VerifierResult:
        """Predict verdict for raw claim and evidence text using embedding features."""
        if not self.is_trained:
            raise RuntimeError("Verifier must be trained before prediction")
        if self.embedding_model is None:
            raise RuntimeError("Embedding model must be provided for predict_text")

        claim_id_placeholder = uuid.uuid4()
        X = _compute_embedding_features(claim_text, evidence_text, self.embedding_model).reshape(1, -1)
        probabilities = self.pipeline.predict_proba(X)[0]

        classes = self.pipeline.classes_
        prob_dict = {Verdict(c): float(p) for c, p in zip(classes, probabilities)}

        predicted_label = max(prob_dict, key=prob_dict.get)

        conformal_set = [predicted_label]
        if prob_dict[predicted_label] < 0.7:
            sorted_labels = sorted(prob_dict, key=prob_dict.get, reverse=True)
            conformal_set = sorted_labels[:2]

        return VerifierResult(
            claim_id=claim_id_placeholder,
            predicted_label=predicted_label,
            probabilities=prob_dict,
            calibrated=True,
            conformal_set=conformal_set,
            coverage_target=0.90,
            calibration_id="calibration-placeholder",
        )

    def predict(self, feature_vector: EvidenceFeatureVector) -> VerifierResult:
        """Predict verdict from EvidenceFeatureVector (API compatibility)."""
        if not self.is_trained:
            raise RuntimeError("Verifier must be trained before prediction")
        if self.embedding_model is None:
            raise RuntimeError("Embedding model must be provided for predict")

        claim_text = getattr(feature_vector, 'claim_text', '') or ''
        evidence_text = getattr(feature_vector, 'evidence_text', '') or ''
        return self.predict_text(claim_text, evidence_text)

    def save(self, path: str):
        """Save trained model to disk."""
        dump(self.pipeline, path)
