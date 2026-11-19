"""
tool_policy.py – Agent tool permission registry and policy engine.

Defines which tools each agent type may and may not call.  Any tool that is
not explicitly listed in `allowed` defaults to DENY (whitelist model).
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Permission registry
# ---------------------------------------------------------------------------

AGENT_PERMISSIONS: dict[str, dict[str, list[str]]] = {
    "security_guardian": {
        "allowed": ["inspect_input", "log_security_event", "check_permissions"],
        "denied": ["execute_actions", "modify_database", "approve_decisions"],
    },
    "triage": {
        "allowed": [
            "read_incident",
            "classify_incident",
            "extract_entities",
            "update_incident_status",
        ],
        "denied": [
            "close_incident",
            "delete_incident",
            "approve_decisions",
            "dispatch_teams",
        ],
    },
    "knowledge": {
        "allowed": [
            "search_documents",
            "retrieve_chunks",
            "query_graph",
            "read_incident",
        ],
        "denied": ["modify_documents", "delete_documents", "approve_decisions"],
    },
    "risk": {
        "allowed": [
            "read_incident",
            "read_stations",
            "read_assets",
            "read_history",
        ],
        "denied": ["send_emergency_alert", "modify_assets", "approve_decisions"],
    },
    "workforce": {
        "allowed": [
            "read_teams",
            "read_agents",
            "read_tasks",
            "create_tasks",
            "recommend_assignments",
        ],
        "denied": ["dispatch_field_teams", "approve_decisions", "modify_personnel"],
    },
    "response": {
        "allowed": [
            "read_all_results",
            "generate_recommendation",
            "create_approval_request",
        ],
        "denied": [
            "execute_public_actions",
            "approve_own_recommendation",
            "dispatch_teams",
        ],
    },
}


# ---------------------------------------------------------------------------
# Policy engine
# ---------------------------------------------------------------------------

class ToolPolicyEngine:
    """Whitelist-based agent tool policy engine.

    Any tool not in the ``allowed`` list is DENIED by default.
    Tools in the ``denied`` list are explicitly forbidden with a clearer reason.
    """

    def __init__(self, permissions: dict[str, dict[str, list[str]]] | None = None):
        self._permissions = permissions or AGENT_PERMISSIONS

    # ------------------------------------------------------------------
    # Permission check
    # ------------------------------------------------------------------

    def check_permission(self, agent_type: str, tool_name: str) -> dict[str, Any]:
        """Check whether *agent_type* may call *tool_name*.

        Returns:
            {allowed: bool, reason: str}
        """
        agent_config = self._permissions.get(agent_type)

        if agent_config is None:
            return {
                "allowed": False,
                "reason": f"Unknown agent type '{agent_type}'. No permissions defined.",
            }

        allowed_tools: list[str] = agent_config.get("allowed", [])
        denied_tools: list[str] = agent_config.get("denied", [])

        if tool_name in denied_tools:
            return {
                "allowed": False,
                "reason": (
                    f"Tool '{tool_name}' is explicitly denied for agent type "
                    f"'{agent_type}'."
                ),
            }

        if tool_name in allowed_tools:
            return {
                "allowed": True,
                "reason": (
                    f"Tool '{tool_name}' is explicitly permitted for agent type "
                    f"'{agent_type}'."
                ),
            }

        # Whitelist model: not in allowed → deny
        return {
            "allowed": False,
            "reason": (
                f"Tool '{tool_name}' is not in the allowed list for agent type "
                f"'{agent_type}'. Access denied by whitelist policy."
            ),
        }

    # ------------------------------------------------------------------
    # Permission query
    # ------------------------------------------------------------------

    def get_agent_permissions(self, agent_type: str) -> dict[str, Any]:
        """Return the full permission record for *agent_type*."""
        config = self._permissions.get(agent_type)
        if config is None:
            return {
                "agent_type": agent_type,
                "error": f"Unknown agent type '{agent_type}'",
            }
        return {
            "agent_type": agent_type,
            "allowed": config.get("allowed", []),
            "denied": config.get("denied", []),
        }

    def list_agent_types(self) -> list[str]:
        """Return all registered agent types."""
        return list(self._permissions.keys())

    def all_permissions(self) -> dict[str, dict[str, list[str]]]:
        """Return the full permission registry."""
        return dict(self._permissions)
