"""
WorkforceAgent: Coordinates human teams and AI agents.
Decomposes incident into subtasks and performs explainable multi-factor resource matching.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List
from sqlalchemy import select

from app.agents.base import AgentInput, AgentOutput, BaseAgent
from app.workforce.assignment_engine import AssignmentEngine
from app.workforce.task_decomposer import TaskDecomposer

logger = logging.getLogger(__name__)


class WorkforceAgent(BaseAgent):
    agent_type = "workforce"

    def __init__(self):
        super().__init__()
        self.decomposer = TaskDecomposer()
        self.assignment_engine = AssignmentEngine()

    async def execute(self, agent_input: AgentInput, db=None) -> AgentOutput:
        start_time = time.perf_counter()
        self._step_count += 1
        self._check_limits()

        incident = agent_input.context.get("incident", {})
        district = incident.get("district", "Sunamganj")

        # 1. Decompose incident into subtasks
        subtasks = self.decomposer.decompose(incident)
        self._record_tool_call(
            "decompose_incident_tasks",
            {"category": incident.get("category"), "district": district},
            f"Generated {len(subtasks)} subtasks"
        )

        # 2. Fetch available teams
        teams = await self._get_teams(db)

        # 3. Score and assign each task
        task_plans = []
        for task in subtasks:
            ranked_teams = self.assignment_engine.rank_teams(
                teams=teams,
                required_skills=task.required_skills,
                incident_district=district,
            )
            top_candidate = ranked_teams[0] if ranked_teams else None

            plan_entry = {
                "task_id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "required_skills": task.required_skills,
                "dependencies": task.dependencies,
                "recommended_team_id": top_candidate.team_id if top_candidate else None,
                "recommended_team_name": top_candidate.team_name if top_candidate else "Unassigned",
                "match_score": top_candidate.total_score if top_candidate else 0.0,
                "match_explanation": top_candidate.explanation if top_candidate else "No candidates available",
                "all_candidates": [
                    {
                        "team_id": c.team_id,
                        "team_name": c.team_name,
                        "score": c.total_score,
                        "matched_skills": c.matched_skills,
                    }
                    for c in ranked_teams[:3]
                ],
            }
            task_plans.append(plan_entry)

        # 4. If DB is provided, persist tasks as pending internal tasks
        if db:
            try:
                from app.models.task import Task, TaskPriority, TaskStatus
                for tp in task_plans:
                    db_task = Task(
                        id=tp["task_id"],
                        incident_id=agent_input.incident_id,
                        title=tp["title"],
                        description=tp["description"],
                        priority=TaskPriority(tp["priority"].lower()) if tp["priority"].lower() in [p.value for p in TaskPriority] else TaskPriority.medium,
                        status=TaskStatus.pending,
                        assigned_team_id=tp["recommended_team_id"],
                        dependencies=tp["dependencies"],
                    )
                    db.add(db_task)
                await db.commit()
            except Exception as e:
                logger.warning(f"Could not persist tasks to DB: {e}")

        result = {
            "incident_id": agent_input.incident_id,
            "total_tasks": len(task_plans),
            "tasks": task_plans,
            "assigned_teams_count": len(set(tp["recommended_team_id"] for tp in task_plans if tp["recommended_team_id"])),
            "scoring_formula": "Score = 0.40*S + 0.25*Z + 0.20*A + 0.15*L",
        }

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return AgentOutput(
            agent_type=self.agent_type,
            success=True,
            result=result,
            evidence=[f"Decomposed incident into {len(task_plans)} operational tasks with ranked team assignments."],
            limitations=["Task assignments are recommendations subject to supervisor review and human approval."],
            execution_time_ms=elapsed_ms,
        )

    async def _get_teams(self, db=None) -> List[Dict[str, Any]]:
        if db:
            try:
                from app.models.team import Team
                stmt = select(Team)
                res = await db.execute(stmt)
                teams = res.scalars().all()
                if teams:
                    team_list = []
                    for t in teams:
                        skills = [{"skill": ts.skill, "proficiency": ts.proficiency} for ts in (t.skills or [])]
                        team_list.append({
                            "id": t.id,
                            "name": t.name,
                            "zone": t.zone,
                            "status": t.status.value if hasattr(t.status, "value") else str(t.status),
                            "skills": skills,
                        })
                    return team_list
            except Exception as e:
                logger.warning(f"Failed to query teams: {e}")

        # Deterministic fallback teams representing Bangladesh infrastructure response units
        return [
            {
                "id": "TEAM-SYL-01",
                "name": "Sylhet Division Rapid Flood Response Team",
                "zone": "Sylhet",
                "status": "available",
                "skills": [
                    {"skill": "gis_mapping", "proficiency": 0.9},
                    {"skill": "field_inspection", "proficiency": 0.95},
                    {"skill": "dewatering", "proficiency": 0.85},
                    {"skill": "emergency_response", "proficiency": 0.9},
                ],
            },
            {
                "id": "TEAM-SUN-01",
                "name": "Sunamganj Haor Infrastructure Inspection Unit",
                "zone": "Sunamganj",
                "status": "available",
                "skills": [
                    {"skill": "field_inspection", "proficiency": 0.95},
                    {"skill": "bridge_inspection", "proficiency": 0.90},
                    {"skill": "structural_engineering", "proficiency": 0.85},
                    {"skill": "traffic_management", "proficiency": 0.80},
                ],
            },
            {
                "id": "TEAM-CTG-01",
                "name": "Chattogram Highway & Embankment Division",
                "zone": "Chattogram",
                "status": "available",
                "skills": [
                    {"skill": "road_maintenance", "proficiency": 0.95},
                    {"skill": "heavy_machinery", "proficiency": 0.90},
                    {"skill": "asphalt_laying", "proficiency": 0.90},
                ],
            },
            {
                "id": "TEAM-DHK-01",
                "name": "Central Engineering Corps - Dhaka",
                "zone": "Dhaka",
                "status": "available",
                "skills": [
                    {"skill": "structural_engineering", "proficiency": 0.95},
                    {"skill": "data_analysis", "proficiency": 0.90},
                    {"skill": "civil_engineering", "proficiency": 0.95},
                ],
            },
        ]
