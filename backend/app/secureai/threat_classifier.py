"""
threat_classifier.py – ML-backed threat classifier.

Uses scikit-learn TF-IDF + Logistic Regression.
Falls back to a rule-based heuristic if scikit-learn is unavailable or the
model has not been trained yet.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Graceful import of scikit-learn
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, precision_recall_fscore_support
    from sklearn.model_selection import train_test_split
    import numpy as np
    _SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    _SKLEARN_AVAILABLE = False
    TfidfVectorizer = None  # type: ignore
    LogisticRegression = None  # type: ignore

# Simple rule keywords used for the fallback
_THREAT_KEYWORDS = {
    "prompt_injection": [
        "ignore", "disregard", "bypass", "override", "jailbreak",
        "system prompt", "previous instructions", "developer mode",
    ],
    "data_exfiltration": [
        "dump", "exfiltrate", "leak", "reveal database", "list passwords",
        "show all users",
    ],
    "jailbreak": [
        "DAN mode", "do anything now", "unrestricted mode", "no restrictions",
        "act as evil",
    ],
    "sensitive_data": [
        "social security", "credit card", "password", "api key",
    ],
}


class ThreatClassifier:
    """TF-IDF + Logistic Regression threat classifier with rule-based fallback."""

    def __init__(self):
        if _SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=5000,
                sublinear_tf=True,
                strip_accents="unicode",
            )
            self.classifier = LogisticRegression(
                max_iter=1000,
                C=1.0,
                solver="lbfgs",
                multi_class="multinomial",
            )
        else:
            self.vectorizer = None
            self.classifier = None

        self._is_trained = False
        self._classes: list[str] = []

    # ------------------------------------------------------------------
    # Train
    # ------------------------------------------------------------------

    def train(self, texts: list[str], labels: list[str]) -> dict[str, Any]:
        """Train on (texts, labels). Returns training metrics."""
        if not _SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available – classifier not trained.")
            return {"error": "scikit-learn not available"}

        if len(texts) != len(labels):
            raise ValueError("texts and labels must have the same length")
        if len(texts) < 4:
            raise ValueError("Need at least 4 samples to train")

        # Split for metrics
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                texts, labels, test_size=0.2, random_state=42, stratify=labels
            )
        except ValueError:
            X_train, X_test, y_train, y_test = texts, texts, labels, labels

        X_train_vec = self.vectorizer.fit_transform(X_train)
        self.classifier.fit(X_train_vec, y_train)
        self._is_trained = True
        self._classes = list(self.classifier.classes_)

        # Evaluate on held-out set
        X_test_vec = self.vectorizer.transform(X_test)
        y_pred = self.classifier.predict(X_test_vec)

        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        return {
            "trained": True,
            "n_samples": len(texts),
            "n_classes": len(self._classes),
            "classes": self._classes,
            "accuracy": report.get("accuracy", 0.0),
            "macro_f1": report.get("macro avg", {}).get("f1-score", 0.0),
        }

    # ------------------------------------------------------------------
    # Predict
    # ------------------------------------------------------------------

    def predict(self, text: str) -> dict[str, Any]:
        """Return {label, confidence}. Falls back to rule-based if not trained."""
        if _SKLEARN_AVAILABLE and self._is_trained:
            vec = self.vectorizer.transform([text])
            label = self.classifier.predict(vec)[0]
            proba = self.classifier.predict_proba(vec)[0]
            class_idx = list(self.classifier.classes_).index(label)
            return {"label": label, "confidence": float(proba[class_idx])}

        # Rule-based fallback
        return self._rule_predict(text)

    # ------------------------------------------------------------------
    # Evaluate
    # ------------------------------------------------------------------

    def evaluate(self, texts: list[str], labels: list[str]) -> dict[str, Any]:
        """Return per-class precision, recall, f1."""
        if not _SKLEARN_AVAILABLE or not self._is_trained:
            return {"error": "Classifier not trained or sklearn unavailable"}

        X_vec = self.vectorizer.transform(texts)
        y_pred = self.classifier.predict(X_vec)
        report = classification_report(labels, y_pred, output_dict=True, zero_division=0)
        return report

    # ------------------------------------------------------------------
    # Rule-based fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _rule_predict(text: str) -> dict[str, Any]:
        lower = text.lower()
        best_label = "none"
        best_score = 0.0

        for label, keywords in _THREAT_KEYWORDS.items():
            hits = sum(1 for kw in keywords if kw.lower() in lower)
            score = hits / len(keywords)
            if score > best_score:
                best_score = score
                best_label = label

        confidence = min(0.9, best_score * 2.5) if best_score > 0 else 0.05
        return {"label": best_label, "confidence": confidence}
