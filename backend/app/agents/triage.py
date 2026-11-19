"""TriageAgent: classifies incidents and extracts entities."""
from __future__ import annotations

import re
import time

from app.agents.base import AgentInput, AgentOutput, BaseAgent


# ---------------------------------------------------------------------------
# Training data: (text, label) – 50+ examples across 5 categories
# Includes English and Bangla transliteration
# ---------------------------------------------------------------------------
_TRAINING_DATA: list[tuple[str, str]] = [
    # flooding
    ("flood water road damage waterlogged", "flooding"),
    ("heavy rainfall flooding street submerged", "flooding"),
    ("water level rising inundation crops", "flooding"),
    ("flash flood village evacuation rescue", "flooding"),
    ("riverbank overflow breach embankment", "flooding"),
    ("bonna bari pani dobu", "flooding"),          # Bangla transliteration
    ("borsha pani jol bidhi", "flooding"),
    ("নদী বন্যা পানি ডুবে", "flooding"),
    ("water entered homes residents displaced", "flooding"),
    ("downstream flooding dam overflow", "flooding"),
    ("paddy fields submerged crop loss flood", "flooding"),
    # road_damage
    ("road pothole broken surface damaged", "road_damage"),
    ("highway crack erosion landslide road", "road_damage"),
    ("road collapse sinkhole vehicle damaged", "road_damage"),
    ("রাস্তা ভাঙা যানবাহন", "road_damage"),
    ("rasta vanga pothole khurra", "road_damage"),
    ("bituminous surface crack deterioration", "road_damage"),
    ("rural road washed away rain damage", "road_damage"),
    ("embankment road eroded broken", "road_damage"),
    ("asphalt pavement failure traffic", "road_damage"),
    ("road shoulder collapse vehicles stuck", "road_damage"),
    ("road damaged flooded washed carriageway", "road_damage"),
    # bridge_damage
    ("bridge crack damaged structural", "bridge_damage"),
    ("bridge pillar erosion foundation weak", "bridge_damage"),
    ("সেতু ভাঙা ক্ষতি", "bridge_damage"),
    ("setu vanga cracked pillar", "bridge_damage"),
    ("footbridge collapsed pedestrian danger", "bridge_damage"),
    ("culvert damaged blocked road crossing", "bridge_damage"),
    ("bridge railing missing unsafe condition", "bridge_damage"),
    ("bridge deck crack traffic suspension", "bridge_damage"),
    ("overpass structural integrity concern", "bridge_damage"),
    ("bridge flood damage scour foundation", "bridge_damage"),
    # drainage
    ("drainage blocked clogged overflow", "drainage"),
    ("drain sewer choke waterlogging urban", "drainage"),
    ("ড্রেন বন্ধ জলাবদ্ধতা", "drainage"),
    ("drain blocked garbage accumulation", "drainage"),
    ("stormwater drain overflowing market", "drainage"),
    ("canal siltation blocked flow", "drainage"),
    ("pipe burst sewer overflow road", "drainage"),
    ("drainage system choked monsoon flood", "drainage"),
    ("blocked culvert water stagnant", "drainage"),
    ("drainage maintenance required overflow", "drainage"),
    # water_supply
    ("water supply disruption pipe burst", "water_supply"),
    ("no water tap dry supply failure", "water_supply"),
    ("পানি সরবরাহ বন্ধ", "water_supply"),
    ("pani sorbarah bondo leakage", "water_supply"),
    ("contaminated water supply pipe leakage", "water_supply"),
    ("pump failure water treatment plant", "water_supply"),
    ("water main burst pressure drop", "water_supply"),
    ("borehole pump broken village water", "water_supply"),
    # other
    ("electricity power outage tower fallen", "other"),
    ("tree fallen road blockage storm", "other"),
    ("infrastructure damage general report", "other"),
    ("cyclone damage buildings roofs", "other"),
    ("landslide hill slope collapse", "other"),
]

_ENTITY_PATTERNS = {
    "severity_indicators": [
        r"\b(critical|severe|urgent|emergency|extreme|major)\b",
        r"\b(সংকটজনক|মারাত্মক|জরুরি)\b",
    ],
    "location_patterns": [
        r"\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\s+(?:district|upazila|union|village|city|town)\b",
        r"\b(?:district|upazila|union|village)\s+(?:of\s+)?([A-Z][a-z]+)\b",
    ],
    "infrastructure_types": [
        r"\b(bridge|road|highway|drain|canal|culvert|embankment|dam|pump|pipeline|sewer)\b",
    ],
}

# Map label to priority
_PRIORITY_MAP = {
    "flooding": "high",
    "bridge_damage": "high",
    "road_damage": "medium",
    "drainage": "medium",
    "water_supply": "medium",
    "other": "low",
}


class TriageAgent(BaseAgent):
    """Classifies incident, extracts entities, normalises location."""

    agent_type = "triage"

    def __init__(self):
        super().__init__()
        self.classifier = self._load_classifier()

    def _load_classifier(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import Pipeline
        from sklearn.svm import LinearSVC

        texts = [t for t, _ in _TRAINING_DATA]
        labels = [l for _, l in _TRAINING_DATA]

        pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)),
                ("clf", LinearSVC(C=1.0, max_iter=2000)),
            ]
        )
        pipeline.fit(texts, labels)
        return pipeline

    def _classify(self, text: str) -> str:
        try:
            label = self.classifier.predict([text])[0]
            return str(label)
        except Exception:
            return "other"

    def _extract_entities(self, text: str) -> dict:
        entities: dict = {
            "severity_indicators": [],
            "locations": [],
            "infrastructure_types": [],
        }

        for pattern in _ENTITY_PATTERNS["severity_indicators"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["severity_indicators"].extend(matches)

        for pattern in _ENTITY_PATTERNS["location_patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["locations"].extend(
                [m if isinstance(m, str) else m[0] for m in matches]
            )

        for pattern in _ENTITY_PATTERNS["infrastructure_types"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities["infrastructure_types"].extend(matches)

        # Deduplicate
        for k in entities:
            entities[k] = list(dict.fromkeys(entities[k]))

        return entities

    def execute(self, input: AgentInput, db=None) -> AgentOutput:
        self._start_timer()
        try:
            # Get incident description from context (populated by supervisor)
            incident_data = input.context.get("incident", {})
            title = incident_data.get("title", "")
            description = incident_data.get("description", "")
            district = incident_data.get("district", "")

            combined_text = f"{title} {description} {district}".strip()

            self._step_count += 1
            self._check_limits()

            category = self._classify(combined_text)
            self._record_tool_call("classify", {"text": combined_text[:100]}, category)

            self._step_count += 1
            entities = self._extract_entities(combined_text)
            self._record_tool_call("extract_entities", {}, entities)

            # Determine priority
            priority = _PRIORITY_MAP.get(category, "medium")

            # Severity from text signals
            severity = incident_data.get("severity", "medium")
            if entities["severity_indicators"]:
                severity = "high"

            result = {
                "category": category,
                "priority": priority,
                "severity": severity,
                "entities": entities,
                "district": district or (entities["locations"][0] if entities["locations"] else None),
                "infrastructure_types": entities["infrastructure_types"],
                "confidence": 0.85,
            }

            return AgentOutput(
                agent_type=self.agent_type,
                success=True,
                result=result,
                evidence=[f"Classified as '{category}' based on text analysis"],
                execution_time_ms=self._elapsed_ms(),
            )

        except RuntimeError as exc:
            return self._error_output(str(exc))
        except Exception as exc:
            return self._error_output(f"Triage agent error: {exc}")
