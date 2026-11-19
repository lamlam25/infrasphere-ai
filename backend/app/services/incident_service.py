"""
Incident Analysis Service: Orchestrates analysis of incidents using the supervisor
and broadcasts real-time telemetry over WebSockets.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.supervisor import Supervisor, WorkflowState
from app.core.exceptions import NotFoundError
from app.models.incident import Incident

logger = logging.getLogger(__name__)


class IncidentAnalysisService:
    def __init__(self):
        self.supervisor = Supervisor()

    async def analyze_incident(
        self,
        incident_id: str,
        db: AsyncSession,
        options: Optional[Dict[str, Any]] = None,
    ) -> WorkflowState:
        # 1. Fetch incident
        res = await db.execute(select(Incident).where(Incident.id == incident_id))
        inc = res.scalar_one_or_none()
        if not inc:
            raise NotFoundError(f"Incident '{incident_id}' not found")

        incident_dict = {
            "id": inc.id,
            "title": inc.title,
            "description": inc.description,
            "category": inc.category.value if hasattr(inc.category, "value") else str(inc.category),
            "severity": inc.severity.value if hasattr(inc.severity, "value") else str(inc.severity),
            "district": inc.district or "Sunamganj",
            "latitude": inc.latitude,
            "longitude": inc.longitude,
            "language": inc.language,
            "is_synthetic": inc.is_synthetic,
        }

        # 2. Execute multi-agent supervisor
        state = await self.supervisor.run_workflow(
            incident_id=incident_id,
            incident_dict=incident_dict,
            db=db,
        )

        return state


incident_analysis_service = IncidentAnalysisService()
