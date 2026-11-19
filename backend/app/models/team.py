"""SQLAlchemy Team and TeamSkill models."""
from __future__ import annotations

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TeamStatus(str, PyEnum):
    available = "available"
    busy = "busy"
    unavailable = "unavailable"


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    zone: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[TeamStatus] = mapped_column(
        Enum(TeamStatus), nullable=False, default=TeamStatus.available
    )

    skills: Mapped[list["TeamSkill"]] = relationship(
        "TeamSkill", back_populates="team", cascade="all, delete-orphan"
    )


class TeamSkill(Base):
    __tablename__ = "team_skills"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    team_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("teams.id"), nullable=False
    )
    skill: Mapped[str] = mapped_column(String(128), nullable=False)
    proficiency: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)

    team: Mapped["Team"] = relationship("Team", back_populates="skills")
