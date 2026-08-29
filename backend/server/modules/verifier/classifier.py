"""
Three-way verifier classifier.

Uses RandomForestClassifier + CalibratedClassifierCV for SUPPORTED / REFUTED / INSUFFICIENT.
For C0: uses 3-dim features (cosine_sim, l2_dist, word_overlap).
For A0: upgrade to fine-tuned biomedical NLI model if data permits.
"""

import numpy as np
from typing import Optional, List, Dict
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from joblib import dump, load

from server.schemas import Verdict, VerifierResult, EvidenceFeatureVector


EMBEDDING_DIM = 384


def _compute_embedding_features(claim_text: str, evidence_text: str, embedding_model) -> np.ndarray:
    """Compute 3-dim features for claim-evidence pair."""
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

        claim_id_placeholder = None
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
