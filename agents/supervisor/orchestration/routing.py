"""Routing functions for the 3.0 supervisor graph."""

from __future__ import annotations

from agents.supervisor.orchestration.completion import should_continue_plan
from agents.supervisor.planning.plan_schema import normalize_execution_plan
from agents.supervisor.state import SupervisorState


def route_supervisor_decision(state: SupervisorState) -> str:
    action = (state.get("route_decision") or {}).get("action")
    if action == "answer_knowledge":
        return "consultation"
    if action == "query_availability":
        return "availability"
    if action in {"recommend_service", "generate_recommendation", "answer_recommendation", "replace_recommendation"}:
        return "recommendation"
    if action in {
        "start_or_continue_booking",
        "modify_booking",
        "confirm_booking",
        "cancel_booking",
        "select_recommended_technician",
    }:
        return "booking"
    if action == "ask_clarification":
        return "fallback"
    return "fallback"


def route_after_agent_result(state: SupervisorState) -> str:
    """Route every specialist result back through Supervisor completion.

    In the target architecture, child agents never route directly to another
    child agent. They return AgentResult; Supervisor marks the current task,
    appends safe suggestions if needed, then either starts the next plan task
    or finishes the turn.
    """
    if _has_running_plan_task(state):
        return "continue"
    if should_continue_plan(state):
        return "continue"
    return "end"


def route_after_supervisor_continue(state: SupervisorState) -> str:
    """Route to the next planned agent or to the final response writer."""
    plan = normalize_execution_plan(state.get("execution_plan"))
    if plan.get("current_task_id"):
        return route_supervisor_decision(state)
    return "response"


def _has_running_plan_task(state: SupervisorState) -> bool:
    plan = normalize_execution_plan(state.get("execution_plan"))
    current_id = plan.get("current_task_id")
    if not current_id:
        return False
    for task in plan.get("tasks") or []:
        if task.get("task_id") == current_id and task.get("status") == "running":
            return True
    return False
