"""
WorkforceOS Router: AI Agent Registry, Human Team Registry,
Task Board, and Candidate Assignment.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import get_current_user, require_role
from app.models.agent import Agent
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.team import Team, TeamSkill
from app.models.user import User
from app.workforce.assignment_engine import AssignmentEngine

router = APIRouter(tags=["workforce"])
assignment_engine = AssignmentEngine()


class TaskCreate(BaseModel):
    incident_id: str
    title: str
    description: str
    priority: str = "medium"
    assigned_team_id: Optional[str] = None
    dependencies: List[str] = []


class AssignRequest(BaseModel):
    team_id: str


@router.get("/agents")
async def list_agents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all registered AI agents, capabilities, and permissions."""
    res = await db.execute(select(Agent))
    agents = res.scalars().all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "agent_type": a.agent_type.value if hasattr(a.agent_type, "value") else str(a.agent_type),
            "description": a.description,
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
            "permissions": a.permissions_json or [],
            "capabilities": a.capabilities_json or [],
        }
        for a in agents
    ]


@router.get("/teams")
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all human field response teams and their skills."""
    res = await db.execute(select(Team))
    teams = res.scalars().all()
    results = []
    for t in teams:
        res_skills = await db.execute(select(TeamSkill).where(TeamSkill.team_id == t.id))
        skills = res_skills.scalars().all()
        results.append({
            "id": t.id,
            "name": t.name,
            "zone": t.zone,
            "status": t.status.value if hasattr(t.status, "value") else str(t.status),
            "skills": [
                {"skill": s.skill, "proficiency": s.proficiency}
                for s in skills
            ],
        })
    return results


@router.get("/tasks")
async def list_tasks(
    incident_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List operational tasks, filterable by incident and status."""
    stmt = select(Task).order_by(Task.created_at.desc())
    if incident_id:
        stmt = stmt.where(Task.incident_id == incident_id)
    if status:
        try:
            stmt = stmt.where(Task.status == TaskStatus(status.lower()))
        except ValueError:
            pass

    res = await db.execute(stmt)
    tasks = res.scalars().all()
    return [
        {
            "id": t.id,
            "incident_id": t.incident_id,
            "title": t.title,
            "description": t.description,
            "priority": t.priority.value if hasattr(t.priority, "value") else str(t.priority),
            "status": t.status.value if hasattr(t.status, "value") else str(t.status),
            "assigned_team_id": t.assigned_team_id,
            "assigned_agent_id": t.assigned_agent_id,
            "dependencies": t.dependencies or [],
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tasks
    ]


@router.post("/tasks")
async def create_task(
    req: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("analyst", "manager", "admin")),
):
    """Manually create an operational task."""
    task_id = f"TASK-{uuid.uuid4().hex[:6].upper()}"
    task = Task(
        id=task_id,
        incident_id=req.incident_id,
        title=req.title,
        description=req.description,
        priority=TaskPriority(req.priority.lower()) if req.priority.lower() in [p.value for p in TaskPriority] else TaskPriority.medium,
        status=TaskStatus.pending,
        assigned_team_id=req.assigned_team_id,
        dependencies=req.dependencies,
    )
    db.add(task)
    await db.commit()
    return {"success": True, "task_id": task_id, "status": "pending"}


@router.post("/tasks/{id}/assign")
async def assign_task(
    id: str,
    req: AssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    """Assign or reassign an operational task to a response team."""
    res = await db.execute(select(Task).where(Task.id == id))
    task = res.scalar_one_or_none()
    if not task:
        raise NotFoundError(f"Task '{id}' not found")

    task.assigned_team_id = req.team_id
    task.status = TaskStatus.in_progress
    await db.commit()

    return {"success": True, "task_id": id, "assigned_team_id": req.team_id, "status": "in_progress"}
