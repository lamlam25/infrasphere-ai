"""
AgentOps: Execution and Tracing Manager.
Tracks individual agent execution lifecycles, spans, timing, and errors.
"""
from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TraceSpan(BaseModel):
    span_id: str = Field(default_factory=lambda: f"SPAN-{uuid.uuid4().hex[:6].upper()}")
    run_id: str
    parent_span_id: Optional[str] = None
    operation: str
    agent_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: str = "running"  # running, success, error
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error: Optional[str] = None


class TraceManager:
    """In-memory and persistent trace collector for agent operations."""

    def __init__(self):
        self._spans: Dict[str, TraceSpan] = {}

    def start_span(
        self,
        run_id: str,
        operation: str,
        agent_id: str,
        parent_span_id: Optional[str] = None,
        input_summary: Optional[str] = None,
    ) -> TraceSpan:
        span = TraceSpan(
            run_id=run_id,
            operation=operation,
            agent_id=agent_id,
            parent_span_id=parent_span_id,
            input_summary=input_summary,
        )
        self._spans[span.span_id] = span
        return span

    def end_span(
        self,
        span_id: str,
        status: str = "success",
        output_summary: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[TraceSpan]:
        span = self._spans.get(span_id)
        if not span:
            return None
        span.ended_at = datetime.now(timezone.utc)
        span.status = status
        span.output_summary = output_summary
        span.error = error
        if span.started_at:
            delta = span.ended_at - span.started_at
            span.duration_ms = int(delta.total_seconds() * 1000)
        return span

    def get_traces_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        return [
            s.model_dump()
            for s in self._spans.values()
            if s.run_id == run_id
        ]


# Global singleton instance for easy in-process telemetry
trace_manager = TraceManager()
