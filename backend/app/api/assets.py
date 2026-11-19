"""Assets router: full CRUD."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError
from app.core.security import get_current_user
from app.models.asset import Asset, AssetType
from app.models.user import User

router = APIRouter(prefix="/assets", tags=["assets"])


class AssetCreate(BaseModel):
    name: str
    asset_type: AssetType = AssetType.other
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    source: str = "manual"


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[AssetType] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None


class AssetResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    organization_id: Optional[str]
    name: str
    asset_type: str
    district: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    description: Optional[str]
    source: str
    is_synthetic: bool


async def _next_asset_id(db: AsyncSession) -> str:
    result = await db.execute(select(func.count()).select_from(Asset))
    count = result.scalar_one() or 0
    return f"ASSET-{(count + 1):04d}"


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    district: Optional[str] = None,
    asset_type: Optional[AssetType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Asset)
    if district:
        q = q.where(Asset.district == district)
    if asset_type:
        q = q.where(Asset.asset_type == asset_type)
    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("", response_model=AssetResponse, status_code=201)
async def create_asset(
    payload: AssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    asset_id = await _next_asset_id(db)
    asset = Asset(
        id=asset_id,
        organization_id=current_user.organization_id,
        name=payload.name,
        asset_type=payload.asset_type,
        district=payload.district,
        latitude=payload.latitude,
        longitude=payload.longitude,
        description=payload.description,
        source=payload.source,
        is_synthetic=False,
    )
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return asset


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise NotFoundError(f"Asset {asset_id} not found")
    return asset


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    payload: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise NotFoundError(f"Asset {asset_id} not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(asset, field, value)
    await db.flush()
    await db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise NotFoundError(f"Asset {asset_id} not found")
    await db.delete(asset)
