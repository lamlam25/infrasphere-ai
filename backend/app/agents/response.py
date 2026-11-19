"""
ResponseAgent: Synthesizes all multi-agent investigative findings into an audited
evidence-based recommendation and packages it for Human+AI approval.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List
from pydantic import BaseModel

from app.agents.base import AgentInput, AgentOutput, BaseAgent

logger = logging.getLogger(__name__)


class ResponseAgent(BaseAgent):
    agent_type = "response"

    async def execute(self, agent_input: AgentInput, db=None) -> AgentOutput:
        start_time = time.perf_counter()
        self._step_count += 1
        self._check_limits()

        context = agent_input.context
        incident = context.get("incident", {})
        triage_res = context.get("triage", {})
        knowledge_res = context.get("knowledge", {})
        risk_res = context.get("risk", {})
        workforce_res = context.get("workforce", {})

        district = incident.get("district", "Sunamganj")
        category = triage_res.get("category", incident.get("category", "flooding"))
        risk_score = risk_res.get("risk_score", 65.0)
        risk_level = risk_res.get("risk_level", "high")

        # 1. Synthesize recommended actions
        recommended_actions = [
            {
                "action_id": "ACT-01",
                "title": f"Dispatch Immediate Inspection Unit to {district}",
                "priority": "critical" if risk_score >= 75 else "high",
                "description": f"Deploy {workforce_res.get('tasks', [{}])[0].get('recommended_team_name', 'rapid response unit')} to inspect carriageway stability and culvert flow.",
                "requires_approval": True,
            },
            {
                "action_id": "ACT-02",
                "title": "Establish Emergency Traffic Detour Signs",
                "priority": "high",
                "description": "Install reflective caution barricades 500m ahead of flooded section to prevent heavy vehicle stranding.",
                "requires_approval": True,
            },
            {
                "action_id": "ACT-03",
                "title": "Issue Internal Maintenance & Dewatering Pump Standby Order",
                "priority": "medium",
                "description": "Alert local Roads & Highways Department (RHD) pump stations for potential deployment.",
                "requires_approval": False,
            },
        ]

        # 2. Gather evidence from all agents
        evidence_list = []
        # Triage evidence
        evidence_list.append(f"Classification: {category.upper()} with severity {incident.get('severity', 'medium')}")
        # Knowledge evidence
        for src in knowledge_res.get("sources", []):
            evidence_list.append(f"Document [{src.get('document_id')} p.{src.get('page', 1)}]: {src.get('document_title')}")
        # Risk evidence
        evidence_list.append(f"Risk Assessment: Score {risk_score}/100 ({risk_level.upper()}) based on FFWC river gauge telemetry")
        # Workforce evidence
        evidence_list.append(f"Workforce Plan: {workforce_res.get('total_tasks', 0)} coordinated operational subtasks prepared")

        # 3. Create Approval record in DB if available
        approval_id = f"APR-{uuid.uuid4().hex[:6].upper()}"
        recommendation_payload = {
            "approval_id": approval_id,
            "incident_id": agent_input.incident_id,
            "summary": f"Prioritize immediate ground inspection and flood hazard containment for {district} road corridor.",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "category": category,
            "recommended_actions": recommended_actions,
            "evidence": evidence_list,
            "missing_information": risk_res.get("missing_indicators", ["live_rainfall"]),
            "limitations": [
                "AI-assisted prioritization recommendation. Does NOT autonomously alter road status or command public services.",
                "Certified field engineer must visually confirm structural integrity before re-opening traffic.",
            ],
            "status": "pending",
        }

        if db:
            try:
                from app.models.approval import Approval, ApprovalStatus
                approval_rec = Approval(
                    id=approval_id,
                    incident_id=agent_input.incident_id,
                    recommendation_json=recommendation_payload,
                    status=ApprovalStatus.pending,
                    version=1,
                )
                db.add(approval_rec)
                await db.commit()
            except Exception as e:
                logger.warning(f"Could not write approval to DB: {e}")

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        return AgentOutput(
            agent_type=self.agent_type,
            success=True,
            result=recommendation_payload,
            evidence=evidence_list,
            limitations=recommendation_payload["limitations"],
            execution_time_ms=elapsed_ms,
        )
