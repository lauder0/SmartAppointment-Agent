"""Routing functions for the 3.0 supervisor graph."""

from __future__ import annotations

from agents.supervisor.state import SupervisorState


def route_supervisor_decision(state: SupervisorState) -> str:
    action = (state.get("route_decision") or {}).get("action")
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
    if action == "ask_clarification":
        return "fallback"
    return "fallback"


def route_after_availability(state: SupervisorState) -> str:
    """Continue into recommendation when availability was requested as preparation."""
    reason = (state.get("route_decision") or {}).get("reason")
    options = (state.get("availability") or {}).get("options") or []
    if reason == "prepare_candidates_for_recommendation" and options:
        return "recommendation"
    return "end"
