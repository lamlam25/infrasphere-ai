"""Metrics router: summary statistics."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.agent import Agent, AgentStatus
from app.models.approval import Approval, ApprovalStatus
from app.models.event import SecurityEvent
from app.models.incident import Incident, IncidentStatus
from app.models.user import User

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
async def metrics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Incidents by status
    inc_result = await db.execute(
        select(Incident.status, func.count().label("count"))
        .group_by(Incident.status)
    )
    incidents_by_status = {row.status.value: row.count for row in inc_result}

    # Total incidents
    total_result = await db.execute(select(func.count()).select_from(Incident))
    total_incidents = total_result.scalar_one()

    # Active agents
    agents_result = await db.execute(
        select(func.count()).select_from(Agent).where(Agent.status == AgentStatus.active)
    )
    active_agents = agents_result.scalar_one()

    # Pending approvals
    approvals_result = await db.execute(
        select(func.count()).select_from(Approval).where(
            Approval.status == ApprovalStatus.pending
        )
    )
    pending_approvals = approvals_result.scalar_one()

    # Recent security events (last 24h)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    sec_result = await db.execute(
        select(func.count()).select_from(SecurityEvent).where(
            SecurityEvent.timestamp >= since
        )
    )
    recent_security_events = sec_result.scalar_one()

    return {
        "total_incidents": total_incidents,
        "incidents_by_status": incidents_by_status,
        "active_agents": active_agents,
        "pending_approvals": pending_approvals,
        "recent_security_events_24h": recent_security_events,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
