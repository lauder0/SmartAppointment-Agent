"""Chat handler backed by the 3.0 supervisor workflow."""

from __future__ import annotations

import uuid

from langchain_core.messages import HumanMessage

from agents.supervisor import build_smart_appointment_supervisor_graph
from agents.supervisor.state import (
    SupervisorState,
    default_availability_state,
    default_booking_state,
    default_consultation_state,
    default_recommendation_state,
    default_shared_focus_context,
)
from services.session_state_store import SessionStateStore, create_session_state_store

_graph = None
_session_store: SessionStateStore | None = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_smart_appointment_supervisor_graph()
    return _graph


def _get_session_store() -> SessionStateStore:
    global _session_store
    if _session_store is None:
        _session_store = create_session_state_store()
    return _session_store


def _initial_state(session_id: str, user_id: str = "default_user") -> SupervisorState:
    return {
        "session_id": session_id,
        "user_id": user_id,
        "messages": [],
        "active_agent": None,
        "active_task": None,
        "task_stack": [],
        "shared_focus_context": default_shared_focus_context(),
        "consultation": default_consultation_state(),
        "availability": default_availability_state(),
        "booking": default_booking_state(),
        "recommendation": default_recommendation_state(),
        "route_decision": None,
        "handoff_payload": {},
        "last_agent_result": None,
        "last_completed_booking": None,
        "final_response": None,
        "error": None,
        "tool_results": {},
    }


async def reset_graph_session(session_id: str) -> None:
    await _get_session_store().delete(session_id)


async def get_graph_session_state(session_id: str) -> SupervisorState:
    return await _get_session_store().get(session_id) or {}


async def process_user_input_graph(
    user_input: str,
    session_id: str | None = None,
    user_id: str = "default_user",
) -> SupervisorState:
    """Process one user turn through the 3.0 supervisor workflow and return final state."""
    resolved_session_id = session_id or str(uuid.uuid4())
    store = _get_session_store()

    async with store.lock(resolved_session_id):
        state = await store.get(resolved_session_id) or _initial_state(resolved_session_id, user_id)
        state = dict(state)
        state["session_id"] = resolved_session_id
        state["user_id"] = user_id or state.get("user_id") or "default_user"
        state["messages"] = list(state.get("messages", [])) + [HumanMessage(content=user_input)]

        result = await _get_graph().ainvoke(state)
        await store.set(resolved_session_id, result)
        return result


async def ProcessUserInput_graph_stream(
    user_input: str,
    session_id: str | None = None,
    user_id: str = "default_user",
):
    """Process one user turn through the 3.0 supervisor workflow as a character stream."""
    result = await process_user_input_graph(
        user_input,
        session_id=session_id,
        user_id=user_id,
    )
    response = result.get("final_response") or "[ERROR]Supervisor workflow did not generate a response."
    for char in response:
        yield char
