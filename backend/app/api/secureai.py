"""
SecureAI Router: Threat inspection, prompt testing laboratory,
security events, policy inspection, and threat metrics.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.event import SecurityEvent, SecurityEventAction, SecurityEventSeverity
from app.models.user import User
from app.secureai.prompt_guard import PromptGuard
from app.secureai.tool_policy import ToolPolicyEngine, AGENT_PERMISSIONS

router = APIRouter(prefix="/security", tags=["secureai"])
prompt_guard = PromptGuard()
tool_policy_engine = ToolPolicyEngine()


class InspectRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None


class InspectResponse(BaseModel):
    threat_type: str
    risk_level: str
    confidence: float
    action: str
    reason: str
    matched_patterns: List[str]
    detection_method: str
    is_safe: bool


@router.post("/inspect", response_model=InspectResponse)
async def inspect_input(
    req: InspectRequest,
    current_user: User = Depends(get_current_user),
):
    """Inspect text in production flow."""
    res = prompt_guard.inspect(req.text, req.context)
    return InspectResponse(
        threat_type=res.threat_type,
        risk_level=res.risk_level,
        confidence=res.confidence,
        action=res.action,
        reason=res.reason,
        matched_patterns=res.matched_patterns,
        detection_method=res.detection_method,
        is_safe=(res.action == "allow"),
    )


@router.post("/test", response_model=InspectResponse)
async def test_prompt(
    req: InspectRequest,
    current_user: User = Depends(require_role("analyst", "manager", "admin", "ai_auditor")),
):
    """
    Security Test Laboratory endpoint.
    Explicitly labeled safe testing environment for red-teaming prompts.
    """
    res = prompt_guard.inspect(req.text, req.context)
    return InspectResponse(
        threat_type=res.threat_type,
        risk_level=res.risk_level,
        confidence=res.confidence,
        action=res.action,
        reason=res.reason,
        matched_patterns=res.matched_patterns,
        detection_method=res.detection_method,
        is_safe=(res.action == "allow"),
    )


@router.get("/events")
async def list_security_events(
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List recent security events and quarantine alerts."""
    stmt = select(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).limit(limit)
    if severity:
        try:
            stmt = stmt.where(SecurityEvent.severity == SecurityEventSeverity(severity.lower()))
        except ValueError:
            pass
    if action:
        try:
            stmt = stmt.where(SecurityEvent.action == SecurityEventAction(action.lower()))
        except ValueError:
            pass
    res = await db.execute(stmt)
    events = res.scalars().all()
    return [
        {
            "id": e.id,
            "actor_id": e.actor_id,
            "agent_id": e.agent_id,
            "threat_type": e.threat_type,
            "severity": e.severity.value if hasattr(e.severity, "value") else str(e.severity),
            "action": e.action.value if hasattr(e.action, "value") else str(e.action),
            "input_hash": e.input_hash,
            "metadata": e.metadata_json or {},
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
        }
        for e in events
    ]


@router.get("/metrics")
async def get_security_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Threat detection summary and metrics."""
    res = await db.execute(select(SecurityEvent))
    events = res.scalars().all()

    by_action = {"allow": 0, "flag": 0, "quarantine": 0, "block": 0}
    by_threat = {}
    by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}

    for e in events:
        act = e.action.value if hasattr(e.action, "value") else str(e.action)
        sev = e.severity.value if hasattr(e.severity, "value") else str(e.severity)
        thr = e.threat_type or "unknown"

        by_action[act] = by_action.get(act, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_threat[thr] = by_threat.get(thr, 0) + 1

    return {
        "total_events": len(events),
        "by_action": by_action,
        "by_severity": by_severity,
        "by_threat_type": by_threat,
        "blocked_threats_count": by_action.get("block", 0),
        "quarantined_count": by_action.get("quarantine", 0),
    }


@router.get("/policies")
async def get_tool_policies(
    current_user: User = Depends(get_current_user),
):
    """Retrieve the active agent tool permission matrix."""
    return {
        "policies": AGENT_PERMISSIONS,
        "enforcement_mode": "strict_whitelist",
        "description": "Every agent execution requires explicit tool permission validation prior to call dispatch.",
    }
