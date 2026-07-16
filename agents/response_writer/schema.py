"""Contracts for the final response writer."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class WriterInput(TypedDict, total=False):
    """Minimal state summary consumed by the response writer."""

    execution_plan: Dict[str, Any]
    turn_results: List[Dict[str, Any]]
    shared_focus_context: Dict[str, Any]
    completion_reason: Optional[str]
    next_expected_user_action: Optional[str]
    final_response: Optional[str]


class WriterOutput(TypedDict, total=False):
    """Rendered final response plus trace metadata."""

    final_response: Optional[str]
    selected_label: str
    rendered_result_count: int
    skipped_result_count: int
    writer_strategy: str
    input_summary: Dict[str, Any]


def build_writer_input(state: Dict[str, Any]) -> WriterInput:
    """Extract the stable writer-facing subset from Supervisor state."""
    plan = state.get("execution_plan") or {}
    return {
        "execution_plan": plan,
        "turn_results": list(state.get("turn_results") or []),
        "shared_focus_context": dict(state.get("shared_focus_context") or {}),
        "completion_reason": plan.get("completion_reason"),
        "next_expected_user_action": plan.get("next_expected_user_action"),
        "final_response": state.get("final_response"),
    }


def summarize_writer_input(writer_input: WriterInput) -> Dict[str, Any]:
    """Return a compact trace-safe writer input summary."""
    plan = writer_input.get("execution_plan") or {}
    results = writer_input.get("turn_results") or []
    return {
        "plan_id": plan.get("plan_id"),
        "plan_status": plan.get("status"),
        "completion_reason": writer_input.get("completion_reason"),
        "next_expected_user_action": writer_input.get("next_expected_user_action"),
        "result_count": len(results),
        "result_types": [result.get("result_type") for result in results],
        "agents": [result.get("agent_name") for result in results],
    }
