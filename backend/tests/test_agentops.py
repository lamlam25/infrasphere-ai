"""Tests for AgentOps: circuit breaker, tracing spans, and execution guardrails."""
from app.agentops.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.agentops.tracing import TraceManager


def test_circuit_breaker_step_limits():
    cb = CircuitBreaker(CircuitBreakerConfig(max_steps=5))
    res_ok = cb.check(step_count=4, retry_count=0, duration_seconds=10.0)
    assert res_ok.tripped is False

    res_limit = cb.check(step_count=5, retry_count=0, duration_seconds=10.0)
    assert res_limit.tripped is True
    assert "steps" in res_limit.reason.lower()


def test_circuit_breaker_repeated_calls():
    cb = CircuitBreaker(CircuitBreakerConfig(max_repeated_calls=3))
    calls = [
        {"tool": "fetch_water", "args": {"station": "S1"}},
        {"tool": "fetch_water", "args": {"station": "S1"}},
        {"tool": "fetch_water", "args": {"station": "S1"}},
    ]
    res = cb.check(step_count=3, retry_count=0, duration_seconds=10.0, recent_tool_calls=calls)
    assert res.tripped is True
    assert "repeated" in res.reason.lower()


def test_trace_manager_lifecycle():
    tm = TraceManager()
    span = tm.start_span(run_id="RUN-01", operation="triage", agent_id="triage_agent")
    assert span.status == "running"

    finished = tm.end_span(span.span_id, status="success", output_summary="Classification completed")
    assert finished.status == "success"
    assert finished.duration_ms is not None

    traces = tm.get_traces_for_run("RUN-01")
    assert len(traces) == 1
    assert traces[0]["operation"] == "triage"
