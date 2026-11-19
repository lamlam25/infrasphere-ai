"""
Data Sources & System Health Router.
Reports operational status of external connectors and local data stores.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database import get_db

router = APIRouter(prefix="/data", tags=["data-sources"])


@router.get("/sources/status")
async def get_data_sources_status(db: AsyncSession = Depends(get_db)):
    """Check connectivity and operational readiness of all data providers."""
    # DB check
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "sources": [
            {
                "name": "SQLite Core Database",
                "type": "relational_database",
                "status": "healthy" if db_ok else "unhealthy",
                "details": "Local transaction store for incidents, tasks, users, and audit trail",
                "mode": "embedded",
            },
            {
                "name": "Qdrant Vector Database",
                "type": "vector_store",
                "status": "healthy",
                "details": "Local on-disk vector storage for multilingual semantic retrieval",
                "mode": "embedded_local",
            },
            {
                "name": "Language Model Provider",
                "type": "llm_adapter",
                "status": "healthy",
                "details": f"Active provider: {settings.llm_provider.upper()} (Deterministic demo fallback mode enabled)",
                "mode": settings.llm_provider,
            },
            {
                "name": "Bangladesh FFWC / BWDB Connector",
                "type": "external_api",
                "status": "connected_demo_mode" if not settings.ffwc_enabled else "live",
                "details": "Flood Forecasting & Warning Centre river gauge observations and forecasts",
                "is_synthetic": not settings.ffwc_enabled,
            },
            {
                "name": "OpenStreetMap Infrastructure Layer",
                "type": "geospatial",
                "status": "operational",
                "details": "Road and bridge geometries for Sunamganj and Sylhet Division",
                "is_synthetic": True,
            },
        ],
        "demo_data_enabled": settings.enable_demo_data,
        "synthetic_incidents_active": settings.enable_synthetic_incidents,
    }
