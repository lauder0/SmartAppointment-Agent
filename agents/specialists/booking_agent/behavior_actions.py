"""User behavior graph nodes."""

from __future__ import annotations

from agents._shared.state import AgentState, ensure_state_defaults
from tools.user_behavior_tools import record_user_behavior


async def behavior_recorder_node(state: AgentState) -> AgentState:
    """Record behavior after graph-handled actions.

    AppointmentService already records durable appointment data. This node is
    intentionally conservative and records only when appointment details are
    still available in tool results.
    """
    state = ensure_state_defaults(state)
    create_result = state.get("tool_results", {}).get("create_appointment")
    if not create_result or not create_result.get("success"):
        return {}

    data = create_result.get("data", {})
    result = record_user_behavior.invoke(
        {
            "user_id": state.get("user_id") or "default_user",
            "action_type": "appointment",
            "action_data": data,
            "technician_id": str(data.get("technician_id")) if data.get("technician_id") else None,
            "session_id": state.get("session_id") or "default_session",
        }
    )
    return {"tool_results": {**state.get("tool_results", {}), "record_user_behavior": result}}
