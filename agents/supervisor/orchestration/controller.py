"""Controller helpers for executing Supervisor plans through existing subgraphs."""

from __future__ import annotations

from typing import Any, Dict, List

from .agent_registry import agent_for_action, task_for_action
from agents.supervisor.planning.plan_schema import ExecutionPlan, PlanTask, make_plan_task, normalize_execution_plan


def route_decision_from_current_task(plan: Dict[str, Any], fallback: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build the route decision consumed by the current LangGraph subgraph."""
    task = current_task(plan)
    fallback = fallback or {}
    if not task:
        return fallback or {"action": "unsupported", "reason": "no_current_plan_task"}

    original = ((task.get("input") or {}).get("route_decision") or fallback or {}).copy()
    action = task.get("action") or original.get("action") or "unsupported"
    return {
        **original,
        "action": action,
        "reason": task.get("reason") or original.get("reason") or "execution_plan_task",
        "source": "execution_plan",
        "task_id": task.get("task_id"),
        "plan_id": plan.get("plan_id"),
        "planned_agent": task.get("agent") or agent_for_action(action),
        "planned_action": action,
        "trace": {
            **(original.get("trace") or {}),
            "plan_id": plan.get("plan_id"),
            "task_id": task.get("task_id"),
            "planned_agent": task.get("agent"),
            "planned_action": action,
        },
    }


def current_task(plan: Dict[str, Any] | None) -> PlanTask | None:
    normalized = normalize_execution_plan(plan)
    current_id = normalized.get("current_task_id")
    if not current_id:
        return None
    for task in normalized.get("tasks") or []:
        if task.get("task_id") == current_id:
            return task
    return None


def active_agent_for_plan(plan: Dict[str, Any], fallback_action: str | None = None) -> str:
    task = current_task(plan)
    if task:
        return task.get("agent") or agent_for_action(task.get("action"))
    return agent_for_action(fallback_action)


def active_task_for_plan(plan: Dict[str, Any], fallback_action: str | None = None) -> str | None:
    task = current_task(plan)
    if task:
        return task_for_action(task.get("action"))
    return task_for_action(fallback_action)


def append_suggested_tasks(plan: Dict[str, Any], result: Dict[str, Any] | None) -> ExecutionPlan:
    """Append safe suggested_next_tasks from AgentResult into the plan."""
    normalized = normalize_execution_plan(plan)
    suggestions = list((result or {}).get("suggested_next_tasks") or [])
    if not suggestions:
        return normalized

    existing_actions = {(task.get("agent"), task.get("action")) for task in normalized.get("tasks") or []}
    reviews = list(normalized.get("suggested_task_reviews") or [])
    next_index = len(normalized.get("tasks") or []) + 1
    completed_or_current = [
        task.get("task_id")
        for task in normalized.get("tasks") or []
        if task.get("status") in {"running", "completed"}
    ]
    depends_on = [completed_or_current[-1]] if completed_or_current else []

    for suggestion in suggestions:
        review = _suggestion_review(suggestion, result)
        if not suggestion.get("auto_continue"):
            reviews.append({**review, "decision": "rejected", "reason": "requires_user_acceptance"})
            continue
        action = suggestion.get("action")
        agent = suggestion.get("agent") or agent_for_action(action)
        if not action or (agent, action) in existing_actions:
            reviews.append(
                {
                    **review,
                    "agent": agent,
                    "action": action,
                    "decision": "rejected",
                    "reason": "missing_or_duplicate_action",
                }
            )
            continue
        if action in {"confirm_booking", "cancel_booking"}:
            reviews.append(
                {
                    **review,
                    "agent": agent,
                    "action": action,
                    "decision": "rejected",
                    "reason": "booking_write_action_blocked",
                }
            )
            continue
        task = make_plan_task(
            next_index,
            agent=agent,
            action=action,
            reason=suggestion.get("reason") or "agent_suggested_next_task",
            depends_on=depends_on,
            input={
                "suggestion": suggestion,
                "route_decision": {
                    "action": action,
                    "reason": suggestion.get("reason") or "agent_suggested_next_task",
                    "source": "agent_suggested_next_tasks",
                    "task_type": suggestion.get("task_type") or "",
                    "primary_intent": suggestion.get("primary_intent") or action,
                    "secondary_intents": suggestion.get("secondary_intents") or [],
                    "slot_updates": suggestion.get("input") or {},
                    "execution_policy": "supervisor_plan_suggestion",
                },
            },
            source="agent_suggestion",
        )
        normalized.setdefault("tasks", []).append(task)
        existing_actions.add((agent, action))
        reviews.append(
            {
                **review,
                "agent": agent,
                "action": action,
                "decision": "accepted",
                "reason": "auto_continue_allowed",
                "task_id": task.get("task_id"),
            }
        )
        next_index += 1
    normalized["suggested_task_reviews"] = reviews
    return normalized


def _suggestion_review(suggestion: Dict[str, Any], result: Dict[str, Any] | None) -> Dict[str, Any]:
    return {
        "from_agent": (result or {}).get("agent_name"),
        "from_result_type": (result or {}).get("result_type"),
        "agent": suggestion.get("agent"),
        "action": suggestion.get("action"),
        "auto_continue": bool(suggestion.get("auto_continue")),
        "suggestion_reason": suggestion.get("reason"),
    }


def task_trace(plan: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_execution_plan(plan)
    return {
        "plan_id": normalized.get("plan_id"),
        "plan_status": normalized.get("status"),
        "current_task_id": normalized.get("current_task_id"),
        "executed_tasks": [
            {
                "task_id": task.get("task_id"),
                "agent": task.get("agent"),
                "action": task.get("action"),
                "status": task.get("status"),
                "result_ref": task.get("result_ref"),
            }
            for task in normalized.get("tasks") or []
            if task.get("status") in {"completed", "waiting_user", "blocked", "failed"}
        ],
        "pending_tasks": [
            {
                "task_id": task.get("task_id"),
                "agent": task.get("agent"),
                "action": task.get("action"),
                "status": task.get("status"),
            }
            for task in normalized.get("tasks") or []
            if task.get("status") in {"pending", "running"}
        ],
        "suggested_task_reviews": normalized.get("suggested_task_reviews", []),
    }
