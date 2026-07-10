"""Shared helpers for specialist subgraph adapters."""

from __future__ import annotations

from typing import Any, Dict


def agent_result(
    agent_name: str,
    status: str,
    result_type: str,
    message: str | None = None,
    state_updates: Dict[str, Any] | None = None,
    handoff_suggestion: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    return {
        "agent_name": agent_name,
        "status": status,
        "result_type": result_type,
        "message": message,
        "state_updates": state_updates or {},
        "handoff_suggestion": handoff_suggestion or {"target_agent": None, "reason": "", "payload": {}},
    }


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
