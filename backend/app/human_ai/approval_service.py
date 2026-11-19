"""
Human+AI: Approval Service.
Manages the human-in-the-loop governance boundary.
Guarantees that no autonomous agent can self-approve public infrastructure actions.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit import create_audit_event
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.approval import Approval, ApprovalStatus
from app.models.incident import Incident, IncidentStatus

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    Orchestrates human review, decision logging, and audit hash-chain updates.
    """

    async def get_approval(self, db: AsyncSession, approval_id: str) -> Approval:
        res = await db.execute(select(Approval).where(Approval.id == approval_id))
        appr = res.scalar_one_or_none()
        if not appr:
            raise NotFoundError(f"Approval request '{approval_id}' not found")
        return appr

    async def list_approvals(self, db: AsyncSession, status_filter: Optional[str] = None) -> list[Approval]:
        stmt = select(Approval).order_by(Approval.created_at.desc())
        if status_filter:
            try:
                st = ApprovalStatus(status_filter.lower())
                stmt = stmt.where(Approval.status == st)
            except ValueError:
                pass
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def process_decision(
        self,
        db: AsyncSession,
        approval_id: str,
        reviewer_id: str,
        reviewer_role: str,
        decision: str,  # approved, rejected, needs_revision
        comment: str = "",
    ) -> Dict[str, Any]:
        """
        Processes human decision:
        - Verifies manager/admin role
        - Verifies approval is PENDING
        - Atomically transitions approval + incident state
        - Appends to SHA-256 tamper-evident audit log
        """
        if reviewer_role not in ["manager", "admin"]:
            raise ForbiddenError("Only users with 'manager' or 'admin' roles can approve or reject recommendations")

        approval = await self.get_approval(db, approval_id)

        if approval.status != ApprovalStatus.pending:
            raise ValidationError(f"Approval is already resolved (status: {approval.status.value})")

        decision_clean = decision.lower().strip()
        if decision_clean == "approved":
            new_approval_status = ApprovalStatus.approved
            new_incident_status = IncidentStatus.approved
        elif decision_clean == "rejected":
            new_approval_status = ApprovalStatus.rejected
            new_incident_status = IncidentStatus.rejected
        elif decision_clean in ["needs_revision", "revision"]:
            new_approval_status = ApprovalStatus.needs_revision
            new_incident_status = IncidentStatus.analyzing
        else:
            raise ValidationError(f"Invalid decision '{decision}'. Choose: approved, rejected, needs_revision")

        now = datetime.now(timezone.utc)
        approval.status = new_approval_status
        approval.reviewer_id = reviewer_id
        approval.comment = comment
        approval.reviewed_at = now
        approval.version += 1

        # Update incident status
        await db.execute(
            update(Incident)
            .where(Incident.id == approval.incident_id)
            .values(status=new_incident_status, updated_at=now)
        )

        # Append to SHA-256 tamper-evident audit log
        audit_payload = {
            "approval_id": approval_id,
            "incident_id": approval.incident_id,
            "decision": decision_clean,
            "comment": comment,
            "reviewer_role": reviewer_role,
            "timestamp": now.isoformat(),
        }
        audit_event = await create_audit_event(
            db=db,
            actor=reviewer_id,
            event_type="human_approval_decision",
            entity_type="approval",
            entity_id=approval_id,
            payload_json=audit_payload,
        )

        await db.commit()

        logger.info(
            f"Approval {approval_id} for Incident {approval.incident_id} was {decision_clean} by {reviewer_id}"
        )

        return {
            "approval_id": approval_id,
            "incident_id": approval.incident_id,
            "decision": decision_clean,
            "status": new_approval_status.value,
            "incident_status": new_incident_status.value,
            "reviewed_by": reviewer_id,
            "reviewed_at": now.isoformat(),
            "audit_hash": audit_event.event_hash,
            "previous_hash": audit_event.previous_hash,
        }

    async def record_feedback(
        self,
        db: AsyncSession,
        approval_id: str,
        user_id: str,
        feedback: Dict[str, Any],
    ) -> Dict[str, Any]:
        approval = await self.get_approval(db, approval_id)
        # Store feedback in audit chain for future evaluation
        audit_event = await create_audit_event(
            db=db,
            actor=user_id,
            event_type="recommendation_feedback",
            entity_type="approval",
            entity_id=approval_id,
            payload_json=feedback,
        )
        await db.commit()
        return {"status": "success", "audit_hash": audit_event.event_hash}


approval_service = ApprovalService()
