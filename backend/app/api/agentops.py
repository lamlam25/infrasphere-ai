"""
AgentOps Router: Agent lifecycle management, run tracing,
circuit breaker status, and observability metrics.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agentops.tracing import trace_manager
from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.security import get_current_user, require_role
from app.models.event import AgentEvent, AgentRun, AgentRunStatus
from app.models.user import User

router = APIRouter(tags=["agentops"])


@router.get("/agent-runs")
async def list_agent_runs(
    incident_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List agent execution runs with filtering."""
    stmt = select(AgentRun).order_by(AgentRun.started_at.desc()).limit(limit)
    if incident_id:
        stmt = stmt.where(AgentRun.incident_id == incident_id)
    if status:
        try:
            stmt = stmt.where(AgentRun.status == AgentRunStatus(status.lower()))
        except ValueError:
            pass

    res = await db.execute(stmt)
    runs = res.scalars().all()
    return [
        {
            "id": r.id,
            "incident_id": r.incident_id,
            "agent_id": r.agent_id,
            "workflow_id": r.workflow_id,
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "step_count": r.step_count,
            "retry_count": r.retry_count,
            "error_message": r.error_message,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in runs
    ]


@router.get("/agent-runs/{id}")
async def get_agent_run(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(AgentRun).where(AgentRun.id == id))
    run = res.scalar_one_or_none()
    if not run:
        raise NotFoundError(f"Agent run '{id}' not found")

    res_events = await db.execute(select(AgentEvent).where(AgentEvent.run_id == id))
    events = res_events.scalars().all()

    return {
        "id": run.id,
        "incident_id": run.incident_id,
        "agent_id": run.agent_id,
        "workflow_id": run.workflow_id,
        "status": run.status.value if hasattr(run.status, "value") else str(run.status),
        "step_count": run.step_count,
        "retry_count": run.retry_count,
        "error_message": run.error_message,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "payload": e.payload_json or {},
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ],
    }


@router.get("/agent-runs/{id}/traces")
async def get_run_traces(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve detailed execution trace spans for an agent run."""
    traces = trace_manager.get_traces_for_run(id)
    if not traces:
        # Fallback trace synthesized from run record
        res = await db.execute(select(AgentRun).where(AgentRun.id == id))
        run = res.scalar_one_or_none()
        if run:
            traces = [
                {
                    "span_id": f"SPAN-{run.id[-4:]}-1",
                    "run_id": run.id,
                    "agent_id": run.agent_id,
                    "operation": "agent_execution",
                    "status": "success" if run.status == AgentRunStatus.completed else "error",
                    "duration_ms": 180,
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                    "ended_at": run.completed_at.isoformat() if run.completed_at else None,
                }
            ]
    return traces


@router.post("/agent-runs/{id}/pause")
async def pause_agent_run(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    """Pause an active agent execution."""
    await db.execute(
        update(AgentRun)
        .where(AgentRun.id == id)
        .values(status=AgentRunStatus.paused)
    )
    await db.commit()
    return {"success": True, "run_id": id, "status": "paused"}


@router.post("/agent-runs/{id}/resume")
async def resume_agent_run(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    """Resume a paused agent execution."""
    await db.execute(
        update(AgentRun)
        .where(AgentRun.id == id)
        .values(status=AgentRunStatus.running)
    )
    await db.commit()
    return {"success": True, "run_id": id, "status": "running"}


@router.post("/agent-runs/{id}/cancel")
async def cancel_agent_run(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    """Cancel an agent execution."""
    await db.execute(
        update(AgentRun)
        .where(AgentRun.id == id)
        .values(status=AgentRunStatus.cancelled)
    )
    await db.commit()
    return {"success": True, "run_id": id, "status": "cancelled"}


@router.get("/agentops/metrics")
async def get_agentops_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated AgentOps telemetry and quality metrics."""
    res = await db.execute(select(AgentRun))
    runs = res.scalars().all()

    total = len(runs)
    completed = sum(1 for r in runs if r.status == AgentRunStatus.completed)
    failed = sum(1 for r in runs if r.status == AgentRunStatus.failed)
    paused = sum(1 for r in runs if r.status == AgentRunStatus.paused)
    circuit_broken = sum(1 for r in runs if r.status == AgentRunStatus.circuit_broken)

    success_rate = round((completed / total * 100), 1) if total > 0 else 100.0

    return {
        "total_runs": total,
        "completed": completed,
        "failed": failed,
        "paused": paused,
        "circuit_broken": circuit_broken,
        "success_rate_percent": success_rate,
        "average_duration_ms": 340,
        "estimated_llm_cost_usd": "0.00 (Mock provider active)",
        "circuit_breaker_thresholds": {
            "max_steps": 8,
            "max_retries": 2,
            "max_duration_seconds": 120,
            "max_repeated_calls": 3,
        },
    }
