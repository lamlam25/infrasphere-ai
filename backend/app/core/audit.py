"""Tamper-evident audit log with SHA-256 hash chain."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import AuditEvent


def _canonical_json(d: dict) -> str:
    return json.dumps(d, sort_keys=True, separators=(",", ":"), default=str)


def _compute_hash(previous_hash: str, event_dict: dict) -> str:
    raw = previous_hash + _canonical_json(event_dict)
    return hashlib.sha256(raw.encode()).hexdigest()


async def _get_last_hash(db: AsyncSession) -> str:
    result = await db.execute(
        select(AuditEvent.event_hash).order_by(AuditEvent.created_at.desc()).limit(1)
    )
    row = result.scalar_one_or_none()
    return row or "0" * 64  # genesis hash


async def create_audit_event(
    db: AsyncSession,
    actor: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    payload_json: dict[str, Any],
) -> AuditEvent:
    previous_hash = await _get_last_hash(db)
    now = datetime.now(timezone.utc)
    ts_str = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    event_dict = {
        "actor": actor,
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload": payload_json,
        "created_at": ts_str,
    }
    event_hash = _compute_hash(previous_hash, event_dict)

    audit_event = AuditEvent(
        actor=actor,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_hash=previous_hash,
        event_hash=event_hash,
        payload_json=payload_json,
        created_at=now,
    )
    db.add(audit_event)
    await db.flush()
    return audit_event


async def verify_audit_chain(db: AsyncSession) -> dict[str, Any]:
    result = await db.execute(
        select(AuditEvent).order_by(AuditEvent.created_at.asc())
    )
    events = result.scalars().all()

    if not events:
        return {"valid": True, "events_checked": 0, "broken_at": None}

    genesis = "0" * 64
    previous_hash = genesis
    broken_at = None

    for idx, event in enumerate(events):
        ts_str = (
            event.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
            if hasattr(event.created_at, "strftime")
            else str(event.created_at)[:19] + "Z"
        )
        event_dict = {
            "actor": event.actor,
            "event_type": event.event_type,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "payload": event.payload_json,
            "created_at": ts_str,
        }
        expected_hash = _compute_hash(previous_hash, event_dict)
        if expected_hash != event.event_hash or previous_hash != event.previous_hash:
            broken_at = idx
            break
        previous_hash = event.event_hash

    return {
        "valid": broken_at is None,
        "events_checked": len(events),
        "broken_at": broken_at,
    }

