"""SQLAlchemy Agent model."""
from __future__ import annotations

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Enum, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AgentType(str, PyEnum):
    security_guardian = "security_guardian"
    triage = "triage"
    knowledge = "knowledge"
    risk = "risk"
    workforce = "workforce"
    response = "response"
    supervisor = "supervisor"


class AgentStatus(str, PyEnum):
    active = "active"
    inactive = "inactive"
    paused = "paused"


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    agent_type: Mapped[AgentType] = mapped_column(
        Enum(AgentType), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus), nullable=False, default=AgentStatus.active
    )
    permissions_json: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    capabilities_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)

    runs: Mapped[list] = relationship("AgentRun", back_populates="agent", lazy="select")
