"""
WorkforceOS: Task Decomposition Engine.
Decomposes complex operational incidents into structured, prioritized subtasks
with dependency graphs.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SubtaskDefinition(BaseModel):
    id: str = Field(default_factory=lambda: f"TASK-{uuid.uuid4().hex[:6].upper()}")
    title: str
    description: str
    priority: str = "medium"  # low, medium, high, critical
    required_skills: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    suggested_assignee_type: str = "team"  # agent or team


class TaskDecomposer:
    """
    Decomposes an incident into structured subtasks based on incident category,
    severity, and district context.
    """

    DECOMPOSITION_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
        "flooding": [
            {
                "offset_id": 1,
                "title": "Verify Ground Coordinates & Water Logging Extent",
                "description": "Cross-reference reported location coordinates with survey points and verify inundation perimeter.",
                "priority": "high",
                "required_skills": ["gis_mapping", "field_inspection"],
                "dep_offsets": [],
            },
            {
                "offset_id": 2,
                "title": "Historical Incident & Drainage Pattern Analysis",
                "description": "Analyze past monsoon flood reports for this catchment basin and identify recurring choke points.",
                "priority": "medium",
                "required_skills": ["hydrological_analysis", "data_analysis"],
                "dep_offsets": [],
            },
            {
                "offset_id": 3,
                "title": "Downstream Road & Culvert Structural Integrity Inspection",
                "description": "Inspect structural integrity of culverts, bridge abutments, and road embankment stability.",
                "priority": "critical",
                "required_skills": ["structural_engineering", "bridge_inspection"],
                "dep_offsets": [1],
            },
            {
                "offset_id": 4,
                "title": "Emergency Traffic Diversion & Warning Notification",
                "description": "Establish temporary warning signage and deploy barricades for submerged carriageway.",
                "priority": "critical",
                "required_skills": ["traffic_management", "emergency_response"],
                "dep_offsets": [1],
            },
            {
                "offset_id": 5,
                "title": "Mobile Drainage Pump Deployment Coordination",
                "description": "Identify available high-capacity dewatering pumps and dispatch maintenance personnel.",
                "priority": "high",
                "required_skills": ["heavy_machinery", "dewatering"],
                "dep_offsets": [1, 2],
            },
            {
                "offset_id": 6,
                "title": "Post-Action Infrastructure Damage Assessment Report",
                "description": "Synthesize field observations, flood recession telemetry, and formulate repair budget estimates.",
                "priority": "medium",
                "required_skills": ["civil_engineering", "reporting"],
                "dep_offsets": [3, 5],
            },
        ],
        "road_damage": [
            {
                "offset_id": 1,
                "title": "Carriageway Pavement Damage Survey",
                "description": "Assess pothole depth, sub-base erosion, and asphalt cracking extent.",
                "priority": "high",
                "required_skills": ["road_maintenance", "field_inspection"],
                "dep_offsets": [],
            },
            {
                "offset_id": 2,
                "title": "Traffic Safety Containment",
                "description": "Deploy safety cones, detour signs, and reduce vehicle speed limits.",
                "priority": "high",
                "required_skills": ["traffic_management"],
                "dep_offsets": [1],
            },
            {
                "offset_id": 3,
                "title": "Patching & Resurfacing Material Dispatch",
                "description": "Mobilize cold-mix asphalt, bitumen emulsion, and roller equipment.",
                "priority": "medium",
                "required_skills": ["heavy_machinery", "asphalt_laying"],
                "dep_offsets": [1],
            },
        ],
        "bridge_damage": [
            {
                "offset_id": 1,
                "title": "Abutment & Pier Scour Inspection",
                "description": "Sonar and visual inspection of underwater piers and foundation soil erosion.",
                "priority": "critical",
                "required_skills": ["bridge_inspection", "structural_engineering"],
                "dep_offsets": [],
            },
            {
                "offset_id": 2,
                "title": "Load-Bearing Capacity Verification",
                "description": "Measure beam deflection and establish temporary axle weight restrictions.",
                "priority": "critical",
                "required_skills": ["structural_engineering"],
                "dep_offsets": [1],
            },
            {
                "offset_id": 3,
                "title": "Structural Repair & Shoring Coordination",
                "description": "Coordinate structural shoring crews and hydraulic jack placement.",
                "priority": "high",
                "required_skills": ["heavy_construction"],
                "dep_offsets": [2],
            },
        ],
        "default": [
            {
                "offset_id": 1,
                "title": "Initial On-Site Technical Verification",
                "description": "Deploy nearest response unit to verify reported infrastructure conditions.",
                "priority": "medium",
                "required_skills": ["field_inspection"],
                "dep_offsets": [],
            },
            {
                "offset_id": 2,
                "title": "Operational Risk Assessment & Resource Allocation",
                "description": "Analyze technical severity and schedule necessary repair teams.",
                "priority": "medium",
                "required_skills": ["operations_management"],
                "dep_offsets": [1],
            },
        ],
    }

    def decompose(self, incident: Dict[str, Any]) -> List[SubtaskDefinition]:
        category = incident.get("category", "default").lower()
        if category not in self.DECOMPOSITION_TEMPLATES:
            category = "default"

        templates = self.DECOMPOSITION_TEMPLATES[category]
        generated_tasks: List[SubtaskDefinition] = []
        id_map: Dict[int, str] = {}

        # First pass: generate task IDs
        for t in templates:
            task_id = f"TASK-{uuid.uuid4().hex[:6].upper()}"
            id_map[t["offset_id"]] = task_id

        # Second pass: assemble definitions with real dependency IDs
        district = incident.get("district", "the area")
        for t in templates:
            deps = [id_map[d] for d in t["dep_offsets"] if d in id_map]
            title = f"{t['title']} — {district}"
            task = SubtaskDefinition(
                id=id_map[t["offset_id"]],
                title=title,
                description=t["description"],
                priority=incident.get("severity", t["priority"]),
                required_skills=t["required_skills"],
                dependencies=deps,
                suggested_assignee_type="team",
            )
            generated_tasks.append(task)

        return generated_tasks
