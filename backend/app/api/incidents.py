"""Incidents router: full CRUD + analyze trigger."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.security import get_current_user
from app.models.event import AgentRun, AgentRunStatus
from app.models.incident import Incident, IncidentCategory, IncidentSeverity, IncidentStatus
from app.models.user import User

router = APIRouter(prefix="/incidents", tags=["incidents"])


# ---- Schemas ----

class IncidentCreate(BaseModel):
    title: str
    description: str
    category: IncidentCategory = IncidentCategory.other
    severity: IncidentSeverity = IncidentSeverity.medium
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    language: str = "en"
    source: str = "manual"


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[IncidentCategory] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None


class IncidentResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    organization_id: Optional[str]
    title: str
    description: str
    category: str
    severity: str
    status: str
    latitude: Optional[float]
    longitude: Optional[float]
    district: Optional[str]
    language: str
    source: str
    is_synthetic: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime


# ---- ID counter (simple in-memory sequential for demo; persistent via DB query) ----

async def _next_incident_id(db: AsyncSession) -> str:
    result = await db.execute(select(func.count()).select_from(Incident))
    count = result.scalar_one() or 0
    return f"INC-{(count + 1):04d}"


# ---- Routes ----

@router.get("", response_model=list[IncidentResponse])
async def list_incidents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[IncidentStatus] = None,
    district: Optional[str] = None,
    category: Optional[IncidentCategory] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Incident).order_by(Incident.created_at.desc())
    if status:
        q = q.where(Incident.status == status)
    if district:
        q = q.where(Incident.district == district)
    if category:
        q = q.where(Incident.category == category)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    payload: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    incident_id = await _next_incident_id(db)
    incident = Incident(
        id=incident_id,
        organization_id=current_user.organization_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        severity=payload.severity,
        status=IncidentStatus.received,
        latitude=payload.latitude,
        longitude=payload.longitude,
        district=payload.district,
        language=payload.language,
        source=payload.source,
        is_synthetic=False,
        created_by=current_user.id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(incident)
    await db.flush()
    await db.refresh(incident)
    return incident


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise NotFoundError(f"Incident {incident_id} not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise NotFoundError(f"Incident {incident_id} not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(incident, field, value)
    incident.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(incident)
    return incident


@router.delete("/{incident_id}", status_code=204)
async def delete_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise NotFoundError(f"Incident {incident_id} not found")
    await db.delete(incident)


@router.post("/{incident_id}/analyze")
async def analyze_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Triggers the multi-agent investigation workflow:
    SecureAI Guardian -> Triage -> Knowledge Grid & Risk Agent -> WorkforceOS -> Response Agent -> Human Approval Gate.
    """
    from app.services.incident_service import incident_analysis_service

    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise NotFoundError(f"Incident {incident_id} not found")

    workflow_state = await incident_analysis_service.analyze_incident(
        incident_id=incident_id,
        db=db,
    )

    return {
        "workflow_id": workflow_state.workflow_id,
        "incident_id": incident_id,
        "status": workflow_state.status,
        "current_step": workflow_state.current_step,
        "completed_steps": workflow_state.completed_steps,
        "agent_results": workflow_state.agent_results,
        "approval_id": workflow_state.approval_id,
    }


@router.get("/{incident_id}/risk")
async def get_incident_risk(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the computed risk assessment for an incident."""
    from app.models.event import RiskAssessment

    stmt = select(RiskAssessment).where(RiskAssessment.incident_id == incident_id).order_by(RiskAssessment.created_at.desc()).limit(1)
    res = await db.execute(stmt)
    ra = res.scalar_one_or_none()
    if ra:
        return {
            "incident_id": incident_id,
            "risk_score": ra.score,
            "risk_level": ra.risk_level.value if hasattr(ra.risk_level, "value") else str(ra.risk_level),
            "method": ra.model_version,
            "factors": ra.factors_json or {},
            "missing_indicators": ra.missing_factors_json or [],
            "limitations": ra.limitations_json or [],
        }

    # If no risk assessment calculated yet, calculate on the fly
    from app.agents.base import AgentInput
    from app.agents.risk import RiskAgent
    risk_agent = RiskAgent()

    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise NotFoundError(f"Incident {incident_id} not found")

    inp = AgentInput(
        incident_id=incident_id,
        workflow_id="RISK-DIRECT",
        context={"incident": {"district": incident.district or "Sunamganj", "category": incident.category.value, "severity": incident.severity.value}},
    )
    output = await risk_agent.execute(inp, db)
    return output.result

