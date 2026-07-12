"""Supervisor-only nodes for 3.0 orchestration."""

from __future__ import annotations

from agents.supervisor.router_actions import main_router_node
from agents.supervisor.state import (
    SupervisorState,
    ensure_supervisor_defaults,
    state_for_agent_actions,
)


async def supervisor_entry_node(state: SupervisorState) -> SupervisorState:
    state = ensure_supervisor_defaults(state)
    return {
        "active_agent": state.get("active_agent"),
        "active_task": state.get("active_task"),
        "task_stack": state.get("task_stack", []),
        "shared_focus_context": state.get("shared_focus_context"),
        "consultation": state.get("consultation"),
        "availability": state.get("availability"),
        "booking": state.get("booking"),
        "recommendation": state.get("recommendation"),
        "route_decision": None,
        "handoff_payload": {},
        "last_agent_result": state.get("last_agent_result"),
        "last_completed_booking": state.get("last_completed_booking"),
        "tool_results": state.get("tool_results", {}),
        "final_response": None,
        "error": None,
    }


async def supervisor_router_node(state: SupervisorState) -> SupervisorState:
    router_update = await main_router_node(state_for_agent_actions(state))
    decision = router_update.get("route_decision") or {"action": "unsupported", "reason": "no_decision"}
    action = decision.get("action")
    target_agent = _agent_for_action(action)
    return {
        "route_decision": decision,
        "active_agent": target_agent,
        "active_task": _task_for_action(action),
        "tool_results": {
            **(state.get("tool_results") or {}),
            "supervisor_router": decision,
        },
    }


def _agent_for_action(action: str | None) -> str:
    if action == "answer_knowledge":
        return "consultation"
    if action == "query_availability":
        return "availability"
    if action in {"generate_recommendation", "answer_recommendation", "replace_recommendation"}:
        return "recommendation"
    if action in {
        "start_or_continue_booking",
        "modify_booking",
        "confirm_booking",
        "cancel_booking",
        "select_recommended_technician",
    }:
        return "booking"
    return "fallback"


def _task_for_action(action: str | None) -> str | None:
    if action in {"answer_knowledge", "query_availability", "start_or_continue_booking", "modify_booking"}:
        return action
    if action in {"generate_recommendation", "answer_recommendation", "replace_recommendation"}:
        return "recommendation"
    if action in {"confirm_booking", "cancel_booking", "select_recommended_technician"}:
        return "booking_confirmation"
    return None

