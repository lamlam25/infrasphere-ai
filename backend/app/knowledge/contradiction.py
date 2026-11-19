"""
Contradiction and inconsistency detection for the Knowledge Grid.
Identifies conflicting claims about the same entity across different documents.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List


class ContradictionDetector:
    """
    Detects contradictory or inconsistent status claims about infrastructure assets.
    Example:
      Doc A: "Sunamganj Sadar Bridge inspection completed on 10 October 2024"
      Doc B: "Sunamganj Sadar Bridge inspection pending as of 15 October 2024"
    """

    # Antonym / conflicting status pairs
    CONFLICTING_STATUS_PAIRS = [
        ({"completed", "finished", "repaired", "cleared", "operational", "open"},
         {"pending", "delayed", "damaged", "blocked", "submerged", "closed", "unresolved"}),
        ({"safe", "stable", "normal"},
         {"danger", "critical", "compromised", "at risk", "flooded"}),
    ]

    def __init__(self):
        pass

    def detect(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scan chunks for contradictions regarding mentioned infrastructure assets.
        Returns list of detected contradictions with citations.
        """
        claims = []
        for chunk in chunks:
            extracted = self._extract_claims(chunk)
            claims.extend(extracted)

        contradictions = []
        # Group claims by entity
        by_entity: Dict[str, List[Dict[str, Any]]] = {}
        for claim in claims:
            ent = claim["entity"].lower().strip()
            by_entity.setdefault(ent, []).append(claim)

        for entity, entity_claims in by_entity.items():
            if len(entity_claims) < 2:
                continue
            for i in range(len(entity_claims)):
                for j in range(i + 1, len(entity_claims)):
                    c1 = entity_claims[i]
                    c2 = entity_claims[j]
                    if c1["document_id"] != c2["document_id"]:
                        if self._is_contradictory(c1["status"], c2["status"]):
                            contradictions.append({
                                "entity": entity.title(),
                                "claim_a": c1["statement"],
                                "doc_a": c1["document_id"],
                                "doc_a_title": c1.get("document_title", "Document A"),
                                "claim_b": c2["statement"],
                                "doc_b": c2["document_id"],
                                "doc_b_title": c2.get("document_title", "Document B"),
                                "status_a": c1["status"],
                                "status_b": c2["status"],
                                "severity": "high",
                                "requires_human_resolution": True,
                            })

        return contradictions

    def _extract_claims(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = chunk.get("content", "")
        doc_id = chunk.get("document_id", "UNKNOWN")
        doc_title = chunk.get("metadata", {}).get("title", doc_id) if isinstance(chunk.get("metadata"), dict) else doc_id

        # Regex to find: [Named Asset] [inspection/repair/work/status] is/was [completed/pending/...]
        pattern = re.compile(
            r"([A-Za-z\s]+(?:Bridge|Road|Culvert|Station|Embankment|Drainage))(?:\s+inspection|\s+repair|\s+status)?\s+(?:was|is|remains|has been)\s+([a-zA-Z]+)",
            re.IGNORECASE
        )

        claims = []
        for match in pattern.finditer(text):
            entity = match.group(1).strip()
            status = match.group(2).lower().strip()
            # grab surrounding sentence
            start = max(0, text.rfind(".", 0, match.start()) + 1)
            end = text.find(".", match.end())
            sentence = text[start:end + 1 if end != -1 else len(text)].strip()

            claims.append({
                "entity": entity,
                "status": status,
                "statement": sentence,
                "document_id": doc_id,
                "document_title": doc_title,
                "chunk_id": chunk.get("chunk_id", ""),
            })

        return claims

    def _is_contradictory(self, status_a: str, status_b: str) -> bool:
        for group_1, group_2 in self.CONFLICTING_STATUS_PAIRS:
            if (status_a in group_1 and status_b in group_2) or (status_a in group_2 and status_b in group_1):
                return True
        return False
