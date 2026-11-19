"""SQLAlchemy event-related models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AgentRunStatus(str, PyEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    paused = "paused"
    cancelled = "cancelled"
    circuit_broken = "circuit_broken"


class SecurityEventSeverity(str, PyEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class SecurityEventAction(str, PyEnum):
    allow = "allow"
    flag = "flag"
    quarantine = "quarantine"
    block = "block"


class RiskLevel(str, PyEnum):
    low = "low"
    moderate = "moderate"
    high = "high"
    critical = "critical"


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    incident_id: Mapped[str | None] = mapped_column(
        String(16), ForeignKey("incidents.id"), nullable=True
    )
    agent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("agents.id"), nullable=True
    )
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(AgentRunStatus), nullable=False, default=AgentRunStatus.pending
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    step_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    workflow_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    incident: Mapped["Incident"] = relationship("Incident", back_populates="agent_runs")  # type: ignore[name-defined]
    agent: Mapped["Agent"] = relationship("Agent", back_populates="runs")  # type: ignore[name-defined]
    events: Mapped[list["AgentEvent"]] = relationship(
        "AgentEvent", back_populates="run", cascade="all, delete-orphan"
    )


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    run_id: Mapped[str] = mapped_column(
        String(16), ForeignKey("agent_runs.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="events")


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    agent_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    threat_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[SecurityEventSeverity] = mapped_column(
        Enum(SecurityEventSeverity), nullable=False, default=SecurityEventSeverity.low
    )
    action: Mapped[SecurityEventAction] = mapped_column(
        Enum(SecurityEventAction), nullable=False, default=SecurityEventAction.allow
    )
    input_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    actor: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    incident_id: Mapped[str] = mapped_column(
        String(16), ForeignKey("incidents.id"), nullable=False
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel), nullable=False, default=RiskLevel.low
    )
    model_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    factors_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    missing_factors_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    limitations_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    incident: Mapped["Incident"] = relationship("Incident", back_populates="risk_assessments")  # type: ignore[name-defined]


class StationObservation(Base):
    __tablename__ = "station_observations"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    station_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    station_name: Mapped[str] = mapped_column(String(128), nullable=False)
    district: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(16), default="m", nullable=False)
    danger_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(64), default="synthetic", nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(default=True, nullable=False)
