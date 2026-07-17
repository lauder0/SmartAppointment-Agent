"""Shared state schema for the LangGraph agent workflow."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from agents._shared.context_schema import default_focus_context
from agents.supervisor.planning.plan_schema import default_execution_plan
from agents.understander.schemas import default_task_frame


class AgentState(TypedDict, total=False):
    """State passed between graph nodes."""

    session_id: str
    user_id: str
    messages: Annotated[List[BaseMessage], add_messages]
    focus_context: Dict[str, Any]
    availability_result: Dict[str, Any]
    booking: Dict[str, Any]
    recommendation: Dict[str, Any]
    task_frame: Dict[str, Any]
    execution_plan: Dict[str, Any]
    route_decision: Optional[Dict[str, Any]]
    last_completed_booking: Optional[Dict[str, Any]]
    final_response: Optional[str]
    error: Optional[str]
    tool_results: Dict[str, Any]


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
    state.setdefault("task_frame", default_task_frame())
    state.setdefault("execution_plan", default_execution_plan())
    state.setdefault("route_decision", None)
    state.setdefault("tool_results", {})
    state.setdefault("last_completed_booking", None)
    state.setdefault("final_response", None)
    state.setdefault("error", None)
    return state
