"""
anomaly_detector.py – Agent behaviour anomaly detection.

Uses scikit-learn IsolationForest when available, with hard-coded rule
fallback that always runs regardless of ML model state.
"""
from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import IsolationForest
    import numpy as np
    _SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    _SKLEARN_AVAILABLE = False
    IsolationForest = None  # type: ignore


# ---------------------------------------------------------------------------
# Feature schema
# ---------------------------------------------------------------------------

class AgentBehaviorFeatures(BaseModel):
    tool_calls: int = Field(0, ge=0, description="Total tool calls made")
    failed_calls: int = Field(0, ge=0, description="Number of failed tool calls")
    repeated_calls: int = Field(0, ge=0, description="Number of repeated / duplicate tool calls")
    execution_duration: float = Field(0.0, ge=0.0, description="Total execution time in seconds")
    state_progress: float = Field(0.0, ge=0.0, le=1.0, description="0 = no progress, 1 = completed")
    retry_count: int = Field(0, ge=0, description="Number of retries")
    permission_denied_count: int = Field(0, ge=0, description="Number of permission-denied events")

    def to_vector(self) -> list[float]:
        return [
            float(self.tool_calls),
            float(self.failed_calls),
            float(self.repeated_calls),
            float(self.execution_duration),
            float(self.state_progress),
            float(self.retry_count),
            float(self.permission_denied_count),
        ]


# ---------------------------------------------------------------------------
# Hard-limit thresholds (always enforced)
# ---------------------------------------------------------------------------

HARD_LIMITS = {
    "tool_calls": (24, "critical"),
    "repeated_calls": (3, "high"),
    "execution_duration": (120.0, "high"),
    "failed_calls": (10, "medium"),
    "permission_denied_count": (5, "high"),
    "retry_count": (5, "medium"),
}


# ---------------------------------------------------------------------------
# AnomalyDetector
# ---------------------------------------------------------------------------

class AnomalyDetector:
    """Detect anomalous agent behaviour using IsolationForest + hard rules."""

    def __init__(self):
        if _SKLEARN_AVAILABLE:
            self.model = IsolationForest(contamination=0.1, random_state=42)
        else:
            self.model = None
        self._fitted = False

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------

    def fit(self, features: list[AgentBehaviorFeatures]) -> None:
        """Fit the IsolationForest on historical agent behaviour vectors."""
        if not _SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available – AnomalyDetector running in rule-only mode.")
            return
        if len(features) < 10:
            logger.warning("Too few samples to fit IsolationForest reliably (need ≥10).")
        X = [f.to_vector() for f in features]
        self.model.fit(X)
        self._fitted = True

    # ------------------------------------------------------------------
    # Detect
    # ------------------------------------------------------------------

    def detect(self, features: AgentBehaviorFeatures) -> dict[str, Any]:
        """
        Detect anomalies.

        Returns:
            {
                anomaly_detected: bool,
                severity: str,          # low/medium/high/critical
                signals: list[str],
                score: float,           # negative = more anomalous (IsolationForest)
                hard_limit_triggered: bool,
            }
        """
        # Always run hard limits first
        hard_result = self.hard_limit_check(features)

        signals: list[str] = list(hard_result["violations"])
        anomaly_detected = hard_result["triggered"]
        severity = hard_result["severity"]
        score = 0.0

        # ML layer
        if _SKLEARN_AVAILABLE and self._fitted:
            X = [features.to_vector()]
            raw_score = float(self.model.score_samples(X)[0])  # negative = anomalous
            prediction = int(self.model.predict(X)[0])  # -1 = anomaly, 1 = normal
            score = raw_score

            if prediction == -1:
                anomaly_detected = True
                ml_severity = self._score_to_severity(raw_score)
                signals.append(f"IsolationForest score={raw_score:.4f}")
                # Take the more severe of hard-limit and ML
                if self._severity_rank(ml_severity) > self._severity_rank(severity):
                    severity = ml_severity

        # Additional heuristic signals (soft rules)
        heuristic_signals = self._heuristic_signals(features)
        signals.extend(heuristic_signals)
        if heuristic_signals and not anomaly_detected:
            anomaly_detected = True
            if self._severity_rank("medium") > self._severity_rank(severity):
                severity = "medium"

        if not anomaly_detected:
            severity = "low"

        return {
            "anomaly_detected": anomaly_detected,
            "severity": severity,
            "signals": signals,
            "score": score,
            "hard_limit_triggered": hard_result["triggered"],
        }

    # ------------------------------------------------------------------
    # Hard limits
    # ------------------------------------------------------------------

    def hard_limit_check(self, features: AgentBehaviorFeatures) -> dict[str, Any]:
        """
        Always-on rule-based checks.

        Returns:
            {triggered: bool, severity: str, violations: list[str]}
        """
        violations: list[str] = []
        worst_severity = "low"

        feature_dict = {
            "tool_calls": features.tool_calls,
            "repeated_calls": features.repeated_calls,
            "execution_duration": features.execution_duration,
            "failed_calls": features.failed_calls,
            "permission_denied_count": features.permission_denied_count,
            "retry_count": features.retry_count,
        }

        for field_name, (threshold, sev) in HARD_LIMITS.items():
            value = feature_dict.get(field_name, 0)
            if value > threshold:
                violations.append(
                    f"{field_name}={value} exceeds limit {threshold} [{sev}]"
                )
                if self._severity_rank(sev) > self._severity_rank(worst_severity):
                    worst_severity = sev

        return {
            "triggered": len(violations) > 0,
            "severity": worst_severity,
            "violations": violations,
        }

    # ------------------------------------------------------------------
    # Heuristic soft signals
    # ------------------------------------------------------------------

    @staticmethod
    def _heuristic_signals(features: AgentBehaviorFeatures) -> list[str]:
        signals = []
        if features.tool_calls > 0 and features.failed_calls / features.tool_calls > 0.5:
            signals.append(
                f"High failure rate: {features.failed_calls}/{features.tool_calls} calls failed"
            )
        if features.tool_calls > 5 and features.state_progress < 0.1:
            signals.append(
                f"No state progress after {features.tool_calls} tool calls"
            )
        if features.permission_denied_count > 2:
            signals.append(
                f"Multiple permission denials: {features.permission_denied_count}"
            )
        return signals

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _score_to_severity(score: float) -> str:
        """Map IsolationForest score to severity label (more negative = worse)."""
        if score < -0.3:
            return "critical"
        if score < -0.2:
            return "high"
        if score < -0.1:
            return "medium"
        return "low"

    @staticmethod
    def _severity_rank(sev: str) -> int:
        return {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(sev, 0)
