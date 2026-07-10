"""API-facing views derived from the 3.0 supervisor state."""

from __future__ import annotations

from typing import Any, Dict


def action_to_intent(action: str | None) -> str:
    if action == "answer_knowledge":
        return "knowledge_query"
    if action == "query_availability":
        return "availability_query"
    if action in {
        "start_or_continue_booking",
        "modify_booking",
        "confirm_booking",
        "cancel_booking",
    }:
        return "appointment"
    return "other"


def state_to_intent(state: Dict[str, Any]) -> str:
    action = (state.get("route_decision") or {}).get("action")
    booking_status = (state.get("booking") or {}).get("status")
    if action in {"unsupported", "ask_clarification"} and booking_status in {
        "drafting",
        "draft_ready",
        "matched",
        "awaiting_confirmation",
        "confirmed",
    }:
        return "appointment"
    return action_to_intent(action)


def action_to_agent(action: str | None, response: str | None = None) -> str:
    if action == "answer_knowledge":
        return "consultation"
    if action == "query_availability":
        return "availability"
    if action in {
        "start_or_continue_booking",
        "modify_booking",
        "confirm_booking",
        "cancel_booking",
    }:
        return "booking"
    if response and "[棰勭害鏈哄櫒浜篯" in response:
        return "booking"
    if response and "[鍜ㄨ鏈哄櫒浜篯" in response:
        return "consultation"
    return "fallback"


def _availability_result_view(state: Dict[str, Any]) -> Dict[str, Any]:
    availability = state.get("availability") or {}
    return {
        "criteria_snapshot": availability.get("criteria_snapshot"),
        "options": availability.get("options", []),
        "available_technician_names": availability.get("available_technician_names", []),
        "last_answer": availability.get("last_answer"),
    }


def state_view(state: Dict[str, Any]) -> Dict[str, Any]:
    decision = state.get("route_decision") or {}
    action = decision.get("action")
    response = state.get("final_response")
    shared_focus_context = state.get("shared_focus_context")
    return {
        "supervisor": {
            "active_agent": state.get("active_agent"),
            "active_task": state.get("active_task"),
            "task_stack": state.get("task_stack", []),
            "handoff_payload": state.get("handoff_payload", {}),
            "last_agent_result": state.get("last_agent_result"),
        },
        "route_decision": decision,
        "intent": state_to_intent(state),
        "agent": action_to_agent(action, response),
        "shared_focus_context": shared_focus_context,
        "focus_context": shared_focus_context,
        "consultation": state.get("consultation"),
        "availability": state.get("availability"),
        "availability_result": _availability_result_view(state),
        "booking": state.get("booking"),
        "recommendation": state.get("recommendation"),
        "last_completed_booking": state.get("last_completed_booking"),
    }
