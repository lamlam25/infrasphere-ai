"""
Human+AI Router: Approval center, human review decisions,
and operator feedback collection.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.human_ai.approval_service import approval_service
from app.models.user import User

router = APIRouter(prefix="/approvals", tags=["approvals"])


class DecisionRequest(BaseModel):
    decision: str  # approved, rejected, needs_revision
    comment: str = ""


class FeedbackRequest(BaseModel):
    was_useful: bool
    evidence_relevant: bool
    assignment_suitable: bool
    corrections: Optional[str] = None
    rating: int = 5


@router.get("")
async def list_approvals(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List approvals queue with status filtering."""
    apprs = await approval_service.list_approvals(db, status)
    return [
        {
            "id": a.id,
            "incident_id": a.incident_id,
            "task_id": a.task_id,
            "status": a.status.value if hasattr(a.status, "value") else str(a.status),
            "recommendation": a.recommendation_json or {},
            "reviewer_id": a.reviewer_id,
            "comment": a.comment,
            "version": a.version,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None,
        }
        for a in apprs
    ]


@router.get("/{id}")
async def get_approval(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full recommendation and evidence dossier for a specific approval."""
    a = await approval_service.get_approval(db, id)
    return {
        "id": a.id,
        "incident_id": a.incident_id,
        "task_id": a.task_id,
        "status": a.status.value if hasattr(a.status, "value") else str(a.status),
        "recommendation": a.recommendation_json or {},
        "reviewer_id": a.reviewer_id,
        "comment": a.comment,
        "version": a.version,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "reviewed_at": a.reviewed_at.isoformat() if a.reviewed_at else None,
    }


@router.post("/{id}/decision")
async def submit_approval_decision(
    id: str,
    req: DecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    """
    Submit authorized human decision (Approve, Reject, or Request Revision).
    Enforces that AI agents cannot self-approve.
    """
    res = await approval_service.process_decision(
        db=db,
        approval_id=id,
        reviewer_id=current_user.id,
        reviewer_role=current_user.role.value,
        decision=req.decision,
        comment=req.comment,
    )
    return {"success": True, "data": res}


@router.post("/{id}/feedback")
async def submit_approval_feedback(
    id: str,
    req: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit post-review operator feedback for system evaluation dataset."""
    res = await approval_service.record_feedback(
        db=db,
        approval_id=id,
        user_id=current_user.id,
        feedback=req.model_dump(),
    )
    return {"success": True, "data": res}
