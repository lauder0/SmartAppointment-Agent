"""Chat handler backed by the 3.0 supervisor workflow."""

from __future__ import annotations

import uuid
import time
from typing import Any, AsyncIterator

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


NODE_PROGRESS_MESSAGES = {
    "supervisor_entry": ("intake", "正在接收并整理本轮上下文"),
    "supervisor_router": ("understanding", "正在理解需求并制定处理计划"),
    "supervisor_continue": ("planning", "正在推进下一步任务"),
    "consultation_subgraph": ("consultation", "正在查询知识库并整理咨询结果"),
    "availability_subgraph": ("availability", "正在查询可预约时间和技师"),
    "booking_subgraph": ("booking", "正在校验预约信息"),
    "recommendation_subgraph": ("recommendation", "正在筛选推荐项目或技师"),
    "fallback_subgraph": ("fallback", "正在准备兜底回复"),
    "supervisor_response": ("response", "正在整理最终回复"),
}


async def process_user_input_graph_events(
    user_input: str,
    session_id: str | None = None,
    user_id: str = "default_user",
) -> AsyncIterator[dict[str, Any]]:
    """Process one user turn and stream safe, user-facing progress events."""
    resolved_session_id = session_id or str(uuid.uuid4())
    store = _get_session_store()
    response_text = ""
    done_event: dict[str, Any] | None = None

    async with store.lock(resolved_session_id):
        state = await store.get(resolved_session_id) or _initial_state(resolved_session_id, user_id)
        state = dict(state)
        state["session_id"] = resolved_session_id
        state["user_id"] = user_id or state.get("user_id") or "default_user"
        state["messages"] = list(state.get("messages", [])) + [HumanMessage(content=user_input)]

        trace_id = new_trace_id()
        started = time.perf_counter()
        streamed_state: SupervisorState = dict(state)
        last_plan_signature = _persisted_plan_signature(state)

        yield {
            "type": "start",
            "session_id": resolved_session_id,
            "trace_id": trace_id,
            "message": "开始处理您的请求",
        }

        try:
            async for update_chunk in _get_graph().astream(state, stream_mode="updates"):
                if not isinstance(update_chunk, dict):
                    continue

                for node_name, node_update in update_chunk.items():
                    if not isinstance(node_update, dict):
                        continue

                    streamed_state = _merge_stream_update(streamed_state, node_update)

                    progress_event = _progress_event_for_node(node_name, streamed_state, node_update)
                    if progress_event:
                        yield progress_event

                    plan_event, last_plan_signature = _plan_event_if_changed(
                        streamed_state,
                        last_plan_signature,
                    )
                    if plan_event:
                        yield plan_event

                    result_event = _result_event_for_update(node_name, node_update)
                    if result_event:
                        yield result_event

        except Exception as exc:
            latency_ms = (time.perf_counter() - started) * 1000
            error_state = dict(streamed_state)
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
            yield {
                "type": "error",
                "message": "抱歉，处理过程中出现异常，请稍后再试。",
                "detail": str(exc),
                "trace_id": trace_id,
            }
            return

        latency_ms = (time.perf_counter() - started) * 1000
        result = attach_turn_trace(
            streamed_state,
            trace_id=trace_id,
            user_input=user_input,
            latency_ms=latency_ms,
        )
        await store.set(resolved_session_id, result)

        response_text = result.get("final_response") or "[ERROR]Supervisor workflow did not generate a response."
        done_event = {
            "type": "done",
            "trace_id": trace_id,
            "session_id": resolved_session_id,
            "latency_ms": round(latency_ms, 2),
        }

    for chunk in _chunk_text(response_text):
        yield {"type": "final_delta", "text": chunk}

    if done_event:
        yield done_event


def _merge_stream_update(state: SupervisorState, update: dict[str, Any]) -> SupervisorState:
    """Mirror the small reducer set used by the supervisor graph for streamed updates."""
    merged: SupervisorState = dict(state)
    for key, value in update.items():
        if key == "messages":
            merged[key] = list(merged.get(key) or []) + list(value or [])
        elif key == "tool_results":
            merged[key] = {**(merged.get(key) or {}), **(value or {})}
        elif key in {"turn_results", "trace_history", "task_stack"}:
            merged[key] = list(value or [])
        else:
            merged[key] = value
    return merged


def _progress_event_for_node(
    node_name: str,
    state: SupervisorState,
    update: dict[str, Any],
) -> dict[str, Any] | None:
    stage, message = NODE_PROGRESS_MESSAGES.get(node_name, ("working", f"正在执行 {node_name}"))
    decision = state.get("route_decision") or {}
    event: dict[str, Any] = {
        "type": "progress",
        "stage": stage,
        "node": node_name,
        "message": message,
    }
    if decision.get("action"):
        event["action"] = decision.get("action")
    if update.get("active_agent") or state.get("active_agent"):
        event["agent"] = update.get("active_agent") or state.get("active_agent")
    return event


def _plan_event_if_changed(
    state: SupervisorState,
    last_signature: tuple[Any, ...] | None,
) -> tuple[dict[str, Any] | None, tuple[Any, ...] | None]:
    plan = state.get("execution_plan") or {}
    tasks = plan.get("tasks") or []
    if not tasks:
        return None, last_signature

    # A plan is announced once. Task transitions already have progress events.
    signature = (plan.get("plan_id"),)
    if signature == last_signature:
        return None, last_signature

    return (
        {
            "type": "plan",
            "message": "已生成处理计划",
            "goal": plan.get("goal"),
            "status": plan.get("status"),
            "current_task_id": plan.get("current_task_id"),
            "tasks": [
                {
                    "task_id": task.get("task_id"),
                    "agent": task.get("agent"),
                    "action": task.get("action"),
                    "status": task.get("status"),
                    "reason": task.get("reason"),
                }
                for task in tasks
                if isinstance(task, dict)
            ],
        },
        signature,
    )


def _persisted_plan_signature(state: SupervisorState) -> tuple[Any, ...] | None:
    plan_id = (state.get("execution_plan") or {}).get("plan_id")
    return (plan_id,) if plan_id else None


def _result_event_for_update(
    node_name: str,
    update: dict[str, Any],
) -> dict[str, Any] | None:
    if node_name not in {
        "consultation_subgraph",
        "availability_subgraph",
        "booking_subgraph",
        "recommendation_subgraph",
    }:
        return None
    result = update.get("last_agent_result") or {}
    if not isinstance(result, dict) or not result:
        return None
    if result.get("suppress_response") or result.get("visibility") == "internal":
        return None
    return {
        "type": "tool_result",
        "agent": result.get("agent_name"),
        "status": result.get("status"),
        "result_type": result.get("result_type"),
        "response_type": result.get("response_type"),
        "message": _safe_result_message(result),
        "requires_user_input": result.get("requires_user_input", False),
        "next_expected_user_action": result.get("next_expected_user_action"),
    }


def _safe_result_message(result: dict[str, Any]) -> str:
    agent = result.get("agent_name") or "agent"
    result_type = result.get("result_type") or "result"
    if agent == "availability":
        return "已完成可预约时间查询"
    if agent == "booking":
        return "已完成预约信息校验"
    if agent == "recommendation":
        return "已完成推荐筛选"
    if agent == "consultation":
        return "已完成咨询结果整理"
    return f"已完成 {result_type}"


def _chunk_text(text: str, chunk_size: int = 24) -> list[str]:
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


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
