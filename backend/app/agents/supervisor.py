"""
Supervisor: Orchestrates the multi-agent workflow across all five pillars.
State machine:
RECEIVED -> SECURITY_CHECK -> TRIAGE -> INVESTIGATION (KNOWLEDGE + RISK)
-> WORKFORCE_DECOMPOSITION -> RECOMMENDATION -> PENDING_APPROVAL -> APPROVED / REJECTED
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, update

from app.agents.base import AgentInput, AgentOutput
from app.agents.knowledge import KnowledgeAgent
from app.agents.response import ResponseAgent
from app.agents.risk import RiskAgent
from app.agents.triage import TriageAgent
from app.agents.workforce import WorkforceAgent
from app.secureai.prompt_guard import PromptGuard

logger = logging.getLogger(__name__)


class WorkflowState(BaseModel):
    workflow_id: str
    incident_id: str
    status: str = "running"  # running, waiting_approval, completed, blocked, failed
    current_step: str = "security_check"
    completed_steps: List[str] = Field(default_factory=list)
    agent_results: Dict[str, Any] = Field(default_factory=dict)
    approval_id: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class Supervisor:
    """
    Controlled multi-agent supervisor orchestrator.
    Executes each specialized agent in sequence, enforcing tool policies,
    step limits, and recording full telemetry into AgentOps.
    """

    def __init__(self):
        self.prompt_guard = PromptGuard()
        self.triage_agent = TriageAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.risk_agent = RiskAgent()
        self.workforce_agent = WorkforceAgent()
        self.response_agent = ResponseAgent()

    async def run_workflow(self, incident_id: str, incident_dict: Dict[str, Any], db=None) -> WorkflowState:
        workflow_id = f"WF-{uuid.uuid4().hex[:6].upper()}"
        state = WorkflowState(
            workflow_id=workflow_id,
            incident_id=incident_id,
            current_step="security_check",
        )

        logger.info(f"Starting workflow {workflow_id} for incident {incident_id}")

        try:
            # -----------------------------------------------------------
            # STAGE 1: Security Guardian Check
            # -----------------------------------------------------------
            state.current_step = "security_check"
            content_to_check = f"{incident_dict.get('title', '')} {incident_dict.get('description', '')}"
            sec_result = self.prompt_guard.inspect(content_to_check)
            state.agent_results["security"] = {
                "action": sec_result.action,
                "threat_type": sec_result.threat_type,
                "risk_level": sec_result.risk_level,
                "confidence": sec_result.confidence,
                "reason": sec_result.reason,
            }

            # Record security event in DB if needed
            if db:
                await self._record_security_event(db, incident_id, sec_result, content_to_check)

            if sec_result.action == "block":
                state.status = "blocked"
                state.error = f"Security violation detected: {sec_result.reason}"
                logger.warning(f"Workflow {workflow_id} blocked by SecureAI: {sec_result.reason}")
                if db:
                    await self._update_incident_status(db, incident_id, "rejected")
                return state

            state.completed_steps.append("security_check")

            # -----------------------------------------------------------
            # STAGE 2: Incident Triage Agent
            # -----------------------------------------------------------
            state.current_step = "triage"
            triage_input = AgentInput(
                incident_id=incident_id,
                workflow_id=workflow_id,
                context={"incident": incident_dict},
            )
            triage_output = self.triage_agent.execute(triage_input, db)
            state.agent_results["triage"] = triage_output.result
            state.completed_steps.append("triage")
            await self._record_agent_run(db, workflow_id, incident_id, "triage_agent", triage_output)

            # Update incident with classification if improved
            incident_dict["category"] = triage_output.result.get("category", incident_dict.get("category"))
            incident_dict["severity"] = triage_output.result.get("severity", incident_dict.get("severity"))

            # -----------------------------------------------------------
            # STAGE 3: Knowledge Grid & Risk Assessment (Parallel conceptually)
            # -----------------------------------------------------------
            state.current_step = "investigation"
            # 3A: Knowledge Agent
            knowledge_input = AgentInput(
                incident_id=incident_id,
                workflow_id=workflow_id,
                context={"incident": incident_dict, "triage": triage_output.result},
            )
            knowledge_output = await self.knowledge_agent.execute(knowledge_input, db)
            state.agent_results["knowledge"] = knowledge_output.result
            await self._record_agent_run(db, workflow_id, incident_id, "knowledge_agent", knowledge_output)

            # 3B: Risk Agent
            risk_input = AgentInput(
                incident_id=incident_id,
                workflow_id=workflow_id,
                context={"incident": incident_dict, "triage": triage_output.result},
            )
            risk_output = await self.risk_agent.execute(risk_input, db)
            state.agent_results["risk"] = risk_output.result
            await self._record_agent_run(db, workflow_id, incident_id, "risk_agent", risk_output)

            # Record Risk Assessment in DB
            if db:
                await self._record_risk_assessment(db, incident_id, risk_output.result)

            state.completed_steps.append("investigation")

            # -----------------------------------------------------------
            # STAGE 4: WorkforceOS Coordination Agent
            # -----------------------------------------------------------
            state.current_step = "workforce_planning"
            workforce_input = AgentInput(
                incident_id=incident_id,
                workflow_id=workflow_id,
                context={
                    "incident": incident_dict,
                    "triage": triage_output.result,
                    "risk": risk_output.result,
                    "knowledge": knowledge_output.result,
                },
            )
            workforce_output = await self.workforce_agent.execute(workforce_input, db)
            state.agent_results["workforce"] = workforce_output.result
            state.completed_steps.append("workforce_planning")
            await self._record_agent_run(db, workflow_id, incident_id, "workforce_agent", workforce_output)

            # -----------------------------------------------------------
            # STAGE 5: Response Recommendation Agent
            # -----------------------------------------------------------
            state.current_step = "recommendation_generation"
            response_input = AgentInput(
                incident_id=incident_id,
                workflow_id=workflow_id,
                context={
                    "incident": incident_dict,
                    "triage": triage_output.result,
                    "knowledge": knowledge_output.result,
                    "risk": risk_output.result,
                    "workforce": workforce_output.result,
                },
            )
            response_output = await self.response_agent.execute(response_input, db)
            state.agent_results["response"] = response_output.result
            state.approval_id = response_output.result.get("approval_id")
            state.completed_steps.append("recommendation_generation")
            await self._record_agent_run(db, workflow_id, incident_id, "response_agent", response_output)

            # -----------------------------------------------------------
            # STAGE 6: Human Approval Gate (PAUSE)
            # -----------------------------------------------------------
            state.current_step = "waiting_for_approval"
            state.status = "waiting_approval"

            if db:
                await self._update_incident_status(db, incident_id, "pending_approval")

            logger.info(f"Workflow {workflow_id} paused at human approval gate with approval_id {state.approval_id}")
            return state

        except Exception as e:
            logger.error(f"Error in workflow {workflow_id}: {e}", exc_info=True)
            state.status = "failed"
            state.error = str(e)
            return state

    async def _record_agent_run(self, db, workflow_id: str, incident_id: str, agent_id: str, output: AgentOutput):
        if not db:
            return
        try:
            from app.models.event import AgentRun, AgentRunStatus, AgentEvent
            run_id = f"RUN-{uuid.uuid4().hex[:6].upper()}"
            run = AgentRun(
                id=run_id,
                incident_id=incident_id,
                agent_id=agent_id,
                status=AgentRunStatus.completed if output.success else AgentRunStatus.failed,
                workflow_id=workflow_id,
                step_count=1,
                error_message=output.error_message,
                completed_at=datetime.now(timezone.utc),
            )
            db.add(run)
            event = AgentEvent(
                run_id=run_id,
                event_type="execution_completed",
                payload_json={"duration_ms": output.execution_time_ms, "evidence": output.evidence},
            )
            db.add(event)
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record agent run: {e}")

    async def _record_security_event(self, db, incident_id: str, sec_result, text: str):
        try:
            from app.models.event import SecurityEvent, SecurityEventAction, SecurityEventSeverity
            import hashlib
            h = hashlib.sha256(text.encode()).hexdigest()
            evt = SecurityEvent(
                actor_id="system_gateway",
                agent_id="security_guardian",
                threat_type=sec_result.threat_type,
                severity=SecurityEventSeverity(sec_result.risk_level),
                action=SecurityEventAction(sec_result.action),
                input_hash=h,
                metadata_json={"reason": sec_result.reason, "confidence": sec_result.confidence},
            )
            db.add(evt)
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record security event: {e}")

    async def _record_risk_assessment(self, db, incident_id: str, risk_dict: Dict[str, Any]):
        try:
            from app.models.event import RiskAssessment, RiskLevel
            ra = RiskAssessment(
                id=f"RISK-{uuid.uuid4().hex[:6].upper()}",
                incident_id=incident_id,
                score=risk_dict.get("risk_score", 50.0),
                risk_level=RiskLevel(risk_dict.get("risk_level", "moderate")),
                model_version=risk_dict.get("method", "v1"),
                factors_json=risk_dict.get("factors", {}),
                missing_factors_json=risk_dict.get("missing_indicators", []),
                limitations_json=risk_dict.get("limitations", []),
            )
            db.add(ra)
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to record risk assessment: {e}")

    async def _update_incident_status(self, db, incident_id: str, status_val: str):
        try:
            from app.models.incident import Incident, IncidentStatus
            await db.execute(
                update(Incident)
                .where(Incident.id == incident_id)
                .values(status=IncidentStatus(status_val))
            )
            await db.commit()
        except Exception as e:
            logger.warning(f"Failed to update incident status: {e}")
