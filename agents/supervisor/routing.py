"""Routing functions for the 3.0 supervisor graph."""

from __future__ import annotations

from agents.supervisor.state import SupervisorState


def route_supervisor_decision(state: SupervisorState) -> str:
    action = (state.get("route_decision") or {}).get("action")
    if action == "answer_knowledge":
        return "consultation"
    if action == "query_availability":
        return "availability"
    if action in {"generate_recommendation", "answer_recommendation"}:
        return "recommendation"
    if action in {"start_or_continue_booking", "modify_booking", "confirm_booking", "cancel_booking"}:
        return "booking"
    if action == "ask_clarification":
        return "fallback"
    return "fallback"
