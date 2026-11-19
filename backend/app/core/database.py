"""SQLAlchemy async database engine and session dependency."""
from __future__ import annotations

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


def _get_engine():
    db_url = settings.database_url
    # Ensure data directory exists for SQLite
    if "sqlite" in db_url:
        db_path_str = db_url.split("///")[-1]
        db_path = Path(db_path_str)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_async_engine(
        db_url,
        echo=settings.app_env == "development",
        connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    )


engine = _get_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_tables() -> None:
    """Create all database tables."""
    # Import all models so they are registered with Base
    import app.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: provides an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
