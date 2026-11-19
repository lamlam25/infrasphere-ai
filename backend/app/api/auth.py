"""Auth router: login, logout, /me."""
from __future__ import annotations

from datetime import timedelta

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    organization_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "analyst"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserResponse] = None


@router.post("/register", response_model=TokenResponse)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    email_clean = str(payload.email).lower().strip()
    existing = await db.execute(select(User).where(User.email == email_clean))
    if existing.scalar_one_or_none():
        raise ConflictError(f"User with email '{email_clean}' already exists")

    if len(payload.password) < 6:
        raise ValidationError("Password must be at least 6 characters")

    try:
        user_role = UserRole(payload.role)
    except ValueError:
        user_role = UserRole.analyst

    new_user = User(
        email=email_clean,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip() or "National Operator",
        role=user_role,
        is_active=True,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token({"sub": new_user.id, "email": new_user.email, "role": new_user.role.value}, expires)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse(
            id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role.value,
            is_active=new_user.is_active,
            organization_id=new_user.organization_id,
        ),
    )



@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account deactivated")

    expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role.value}, expires)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            is_active=user.is_active,
            organization_id=user.organization_id,
        ),
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # Stateless JWT — just acknowledge
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        organization_id=current_user.organization_id,
    )
