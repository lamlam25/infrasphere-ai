"""Base agent classes and data models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


class AgentInput(BaseModel):
    incident_id: str
    workflow_id: str
    context: dict = {}


class AgentOutput(BaseModel):
    agent_type: str
    success: bool
    result: dict
    evidence: list[str] = []
    limitations: list[str] = []
    execution_time_ms: int = 0
    error_message: str | None = None


class BaseAgent:
    agent_type: str = "base"
    max_steps: int = 8

    def __init__(self, settings=None):
        self.settings = settings
        self._step_count = 0
        self._tool_calls: list[dict] = []
        self._start_time: datetime | None = None

    def execute(self, input: AgentInput, db=None) -> AgentOutput:
        """Main execution method. Override in subclasses."""
        raise NotImplementedError

    def _start_timer(self) -> None:
        self._start_time = datetime.now(timezone.utc)

    def _elapsed_ms(self) -> int:
        if self._start_time is None:
            return 0
        delta = datetime.now(timezone.utc) - self._start_time
        return int(delta.total_seconds() * 1000)

    def _check_limits(self):
        if self._step_count >= self.max_steps:
            raise RuntimeError(f"Agent exceeded {self.max_steps} steps")

    def _record_tool_call(self, tool_name: str, args: dict, result: Any):
        self._tool_calls.append(
            {
                "tool": tool_name,
                "args": args,
                "result_summary": str(result)[:200],
                "step": self._step_count,
            }
        )
        # Circuit breaker: repeated identical calls
        recent = [c for c in self._tool_calls[-6:] if c["tool"] == tool_name]
        if len(recent) >= 3 and len(set(str(c["args"]) for c in recent)) == 1:
            raise RuntimeError(
                f"Circuit breaker: repeated identical calls to {tool_name}"
            )

    def _error_output(self, error: str) -> AgentOutput:
        return AgentOutput(
            agent_type=self.agent_type,
            success=False,
            result={},
            error_message=error,
            execution_time_ms=self._elapsed_ms(),
        )
