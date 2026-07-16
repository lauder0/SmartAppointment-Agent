"""Plan completion and next-task checks for Supervisor."""

from __future__ import annotations

from typing import Any, Dict

from config.time_utils import utc_now_iso

from agents.supervisor.planning.plan_schema import ExecutionPlan, PlanTask, normalize_execution_plan


WAITING_STATUSES = {"waiting_user", "awaiting_selection", "needs_availability"}
FAILED_STATUSES = {"failed", "blocked", "exhausted"}


def result_task_status(result: Dict[str, Any] | None) -> str:
    status = str((result or {}).get("status") or "completed")
    if status in WAITING_STATUSES:
        return "waiting_user"
    if status in FAILED_STATUSES:
        return "failed" if status != "blocked" else "blocked"
    return "completed"


def complete_current_task_from_result(state: Dict[str, Any]) -> ExecutionPlan:
    """Mark the current running task according to last_agent_result."""
    plan = normalize_execution_plan(state.get("execution_plan"))
    current_id = plan.get("current_task_id")
    if not current_id:
        return plan

    result = state.get("last_agent_result") or {}
    task_status = result_task_status(result)
    turn_results = list(state.get("turn_results") or [])
    result_ref = f"turn_results[{max(len(turn_results) - 1, 0)}]" if turn_results else None

    completed = set(plan.get("completed_task_ids") or [])
    for task in plan.get("tasks") or []:
        if task.get("task_id") != current_id:
            continue
        task["status"] = task_status
        task["result_ref"] = result_ref
        if result.get("error"):
            task["error"] = str(result.get("error"))
        break

    if task_status == "completed":
        completed.add(str(current_id))
        plan["completed_task_ids"] = sorted(completed)
    elif task_status == "waiting_user":
        plan["status"] = "waiting_user"
        plan["waiting_task_id"] = current_id
        plan["requires_user_input"] = True
        plan["next_expected_user_action"] = _expected_user_action(result)
    elif task_status in {"blocked", "failed"}:
        plan["status"] = task_status
        plan["blocked_reason"] = result.get("error") or result.get("result_type") or task_status

    plan["updated_at"] = utc_now_iso()
    return plan


def start_next_task(plan: Dict[str, Any]) -> ExecutionPlan:
    """Set the next runnable pending task as current/running."""
    normalized = normalize_execution_plan(plan)
    if normalized.get("status") in {"waiting_user", "blocked", "failed"}:
        return normalized

    next_task = next_runnable_task(normalized)
    if not next_task:
        normalized["status"] = "completed"
        normalized["current_task_id"] = None
        normalized["completion_reason"] = "all_required_tasks_completed"
        normalized["updated_at"] = utc_now_iso()
        return normalized

    for task in normalized.get("tasks") or []:
        if task.get("task_id") == next_task.get("task_id"):
            task["status"] = "running"
            normalized["current_task_id"] = task.get("task_id")
            normalized["status"] = "running"
            normalized["updated_at"] = utc_now_iso()
            return normalized
    return normalized


def next_runnable_task(plan: Dict[str, Any]) -> PlanTask | None:
    normalized = normalize_execution_plan(plan)
    completed = set(normalized.get("completed_task_ids") or [])
    for task in normalized.get("tasks") or []:
        if task.get("status") != "pending":
            continue
        depends_on = set(task.get("depends_on") or [])
        if depends_on.issubset(completed):
            return task
    return None


def should_continue_plan(state: Dict[str, Any]) -> bool:
    """Return true when the current plan has a safe next pending task."""
    last_result = state.get("last_agent_result") or {}
    if result_task_status(last_result) in {"waiting_user", "blocked", "failed"}:
        return False
    plan = normalize_execution_plan(state.get("execution_plan"))
    current_id = plan.get("current_task_id")
    if current_id:
        completed = set(plan.get("completed_task_ids") or [])
        completed.add(str(current_id))
        plan["completed_task_ids"] = sorted(completed)
    return next_runnable_task(plan) is not None


def _expected_user_action(result: Dict[str, Any]) -> str | None:
    explicit = result.get("next_expected_user_action")
    if explicit:
        return str(explicit)
    result_type = result.get("result_type")
    if result_type == "technician_recommended":
        return "accept_recommendation | choose_alternative | change_preference"
    if str(result_type or "").startswith("booking"):
        return "provide_missing_slots | confirm_booking | modify_booking"
    return None
