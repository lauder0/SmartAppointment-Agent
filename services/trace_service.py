"""Lightweight turn trace helpers for graph-backed conversations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


MAX_TRACE_HISTORY = 20


def new_trace_id() -> str:
    """Return a compact trace id suitable for logs and eval reports."""
    return f"trace_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"


def attach_turn_trace(
    state: Dict[str, Any],
    *,
    trace_id: str,
    user_input: str,
    latency_ms: float,
    error: str | None = None,
) -> Dict[str, Any]:
    """Attach the latest turn trace and keep a bounded per-session history."""
    traced_state = dict(state)
    trace = build_turn_trace(
        traced_state,
        trace_id=trace_id,
        user_input=user_input,
        latency_ms=latency_ms,
        error=error,
    )
    history = list(traced_state.get("trace_history") or [])
    history.append(trace)
    traced_state["turn_trace"] = trace
    traced_state["trace_history"] = history[-MAX_TRACE_HISTORY:]
    return traced_state


def build_turn_trace(
    state: Dict[str, Any],
    *,
    trace_id: str,
    user_input: str,
    latency_ms: float,
    error: str | None = None,
) -> Dict[str, Any]:
    decision = state.get("route_decision") or {}
    task_frame = state.get("task_frame") or {}
    last_result = state.get("last_agent_result") or {}
    tool_results = state.get("tool_results") or {}
    supervisor_response = tool_results.get("supervisor_response") or {}
    return {
        "trace_id": trace_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "session_id": state.get("session_id"),
        "user_id": state.get("user_id"),
        "user_input": user_input,
        "route_action": decision.get("action"),
        "route_reason": decision.get("reason"),
        "primary_intent": decision.get("primary_intent") or task_frame.get("primary_intent"),
        "secondary_intents": decision.get("secondary_intents") or task_frame.get("secondary_intents") or [],
        "task_type": decision.get("task_type") or task_frame.get("task_type"),
        "execution_policy": decision.get("execution_policy") or task_frame.get("execution_policy"),
        "active_agent": state.get("active_agent"),
        "active_task": state.get("active_task"),
        "last_agent": last_result.get("agent_name"),
        "last_result_type": last_result.get("result_type"),
        "last_response_type": last_result.get("response_type"),
        "booking_status": (state.get("booking") or {}).get("status"),
        "recommendation_status": (state.get("recommendation") or {}).get("status"),
        "availability_option_count": len((state.get("availability") or {}).get("options") or []),
        "execution_plan": _plan_summary(state.get("execution_plan")),
        "plan_review": tool_results.get("plan_review"),
        "writer": supervisor_response.get("writer"),
        "turn_results": summarize_turn_results(state.get("turn_results") or []),
        "tool_summary": summarize_tool_results(tool_results),
        "latency_ms": round(latency_ms, 2),
        "final_response_preview": _preview(state.get("final_response")),
        "error": error or state.get("error"),
    }


def summarize_turn_results(turn_results: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    """Return compact AgentResult summaries for trace views."""
    return [
        {
            "agent_name": result.get("agent_name"),
            "status": result.get("status"),
            "result_type": result.get("result_type"),
            "response_type": result.get("response_type"),
            "requires_user_input": result.get("requires_user_input"),
            "next_expected_user_action": result.get("next_expected_user_action"),
        }
        for result in turn_results
    ]


def summarize_tool_results(tool_results: Dict[str, Any]) -> Dict[str, Any]:
    """Return a compact, JSON-safe summary of tool and node results."""
    summary: Dict[str, Any] = {}
    for name, value in tool_results.items():
        if isinstance(value, dict):
            item: Dict[str, Any] = {}
            for key in ("success", "status", "reason", "action", "error", "message"):
                if key in value:
                    item[key] = _compact(value.get(key))
            metadata = value.get("metadata")
            if isinstance(metadata, dict):
                item["metadata"] = {
                    key: metadata.get(key)
                    for key in (
                        "tool_name",
                        "permission",
                        "risk_level",
                        "idempotent",
                        "retryable",
                        "requires_confirmation",
                    )
                    if key in metadata
                }
            data = value.get("data")
            if isinstance(data, dict):
                item["data_keys"] = sorted(str(key) for key in data.keys())
                if "documents" in data and isinstance(data["documents"], list):
                    item["document_count"] = len(data["documents"])
            if "selected" in value:
                item["selected"] = _compact(value.get("selected"))
            if "alternatives" in value and isinstance(value["alternatives"], list):
                item["alternative_count"] = len(value["alternatives"])
            summary[name] = item or {"type": "dict", "keys": sorted(str(key) for key in value.keys())}
        elif isinstance(value, list):
            summary[name] = {"type": "list", "count": len(value)}
        else:
            summary[name] = _compact(value)
    return summary


def _compact(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return _preview(value) if isinstance(value, str) else value
    if isinstance(value, dict):
        compacted = {}
        for key in ("id", "name", "technician_id", "technician_name", "service_type", "start_time"):
            if key in value:
                compacted[key] = value[key]
        return compacted or {"type": "dict", "keys": sorted(str(key) for key in value.keys())[:8]}
    if isinstance(value, list):
        return {"type": "list", "count": len(value)}
    return _preview(str(value))


def _plan_summary(plan: Dict[str, Any] | None) -> Dict[str, Any]:
    """Return a trace-safe snapshot without depending on supervisor internals."""
    plan = plan or {}
    tasks = plan.get("tasks") or []
    return {
        "plan_id": plan.get("plan_id"),
        "goal": plan.get("goal"),
        "status": plan.get("status"),
        "source": plan.get("source"),
        "current_task_id": plan.get("current_task_id"),
        "completed_task_ids": list(plan.get("completed_task_ids") or []),
        "waiting_task_id": plan.get("waiting_task_id"),
        "requires_user_input": plan.get("requires_user_input", False),
        "next_expected_user_action": plan.get("next_expected_user_action"),
        "completion_reason": plan.get("completion_reason"),
        "suggested_task_reviews": list(plan.get("suggested_task_reviews") or []),
        "tasks": [
            {
                "task_id": task.get("task_id"),
                "agent": task.get("agent"),
                "action": task.get("action"),
                "status": task.get("status"),
                "depends_on": list(task.get("depends_on") or []),
                "required": task.get("required", True),
                "reason": task.get("reason"),
                "result_ref": task.get("result_ref"),
            }
            for task in tasks
            if isinstance(task, dict)
        ],
    }


def _preview(value: Any, max_length: int = 180) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).replace("\n", "\\n")
    if len(text) <= max_length:
        return text
    return f"{text[:max_length]}..."
