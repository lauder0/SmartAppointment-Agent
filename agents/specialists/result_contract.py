"""Shared helpers and result contracts for specialist subgraph adapters."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class SpecialistResult(TypedDict, total=False):
    """Structured result contract from a specialist back to Supervisor."""

    version: str
    agent_name: str
    status: str
    result_type: str
    response_type: str
    facts: Dict[str, Any]
    message: Optional[str]
    state_updates: Dict[str, Any]
    tool_results: Dict[str, Any]
    suggested_next_tasks: List[Dict[str, Any]]
    requires_user_input: bool
    next_expected_user_action: Optional[str]
    error: Optional[str]


def agent_result(
    agent_name: str,
    status: str,
    result_type: str,
    message: str | None = None,
    state_updates: Dict[str, Any] | None = None,
    *,
    response_type: str | None = None,
    facts: Dict[str, Any] | None = None,
    tool_results: Dict[str, Any] | None = None,
    error: str | None = None,
    suggested_next_tasks: List[Dict[str, Any]] | None = None,
    requires_user_input: bool = False,
    next_expected_user_action: str | None = None,
) -> SpecialistResult:
    resolved_response_type = response_type or _response_type_for_result(result_type)
    return {
        "version": f"{agent_name}_result.v1",
        "agent_name": agent_name,
        "status": status,
        "result_type": result_type,
        "response_type": resolved_response_type,
        "facts": {**_facts_from_state_updates(state_updates), **(facts or {})},
        "message": message,
        "state_updates": state_updates or {},
        "tool_results": tool_results or {},
        "suggested_next_tasks": suggested_next_tasks or [],
        "requires_user_input": requires_user_input,
        "next_expected_user_action": next_expected_user_action,
        "error": error,
    }


def append_turn_result(
    turn_results: List[Dict[str, Any]] | None,
    result: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    """Append a specialist result once for the current user turn."""
    results = list(turn_results or [])
    if not result:
        return results
    if results and _same_result(results[-1], result):
        return results
    results.append(result)
    return results


def attach_agent_result(
    update: Dict[str, Any],
    state: Dict[str, Any],
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """Attach the latest specialist result and keep a per-turn result trail."""
    update["last_agent_result"] = result
    update["turn_results"] = append_turn_result(state.get("turn_results"), result)
    return update


def _same_result(left: Dict[str, Any], right: Dict[str, Any]) -> bool:
    return (
        left.get("agent_name") == right.get("agent_name")
        and left.get("status") == right.get("status")
        and left.get("result_type") == right.get("result_type")
        and left.get("message") == right.get("message")
    )


def _response_type_for_result(result_type: str) -> str:
    mapping = {
        "knowledge_answer": "knowledge_answer",
        "service_catalog": "service_catalog",
        "availability_result": "availability_result",
        "availability_failed": "availability_failed",
        "booking_confirmation": "booking_confirmation",
        "booking_recommendation": "booking_recommendation",
        "booking_created": "booking_success",
        "booking_missing": "booking_missing_slots",
        "booking_cancelled": "booking_cancelled",
        "booking_unclear_confirmation": "booking_unclear_confirmation",
        "booking_guard_missing": "booking_guard_missing",
        "booking_guard_invalid": "booking_guard_invalid",
        "booking_guard_time_invalid": "booking_guard_time_invalid",
        "booking_guard_technician_unavailable": "booking_guard_technician_unavailable",
        "booking_failed": "booking_failed",
        "technician_recommended": "technician_recommendation",
        "service_recommended": "service_recommendation",
        "recommendation_needs_availability": "technician_recommendation_failed",
        "recommendation_exhausted": "technician_recommendation_failed",
        "ask_clarification": "clarification",
        "unsupported": "unsupported",
    }
    return mapping.get(result_type, result_type)


def _facts_from_state_updates(state_updates: Dict[str, Any] | None) -> Dict[str, Any]:
    updates = state_updates or {}
    facts: Dict[str, Any] = {}
    for key in ("consultation", "availability", "booking", "recommendation", "last_completed_booking"):
        if key in updates:
            facts[key] = updates[key]
    return facts


def apply_update(state: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    next_state = dict(state)
    for key, value in (update or {}).items():
        if key == "tool_results":
            next_state[key] = {**(next_state.get(key) or {}), **(value or {})}
        elif key == "messages":
            next_state[key] = list(next_state.get(key) or []) + list(value or [])
        else:
            next_state[key] = value
    return next_state

