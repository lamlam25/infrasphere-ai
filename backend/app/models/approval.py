"""SQLAlchemy Approval model."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ApprovalStatus(str, PyEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    needs_revision = "needs_revision"
    cancelled = "cancelled"


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        String(16), ForeignKey("incidents.id"), nullable=False
    )
    task_id: Mapped[str | None] = mapped_column(
        String(16), ForeignKey("tasks.id"), nullable=True
    )
    recommendation_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.pending
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    incident: Mapped["Incident"] = relationship("Incident", back_populates="approvals")  # type: ignore[name-defined]
    reviewer: Mapped["User | None"] = relationship("User", back_populates="approvals")  # type: ignore[name-defined]
