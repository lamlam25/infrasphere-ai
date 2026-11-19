"""SQLAlchemy Asset model."""
from __future__ import annotations

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AssetType(str, PyEnum):
    road = "road"
    bridge = "bridge"
    drainage = "drainage"
    water_supply = "water_supply"
    other = "other"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType), nullable=False, default=AssetType.other
    )
    district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="manual", nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
