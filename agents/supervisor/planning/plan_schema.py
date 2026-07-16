"""Execution-plan contract for Supervisor-driven multi-agent orchestration."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional, TypedDict

from config.time_utils import utc_now_iso


PLAN_STATUSES = {"pending", "running", "waiting_user", "completed", "blocked", "failed"}
TASK_STATUSES = {"pending", "running", "completed", "waiting_user", "blocked", "failed", "skipped"}


class PlanTask(TypedDict, total=False):
    task_id: str
    agent: str
    action: str
    status: str
    depends_on: List[str]
    required: bool
    input: Dict[str, Any]
    result_ref: Optional[str]
    error: Optional[str]
    reason: str
    source: str


class ExecutionPlan(TypedDict, total=False):
    plan_id: str
    goal: str
    status: str
    source: str
    created_at: str
    updated_at: str
    tasks: List[PlanTask]
    current_task_id: Optional[str]
    completed_task_ids: List[str]
    waiting_task_id: Optional[str]
    blocked_reason: Optional[str]
    completion_reason: Optional[str]
    requires_user_input: bool
    next_expected_user_action: Optional[str]
    suggested_task_reviews: List[Dict[str, Any]]


def default_execution_plan() -> ExecutionPlan:
    now = utc_now_iso()
    return {
        "plan_id": "",
        "goal": "",
        "status": "pending",
        "source": "",
        "created_at": now,
        "updated_at": now,
        "tasks": [],
        "current_task_id": None,
        "completed_task_ids": [],
        "waiting_task_id": None,
        "blocked_reason": None,
        "completion_reason": None,
        "requires_user_input": False,
        "next_expected_user_action": None,
        "suggested_task_reviews": [],
    }


def new_plan_id() -> str:
    return f"plan_{uuid.uuid4().hex[:12]}"


def make_plan_task(
    index: int,
    *,
    agent: str,
    action: str,
    reason: str = "",
    depends_on: List[str] | None = None,
    required: bool = True,
    input: Dict[str, Any] | None = None,
    source: str = "deterministic_planner",
) -> PlanTask:
    return {
        "task_id": f"t{index}",
        "agent": agent,
        "action": action,
        "status": "pending",
        "depends_on": depends_on or [],
        "required": required,
        "input": input or {},
        "result_ref": None,
        "error": None,
        "reason": reason,
        "source": source,
    }


def normalize_execution_plan(raw: Dict[str, Any] | None) -> ExecutionPlan:
    plan = default_execution_plan()
    if raw:
        plan.update(raw)
    plan["tasks"] = [normalize_plan_task(task) for task in plan.get("tasks") or []]
    plan["completed_task_ids"] = list(plan.get("completed_task_ids") or [])
    plan["suggested_task_reviews"] = list(plan.get("suggested_task_reviews") or [])
    if plan.get("status") not in PLAN_STATUSES:
        plan["status"] = "pending"
    return plan


def normalize_plan_task(raw: Dict[str, Any] | None) -> PlanTask:
    task: PlanTask = {
        "task_id": "",
        "agent": "fallback",
        "action": "unsupported",
        "status": "pending",
        "depends_on": [],
        "required": True,
        "input": {},
        "result_ref": None,
        "error": None,
        "reason": "",
        "source": "",
    }
    if raw:
        task.update(raw)
    if task.get("status") not in TASK_STATUSES:
        task["status"] = "pending"
    task["depends_on"] = list(task.get("depends_on") or [])
    task["input"] = dict(task.get("input") or {})
    return task


def plan_summary(plan: Dict[str, Any] | None) -> Dict[str, Any]:
    normalized = normalize_execution_plan(plan)
    return {
        "plan_id": normalized.get("plan_id"),
        "goal": normalized.get("goal"),
        "status": normalized.get("status"),
        "source": normalized.get("source"),
        "current_task_id": normalized.get("current_task_id"),
        "completed_task_ids": normalized.get("completed_task_ids", []),
        "waiting_task_id": normalized.get("waiting_task_id"),
        "requires_user_input": normalized.get("requires_user_input", False),
        "next_expected_user_action": normalized.get("next_expected_user_action"),
        "completion_reason": normalized.get("completion_reason"),
        "suggested_task_reviews": normalized.get("suggested_task_reviews", []),
        "tasks": [
            {
                "task_id": task.get("task_id"),
                "agent": task.get("agent"),
                "action": task.get("action"),
                "status": task.get("status"),
                "depends_on": task.get("depends_on", []),
                "required": task.get("required", True),
                "reason": task.get("reason"),
                "result_ref": task.get("result_ref"),
            }
            for task in normalized.get("tasks", [])
        ],
    }
