"""
AgentOps: Circuit Breaker.
Protects the platform from runaway agent executions, infinite loops, and repeated failing calls.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CircuitBreakerConfig(BaseModel):
    max_steps: int = 8
    max_retries: int = 2
    max_duration_seconds: float = 120.0
    max_repeated_calls: int = 3


class CircuitBreakerResult(BaseModel):
    tripped: bool
    reason: Optional[str] = None
    action: str = "allow"  # allow, pause, circuit_break


class CircuitBreaker:
    """
    Evaluates real-time execution statistics against safety thresholds.
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()

    def check(
        self,
        step_count: int,
        retry_count: int,
        duration_seconds: float,
        recent_tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> CircuitBreakerResult:
        # Check 1: Step limits
        if step_count >= self.config.max_steps:
            return CircuitBreakerResult(
                tripped=True,
                reason=f"Agent exceeded maximum allowed execution steps ({step_count}/{self.config.max_steps})",
                action="circuit_break",
            )

        # Check 2: Retries
        if retry_count >= self.config.max_retries:
            return CircuitBreakerResult(
                tripped=True,
                reason=f"Agent exhausted maximum retry budget ({retry_count}/{self.config.max_retries})",
                action="circuit_break",
            )

        # Check 3: Duration
        if duration_seconds >= self.config.max_duration_seconds:
            return CircuitBreakerResult(
                tripped=True,
                reason=f"Execution exceeded duration threshold ({duration_seconds:.1f}s / {self.config.max_duration_seconds}s)",
                action="circuit_break",
            )

        # Check 4: Repeated identical tool calls
        if recent_tool_calls and len(recent_tool_calls) >= self.config.max_repeated_calls:
            tail = recent_tool_calls[-self.config.max_repeated_calls:]
            first_tool = tail[0].get("tool")
            first_args = str(tail[0].get("args", {}))
            if all(c.get("tool") == first_tool and str(c.get("args", {})) == first_args for c in tail):
                return CircuitBreakerResult(
                    tripped=True,
                    reason=f"Detected {self.config.max_repeated_calls} repeated identical calls to '{first_tool}' without state progress",
                    action="pause",
                )

        return CircuitBreakerResult(tripped=False, action="allow")
