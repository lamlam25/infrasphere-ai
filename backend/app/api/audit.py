"""
Audit & Governance Router: Tamper-evident hash chain inspection
and cryptographic verification.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import verify_audit_chain
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.event import AuditEvent
from app.models.user import User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events")
async def list_audit_events(
    limit: int = Query(50, ge=1, le=200),
    actor: Optional[str] = None,
    event_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve audit events in reverse chronological order."""
    stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    if actor:
        stmt = stmt.where(AuditEvent.actor == actor)
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type)

    res = await db.execute(stmt)
    events = res.scalars().all()
    return [
        {
            "id": e.id,
            "actor": e.actor,
            "event_type": e.event_type,
            "entity_type": e.entity_type,
            "entity_id": e.entity_id,
            "previous_hash": e.previous_hash,
            "event_hash": e.event_hash,
            "payload": e.payload_json or {},
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/verify")
async def verify_audit_trail(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cryptographically verify the entire audit event hash chain from genesis to head.
    Hi = SHA256(Hi-1 || CanonicalJSON(Event_i))
    """
    verification_result = await verify_audit_chain(db)
    return {
        "verified": verification_result.get("valid", True),
        "events_checked": verification_result.get("events_checked", 0),
        "first_invalid_event": verification_result.get("first_invalid", None),
        "tampering_detected": not verification_result.get("valid", True),
        "algorithm": "SHA-256",
        "message": "Audit chain verified intact with zero tampering detected." if verification_result.get("valid", True) else "Audit chain integrity failed!",
    }
