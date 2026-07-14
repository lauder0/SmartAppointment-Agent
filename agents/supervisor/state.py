"""State schema for the 3.0 supervisor and specialist subgraphs.

The supervisor owns session-level routing and handoff facts. Specialist
subgraphs own their private business state and expose structured results back
to the supervisor.
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph.message import add_messages

from agents.understanding.schemas import default_task_frame


class SupervisorState(TypedDict, total=False):
    """Shared state passed through the 3.0 supervisor graph."""

    session_id: str
    user_id: str
    messages: Annotated[List[BaseMessage], add_messages]

    active_agent: Optional[str]
    active_task: Optional[str]
    task_stack: List[Dict[str, Any]]

    shared_focus_context: Dict[str, Any]
    consultation: Dict[str, Any]
    availability: Dict[str, Any]
    booking: Dict[str, Any]
    recommendation: Dict[str, Any]
    task_frame: Dict[str, Any]

    route_decision: Optional[Dict[str, Any]]
    handoff_payload: Dict[str, Any]
    last_agent_result: Optional[Dict[str, Any]]
    last_completed_booking: Optional[Dict[str, Any]]

    final_response: Optional[str]
    error: Optional[str]
    tool_results: Dict[str, Any]


def default_shared_focus_context() -> Dict[str, Any]:
    """Create cross-subgraph context describing what the user is discussing."""
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


def default_consultation_state() -> Dict[str, Any]:
    return {
        "status": "idle",
        "last_topic": None,
        "retrieved_docs": [],
        "last_answer": None,
    }


def default_availability_state() -> Dict[str, Any]:
    return {
        "status": "idle",
        "criteria_snapshot": None,
        "options": [],
        "available_technician_names": [],
        "last_answer": None,
    }


def default_booking_state() -> Dict[str, Any]:
    return {
        "status": "idle",
        "draft": {},
        "missing_fields": [],
        "confirmation_summary": None,
        "selected_option": None,
        "excluded_technician_ids": [],
        "guard_result": None,
    }


def default_recommendation_state() -> Dict[str, Any]:
    return {
        "status": "idle",
        "recalled_preferences": {},
        "candidate_recommendations": [],
        "selected_recommendation": None,
        "alternative_recommendations": [],
        "preference": None,
        "recommendation_reason": None,
        "confidence": None,
        "excluded_technician_ids": [],
        "trigger_reason": None,
    }


def ensure_supervisor_defaults(state: SupervisorState) -> SupervisorState:
    """Ensure all supervisor and specialist state containers exist."""
    state.setdefault("active_agent", None)
    state.setdefault("active_task", None)
    state.setdefault("task_stack", [])
    state.setdefault("shared_focus_context", default_shared_focus_context())
    state.setdefault("consultation", default_consultation_state())
    state.setdefault("availability", default_availability_state())
    state.setdefault("booking", default_booking_state())
    state.setdefault("recommendation", default_recommendation_state())
    state.setdefault("task_frame", default_task_frame())
    state.setdefault("route_decision", None)
    state.setdefault("handoff_payload", {})
    state.setdefault("last_agent_result", None)
    state.setdefault("last_completed_booking", None)
    state.setdefault("final_response", None)
    state.setdefault("error", None)
    state.setdefault("tool_results", {})
    return state


def state_for_agent_actions(state: SupervisorState) -> Dict[str, Any]:
    """Adapt supervisor state to the internal action contract used by specialists."""
    state = ensure_supervisor_defaults(state)
    return {
        "session_id": state.get("session_id"),
        "user_id": state.get("user_id"),
        "messages": state.get("messages", []),
        "focus_context": dict(state.get("shared_focus_context") or {}),
        "availability_result": {
            "criteria_snapshot": (state.get("availability") or {}).get("criteria_snapshot"),
            "options": list((state.get("availability") or {}).get("options") or []),
            "available_technician_names": list(
                (state.get("availability") or {}).get("available_technician_names") or []
            ),
            "last_answer": (state.get("availability") or {}).get("last_answer"),
        },
        "booking": dict(state.get("booking") or default_booking_state()),
        "recommendation": dict(state.get("recommendation") or default_recommendation_state()),
        "task_frame": dict(state.get("task_frame") or default_task_frame()),
        "route_decision": state.get("route_decision"),
        "last_completed_booking": state.get("last_completed_booking"),
        "final_response": state.get("final_response"),
        "error": state.get("error"),
        "tool_results": dict(state.get("tool_results") or {}),
    }


def merge_agent_action_update(state: SupervisorState, update: Dict[str, Any]) -> SupervisorState:
    """Merge a specialist action update into the 3.0 supervisor state shape."""
    merged: SupervisorState = {}
    pending_responses = list(
        ((state.get("tool_results") or {}).get("query_first_intermediate_responses") or [])
    )
    merged_final_response = update.get("final_response")
    if merged_final_response and pending_responses:
        merged_final_response = "\n\n".join([*pending_responses, merged_final_response])
    if "focus_context" in update:
        merged["shared_focus_context"] = update["focus_context"]
    if "availability_result" in update:
        availability = dict(state.get("availability") or default_availability_state())
        raw = update["availability_result"] or {}
        availability.update(
            {
                "status": "completed" if raw.get("criteria_snapshot") or raw.get("options") else "idle",
                "criteria_snapshot": raw.get("criteria_snapshot"),
                "options": raw.get("options") or [],
                "available_technician_names": raw.get("available_technician_names") or [],
                "last_answer": raw.get("last_answer"),
            }
        )
        merged["availability"] = availability
    if "booking" in update:
        merged["booking"] = update["booking"]
    if "recommendation" in update:
        merged["recommendation"] = update["recommendation"]
    if "task_frame" in update:
        merged["task_frame"] = update["task_frame"]
    if "route_decision" in update:
        merged["route_decision"] = update["route_decision"]
    if "last_completed_booking" in update:
        merged["last_completed_booking"] = update["last_completed_booking"]
    if "final_response" in update:
        merged["final_response"] = merged_final_response
    if "error" in update:
        merged["error"] = update["error"]
    if "tool_results" in update:
        merged["tool_results"] = update["tool_results"]
    if pending_responses and merged_final_response:
        merged["tool_results"] = {
            **(state.get("tool_results") or {}),
            **(merged.get("tool_results") or {}),
            "query_first_intermediate_responses": [],
        }
    if "messages" in update:
        if pending_responses and merged_final_response:
            merged["messages"] = [AIMessage(content=merged_final_response)]
        else:
            merged["messages"] = update["messages"]
    return merged
