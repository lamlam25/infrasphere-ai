"""SQLAlchemy Incident model."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IncidentCategory(str, PyEnum):
    flooding = "flooding"
    road_damage = "road_damage"
    bridge_damage = "bridge_damage"
    drainage = "drainage"
    water_supply = "water_supply"
    other = "other"


class IncidentSeverity(str, PyEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentStatus(str, PyEnum):
    received = "received"
    analyzing = "analyzing"
    recommendation_ready = "recommendation_ready"
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    closed = "closed"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[IncidentCategory] = mapped_column(
        Enum(IncidentCategory), nullable=False, default=IncidentCategory.other
    )
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity), nullable=False, default=IncidentSeverity.medium
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus), nullable=False, default=IncidentStatus.received
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # relationships
    creator: Mapped["User"] = relationship("User", back_populates="incidents")  # type: ignore[name-defined]
    tasks: Mapped[list] = relationship("Task", back_populates="incident", lazy="select")
    approvals: Mapped[list] = relationship("Approval", back_populates="incident", lazy="select")
    agent_runs: Mapped[list] = relationship("AgentRun", back_populates="incident", lazy="select")
    risk_assessments: Mapped[list] = relationship("RiskAssessment", back_populates="incident", lazy="select")
