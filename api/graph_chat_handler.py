"""Chat handler backed by the 3.0 supervisor workflow."""

from __future__ import annotations

import uuid
import time

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
from agents.supervisor.planning.plan_schema import default_execution_plan
from agents.understander.schemas import default_task_frame
from services.session_state_store import SessionStateStore, create_session_state_store
from services.trace_service import attach_turn_trace, new_trace_id

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
        "task_frame": default_task_frame(),
        "execution_plan": default_execution_plan(),
        "route_decision": None,
        "last_agent_result": None,
        "turn_results": [],
        "turn_trace": None,
        "trace_history": [],
        "last_completed_booking": None,
        "final_response": None,
        "error": None,
        "tool_results": {},
    }


async def reset_graph_session(session_id: str) -> None:
    await _get_session_store().delete(session_id)


async def get_graph_session_state(session_id: str) -> SupervisorState:
    state = await _get_session_store().get(session_id) or {}
    return _with_public_compat_aliases(state)


def _with_public_compat_aliases(state: SupervisorState) -> SupervisorState:
    """Return session state with legacy read aliases for eval/debug clients."""
    if not state:
        return state
    public_state: SupervisorState = dict(state)
    availability = public_state.get("availability") or {}
    public_state.setdefault(
        "availability_result",
        {
            "criteria_snapshot": availability.get("criteria_snapshot"),
            "options": availability.get("options", []),
            "available_technician_names": availability.get("available_technician_names", []),
            "last_answer": availability.get("last_answer"),
        },
    )
    public_state.setdefault("focus_context", public_state.get("shared_focus_context"))
    return public_state


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

        trace_id = new_trace_id()
        started = time.perf_counter()
        try:
            result = await _get_graph().ainvoke(state)
        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            error_state = dict(state)
            error_state["error"] = str(exc)
            await store.set(
                resolved_session_id,
                attach_turn_trace(
                    error_state,
                    trace_id=trace_id,
                    user_input=user_input,
                    latency_ms=latency_ms,
                    error=str(exc),
                ),
            )
            raise

        latency_ms = (time.perf_counter() - started) * 1000
        result = attach_turn_trace(
            result,
            trace_id=trace_id,
            user_input=user_input,
            latency_ms=latency_ms,
        )
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
