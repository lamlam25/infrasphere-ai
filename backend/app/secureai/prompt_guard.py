"""
prompt_guard.py – Layered AI prompt threat detection.

Layers:
  1. Input normalisation
  2. Heuristic regex pattern matching
  3. Semantic keyword density scoring
  4. Optional ML classifier (scikit-learn TF-IDF + LR)
  5. Policy decision (action + risk level)
"""
from __future__ import annotations

import re
import unicodedata
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", "critical"),
    (r"disregard\s+(all\s+)?(previous|prior)\s+(instructions?|prompts?)", "critical"),
    (r"you\s+are\s+now\s+(in\s+)?(developer|god|admin|root|unrestricted)\s+mode", "critical"),
    (r"reveal\s+(your\s+)?(system\s+prompt|instructions?|training)", "high"),
    (r"print\s+(your\s+)?(system\s+prompt|instructions?)", "high"),
    (r"show\s+(me\s+)?(your\s+)?(system\s+prompt|hidden\s+instructions?)", "high"),
    (r"bypass\s+(all\s+)?(safety|security|filter|restriction)", "critical"),
    (r"act\s+as\s+(if\s+you\s+are\s+)?(an?\s+)?(unrestricted|evil|harmful|jailbroken)", "critical"),
    (r"pretend\s+(you\s+are|to\s+be)\s+(an?\s+)?(unrestricted|evil|different|no\s+rules)", "high"),
    (r"jailbreak", "high"),
    (r"DAN\s+mode", "critical"),
    (r"do\s+anything\s+now", "high"),
    (r"execute\s+(arbitrary\s+)?(code|command|shell|script)", "critical"),
    (r"access\s+(private|restricted|confidential)\s+(data|documents?|records?)", "high"),
    (r"leak\s+(sensitive|private|confidential)\s+information", "high"),
    (r"exfiltrate", "critical"),
    (r"override\s+(security|safety|permission|access)\s+(control|policy|check)", "critical"),
    (r"treat\s+(this|the\s+following)\s+(as\s+)?(trusted|system|instruction)", "high"),
    (r"new\s+instruction[s]?\s*:", "medium"),
    (r"<\s*system\s*>", "high"),
    (r"\[INST\].*override", "high"),
]

DATA_EXFILTRATION_PATTERNS: list[tuple[str, str]] = [
    (r"show\s+(all\s+)?(user|employee|private|confidential)\s+(data|records?|files?)", "high"),
    (r"list\s+(all\s+)?(user\s+)?(password|credential|secret|key)s?", "critical"),
    (r"reveal\s+(database|db)\s+(schema|structure|tables?)", "high"),
    (r"dump\s+(all\s+)?(data|records?|tables?|database)", "critical"),
]

# Compiled once at import time (case-insensitive)
_COMPILED_INJECTION: list[tuple[re.Pattern, str]] = [
    (re.compile(pat, re.IGNORECASE | re.DOTALL), lvl)
    for pat, lvl in INJECTION_PATTERNS
]
_COMPILED_EXFILTRATION: list[tuple[re.Pattern, str]] = [
    (re.compile(pat, re.IGNORECASE | re.DOTALL), lvl)
    for pat, lvl in DATA_EXFILTRATION_PATTERNS
]

# Risk ordering
_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

# Semantic density keywords – secondary signal
_SEMANTIC_KEYWORDS = [
    "ignore", "disregard", "bypass", "override", "jailbreak",
    "reveal", "dump", "exfiltrate", "leak", "unrestricted",
    "system prompt", "hidden instructions", "no restrictions",
    "act as", "pretend", "developer mode", "god mode",
]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ThreatDetectionResult:
    threat_type: str          # none / prompt_injection / jailbreak / data_exfiltration / unauthorized_tool / sensitive_data
    risk_level: str           # low / medium / high / critical
    confidence: float         # 0.0 – 1.0
    action: str               # allow / flag / quarantine / block
    reason: str
    matched_patterns: list[str] = field(default_factory=list)
    detection_method: str = "rule"   # rule / ml / combined

    def to_dict(self) -> dict:
        return {
            "threat_type": self.threat_type,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "action": self.action,
            "reason": self.reason,
            "matched_patterns": self.matched_patterns,
            "detection_method": self.detection_method,
        }


# ---------------------------------------------------------------------------
# PromptGuard
# ---------------------------------------------------------------------------

class PromptGuard:
    """Multi-layer prompt security inspector.

    Original input is NEVER rewritten.  All decisions are based on a
    normalised copy produced internally.
    """

    def __init__(self, ml_classifier=None):
        """
        Args:
            ml_classifier: Optional ThreatClassifier instance.  When supplied
                           and fitted, its predictions are blended with the
                           rule-based score (combined detection_method).
        """
        self._ml = ml_classifier

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def inspect(self, text: str, context: dict | None = None) -> ThreatDetectionResult:
        """Inspect *text* for security threats.

        The original *text* is preserved; all detection works on a
        normalised copy.
        """
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")

        # Layer 1: normalise (internal copy only)
        norm = self._normalise(text)

        # Layer 2: heuristic pattern matching
        injection_matches, injection_risk = self._check_patterns(norm, _COMPILED_INJECTION)
        exfil_matches, exfil_risk = self._check_patterns(norm, _COMPILED_EXFILTRATION)

        all_matches = injection_matches + exfil_matches

        # Determine primary threat type
        if _RISK_ORDER.get(exfil_risk, -1) > _RISK_ORDER.get(injection_risk, -1):
            threat_type = "data_exfiltration"
            pattern_risk = exfil_risk
        elif injection_matches:
            threat_type = "prompt_injection"
            pattern_risk = injection_risk
        else:
            threat_type = "none"
            pattern_risk = "low"

        # Layer 3: keyword density scoring
        density_score = self._keyword_density(norm)

        # Build rule-based confidence
        rule_confidence = self._confidence_from_risk(pattern_risk)
        if density_score > 0.3:
            rule_confidence = min(1.0, rule_confidence + 0.1)

        # Layer 4: optional ML blend
        ml_confidence: float | None = None
        ml_label: str | None = None
        if self._ml is not None:
            try:
                ml_result = self._ml.predict(text)
                ml_label = ml_result.get("label", "none")
                ml_confidence = ml_result.get("confidence", 0.0)
            except Exception:
                pass  # ML failures are non-fatal

        # Blend
        if ml_confidence is not None:
            final_confidence = 0.6 * rule_confidence + 0.4 * ml_confidence
            detection_method = "combined"
            # If ML detects a threat that rules missed
            if ml_label and ml_label != "none" and threat_type == "none":
                threat_type = ml_label
                pattern_risk = "medium" if final_confidence < 0.6 else "high"
        else:
            final_confidence = rule_confidence
            detection_method = "rule"

        # Layer 5: policy decision
        action, reason = self._policy_decision(
            threat_type, pattern_risk, final_confidence, all_matches
        )

        return ThreatDetectionResult(
            threat_type=threat_type,
            risk_level=pattern_risk if threat_type != "none" else "low",
            confidence=round(final_confidence, 4),
            action=action,
            reason=reason,
            matched_patterns=all_matches,
            detection_method=detection_method,
        )

    # ------------------------------------------------------------------
    # Layer 1 – normalisation (never modifies original)
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise(text: str) -> str:
        # Unicode NFC normalisation
        text = unicodedata.normalize("NFC", text)
        # Lowercase
        text = text.lower()
        # Collapse excessive whitespace (keep single spaces / newlines intact
        # for regex matching but remove doubled spaces)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text

    # ------------------------------------------------------------------
    # Layer 2 – pattern detection
    # ------------------------------------------------------------------

    @staticmethod
    def _check_patterns(
        norm: str,
        compiled: list[tuple[re.Pattern, str]],
    ) -> tuple[list[str], str]:
        """Return (list_of_matched_pattern_strings, highest_risk_level)."""
        matches: list[str] = []
        highest_risk = "low"

        for pattern, risk in compiled:
            m = pattern.search(norm)
            if m:
                matches.append(pattern.pattern)
                if _RISK_ORDER.get(risk, 0) > _RISK_ORDER.get(highest_risk, 0):
                    highest_risk = risk

        return matches, highest_risk

    # ------------------------------------------------------------------
    # Layer 3 – keyword density
    # ------------------------------------------------------------------

    @staticmethod
    def _keyword_density(norm: str) -> float:
        """Score 0-1 based on how many security-sensitive keywords appear."""
        if not norm:
            return 0.0
        words = norm.split()
        if not words:
            return 0.0
        hit_count = sum(
            1 for kw in _SEMANTIC_KEYWORDS if kw in norm
        )
        # Normalise by total keyword count (max = 1.0)
        return min(1.0, hit_count / len(_SEMANTIC_KEYWORDS))

    # ------------------------------------------------------------------
    # Layer 5 – policy decision
    # ------------------------------------------------------------------

    @staticmethod
    def _confidence_from_risk(risk: str) -> float:
        return {
            "critical": 0.95,
            "high": 0.80,
            "medium": 0.55,
            "low": 0.10,
        }.get(risk, 0.10)

    @staticmethod
    def _policy_decision(
        threat_type: str,
        risk_level: str,
        confidence: float,
        matched_patterns: list[str],
    ) -> tuple[str, str]:
        """Return (action, reason)."""
        if threat_type == "none" or risk_level == "low":
            return "allow", "No threat patterns detected."

        if risk_level == "critical" and confidence >= 0.7:
            return "block", (
                f"Critical threat '{threat_type}' detected with confidence "
                f"{confidence:.2f}. Matched: {matched_patterns[:3]}"
            )

        if risk_level == "high" and confidence >= 0.5:
            return "quarantine", (
                f"High-risk threat '{threat_type}' detected with confidence "
                f"{confidence:.2f}. Matched: {matched_patterns[:3]}"
            )

        if risk_level == "medium":
            return "flag", (
                f"Medium-risk indicators of '{threat_type}' detected. "
                f"Requires review. Matched: {matched_patterns[:3]}"
            )

        # low risk with some patterns
        return "allow", (
            f"Low-risk indicators noted for '{threat_type}' (confidence "
            f"{confidence:.2f}). Allowed with note."
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def input_hash(text: str) -> str:
        """Return a SHA-256 hex digest of the original input (for logging)."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
