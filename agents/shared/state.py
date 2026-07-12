"""Shared state schema for the LangGraph agent workflow."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """State passed between graph nodes."""

    session_id: str
    user_id: str
    messages: Annotated[List[BaseMessage], add_messages]
    focus_context: Dict[str, Any]
    availability_result: Dict[str, Any]
    booking: Dict[str, Any]
    recommendation: Dict[str, Any]
    route_decision: Optional[Dict[str, Any]]
    last_completed_booking: Optional[Dict[str, Any]]
    final_response: Optional[str]
    error: Optional[str]
    tool_results: Dict[str, Any]


def default_focus_context() -> Dict[str, Any]:
    """Create a fresh service-request focus context.

    This records what the user is currently talking about, independent of
    whether the next action is availability lookup or booking.
    """
    return {
        "service_type": None,
        "start_time": None,
        "duration_minutes": None,
        "gender_preference": None,
        "technician_name": None,
        "technician_id": None,
        "preference": None,
        "last_offer": None,
    }


def default_availability_result() -> Dict[str, Any]:
    """Create a fresh availability-result container."""
    return {
        "criteria_snapshot": None,
        "options": [],
        "available_technician_names": [],
        "last_answer": None,
    }


def default_booking_state() -> Dict[str, Any]:
    """Create a fresh booking transaction state."""
    return {
        "status": "idle",
        "draft": {},
        "missing_fields": [],
        "confirmation_summary": None,
        "selected_option": None,
        "excluded_technician_ids": [],
        "guard_result": None,
    }


def ensure_state_defaults(state: AgentState) -> AgentState:
    """Ensure optional state containers exist before node processing."""
    state.setdefault("focus_context", default_focus_context())
    state.setdefault("availability_result", default_availability_result())
    state.setdefault("booking", default_booking_state())
    state.setdefault("recommendation", {})
    state.setdefault("route_decision", None)
    state.setdefault("tool_results", {})
    state.setdefault("last_completed_booking", None)
    state.setdefault("final_response", None)
    state.setdefault("error", None)
    return state
