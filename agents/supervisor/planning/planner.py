"""Supervisor planner.

The production path is deterministic and inspectable. A constrained LLM
planner can be enabled for complex/ambiguous plans, but its output is validated
against the same agent/action allowlist and never bypasses Booking guards.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, List, Tuple

from config.model_provider import create_chat_model
from config.time_utils import utc_now_iso

from .plan_schema import ExecutionPlan, PlanTask, make_plan_task, new_plan_id, normalize_execution_plan
from .prompts import supervisor_planner_prompt
from agents.supervisor.orchestration.agent_registry import ACTION_TO_AGENT, BOOKING_WRITE_ACTIONS, agent_for_action


ACTION_ALIASES = {
    "answer_knowledge": "answer_knowledge",
    "query_availability": "query_availability",
    "generate_recommendation": "generate_recommendation",
    "recommend_service": "recommend_service",
    "answer_recommendation": "generate_recommendation",
    "replace_recommendation": "replace_recommendation",
    "start_or_continue_booking": "start_or_continue_booking",
    "modify_booking": "modify_booking",
    "confirm_booking": "confirm_booking",
    "cancel_booking": "cancel_booking",
    "select_recommended_technician": "select_recommended_technician",
    "ask_clarification": "ask_clarification",
    "unsupported": "unsupported",
}


TASK_TYPE_ACTIONS: Dict[str, List[str]] = {
    "knowledge_consultation": ["answer_knowledge"],
    "availability_query": ["query_availability"],
    "service_recommendation": ["recommend_service"],
    "technician_recommendation": ["generate_recommendation"],
    "recommendation_replacement": ["replace_recommendation"],
    "recommendation_selection": ["select_recommended_technician"],
    "booking_creation": ["start_or_continue_booking"],
    "booking_modification": ["start_or_continue_booking"],
    "booking_confirmation": ["confirm_booking"],
    "booking_cancellation": ["cancel_booking"],
    "clarification": ["ask_clarification"],
    "fallback_clarification": ["ask_clarification"],
    "fallback_smalltalk": ["unsupported"],
    "multi_intent": ["ask_clarification"],
    "unsupported": ["unsupported"],
}


def build_execution_plan(
    *,
    task_frame: Dict[str, Any] | None,
    route_decision: Dict[str, Any] | None,
    state: Dict[str, Any] | None = None,
) -> ExecutionPlan:
    """Build an execution plan from understanding output and current state."""
    task_frame = task_frame or {}
    route_decision = route_decision or {}
    state = state or {}
    actions = _actions_for_decision(task_frame, route_decision, state)
    tasks = _tasks_from_actions(actions, route_decision, task_frame)
    now = utc_now_iso()
    first_task_id = tasks[0]["task_id"] if tasks else None
    if first_task_id:
        tasks[0]["status"] = "running"

    return {
        "plan_id": new_plan_id(),
        "goal": _goal_for_plan(task_frame, route_decision),
        "status": "running" if tasks else "completed",
        "source": route_decision.get("source") or task_frame.get("source") or "deterministic_planner",
        "created_at": now,
        "updated_at": now,
        "tasks": tasks,
        "current_task_id": first_task_id,
        "completed_task_ids": [],
        "waiting_task_id": None,
        "blocked_reason": None,
        "completion_reason": None if tasks else "no_tasks",
        "requires_user_input": False,
        "next_expected_user_action": None,
        "suggested_task_reviews": [],
    }


async def build_execution_plan_with_optional_llm(
    *,
    task_frame: Dict[str, Any] | None,
    route_decision: Dict[str, Any] | None,
    state: Dict[str, Any] | None = None,
) -> ExecutionPlan:
    """Build a deterministic plan, optionally upgraded by a validated LLM plan."""
    deterministic = build_execution_plan(
        task_frame=task_frame,
        route_decision=route_decision,
        state=state,
    )
    task_frame = task_frame or {}
    route_decision = route_decision or {}
    state = state or {}
    if not _should_call_llm_planner(task_frame, route_decision, deterministic):
        return deterministic

    try:
        prompt = supervisor_planner_prompt(
            task_frame=task_frame,
            focus_context=state.get("shared_focus_context") or state.get("focus_context") or {},
            allowed_agents=set(ACTION_TO_AGENT.values()),
            allowed_actions=set(ACTION_ALIASES.values()),
        )
        message = await create_chat_model(temperature=0).ainvoke(prompt)
        parsed = _extract_json_object(str(getattr(message, "content", "")))
        llm_plan = _validate_llm_execution_plan(
            parsed,
            task_frame=task_frame,
            route_decision=route_decision,
            fallback=deterministic,
        )
        return llm_plan or deterministic
    except Exception:
        return deterministic


def _actions_for_decision(
    task_frame: Dict[str, Any],
    route_decision: Dict[str, Any],
    state: Dict[str, Any],
) -> List[str]:
    action = _normalize_action(route_decision.get("action"))
    task_type = str(route_decision.get("task_type") or task_frame.get("task_type") or "")
    secondary_intents = set(route_decision.get("secondary_intents") or task_frame.get("secondary_intents") or [])

    if action == "answer_knowledge" and task_type == "service_recommendation":
        action = "recommend_service"

    if route_decision.get("execution_policy") == "query_first_plan":
        actions = _query_first_actions(action, task_type, secondary_intents, state, route_decision)
    elif task_type == "recommendation_before_booking":
        actions = _recommendation_before_booking_actions(state, route_decision)
    else:
        actions = TASK_TYPE_ACTIONS.get(task_type)
        if not actions:
            actions = [action]

    return _dedupe_actions([item for item in actions if item])


def _query_first_actions(
    action: str,
    task_type: str,
    secondary_intents: set[str],
    state: Dict[str, Any],
    route_decision: Dict[str, Any],
) -> List[str]:
    """Expand query-first multi-intent semantics into explicit plan tasks."""
    wants_recommendation = bool({"recommend_technician", "technician_recommendation"} & secondary_intents) or (
        task_type == "recommendation_before_booking"
    )
    wants_booking = bool({"start_booking", "booking_creation"} & secondary_intents) or task_type in {
        "booking_creation",
        "booking_modification",
    }
    wants_availability = "availability_query" in secondary_intents or action == "query_availability"

    if action == "answer_knowledge":
        if wants_availability and wants_recommendation:
            return ["answer_knowledge", "query_availability", "generate_recommendation"]
        if wants_availability and wants_booking:
            return ["answer_knowledge", "query_availability", "start_or_continue_booking"]
        if wants_recommendation:
            return ["answer_knowledge", *_recommendation_before_booking_actions(state, route_decision)]
        if wants_booking:
            return ["answer_knowledge", "start_or_continue_booking"]
        if wants_availability:
            return ["answer_knowledge", "query_availability"]
        return ["answer_knowledge"]

    if action == "query_availability":
        if wants_recommendation:
            return ["query_availability", "generate_recommendation"]
        if wants_booking:
            return ["query_availability", "start_or_continue_booking"]
        return ["query_availability"]

    return TASK_TYPE_ACTIONS.get(task_type) or [action]


def _recommendation_before_booking_actions(state: Dict[str, Any], route_decision: Dict[str, Any]) -> List[str]:
    availability = state.get("availability") or {}
    has_candidates = bool(availability.get("options"))
    if has_candidates and route_decision.get("action") == "generate_recommendation":
        return ["generate_recommendation"]
    return ["query_availability", "generate_recommendation"]


def _tasks_from_actions(
    actions: Iterable[str],
    route_decision: Dict[str, Any],
    task_frame: Dict[str, Any],
) -> List[PlanTask]:
    tasks: List[PlanTask] = []
    previous_task_id = None
    step_metadata = _planned_step_metadata(route_decision)
    used_steps: set[int] = set()
    for index, action in enumerate(actions, start=1):
        normalized_action = _normalize_action(action)
        task_decision = _route_decision_for_step(
            route_decision=route_decision,
            action=normalized_action,
            step_metadata=step_metadata,
            used_steps=used_steps,
        )
        task = make_plan_task(
            index,
            agent=agent_for_action(normalized_action),
            action=normalized_action,
            reason=_reason_for_action(normalized_action, task_decision),
            depends_on=[previous_task_id] if previous_task_id else [],
            input={
                "route_decision": task_decision,
                "task_frame": task_frame,
            },
        )
        tasks.append(task)
        previous_task_id = task["task_id"]
    return tasks


def _normalize_action(action: Any) -> str:
    return ACTION_ALIASES.get(str(action or ""), "unsupported")


def _planned_step_metadata(route_decision: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return route metadata for the initial route decision."""
    steps: List[Dict[str, Any]] = []
    if route_decision.get("action"):
        steps.append(
            {
                "action": route_decision.get("action"),
                "reason": route_decision.get("reason"),
                "task_type": route_decision.get("task_type"),
                "primary_intent": route_decision.get("primary_intent"),
                "secondary_intents": route_decision.get("secondary_intents") or [],
                "execution_policy": route_decision.get("execution_policy"),
            }
        )
    return steps


def _route_decision_for_step(
    *,
    route_decision: Dict[str, Any],
    action: str,
    step_metadata: List[Dict[str, Any]],
    used_steps: set[int],
) -> Dict[str, Any]:
    """Build a task-local route decision for a planned step."""
    for index, step in enumerate(step_metadata):
        if index in used_steps:
            continue
        if _normalize_action(step.get("action")) != action:
            continue
        used_steps.add(index)
        return {
            **route_decision,
            **{key: value for key, value in step.items() if value not in (None, "", [], {})},
            "action": action,
        }
    return {**route_decision, "action": action}


def _dedupe_actions(actions: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen: set[str] = set()
    for action in actions:
        if action and action not in seen:
            result.append(action)
            seen.add(action)
    return result


def _reason_for_action(action: str, route_decision: Dict[str, Any]) -> str:
    if action == route_decision.get("action"):
        return str(route_decision.get("reason") or "understanding_decision")
    if action == "query_availability":
        return "prepare_facts_before_downstream_task"
    if action == "generate_recommendation":
        return "rank_available_candidates"
    if action == "recommend_service":
        return "recommend_service_from_need"
    return "planned_followup_task"


def _goal_for_plan(task_frame: Dict[str, Any], route_decision: Dict[str, Any]) -> str:
    task_type = route_decision.get("task_type") or task_frame.get("task_type") or "unknown_task"
    primary = route_decision.get("primary_intent") or task_frame.get("primary_intent") or ""
    return f"{task_type}:{primary}" if primary else str(task_type)


def action_agent_pairs(plan: Dict[str, Any]) -> List[Tuple[str, str]]:
    return [(task.get("action", ""), task.get("agent", "")) for task in plan.get("tasks") or []]


def _should_call_llm_planner(
    task_frame: Dict[str, Any],
    route_decision: Dict[str, Any],
    deterministic: Dict[str, Any],
) -> bool:
    if os.getenv("ENABLE_SUPERVISOR_LLM_PLANNER", "").strip().lower() not in {"1", "true", "yes"}:
        return False
    task_type = str(route_decision.get("task_type") or task_frame.get("task_type") or "")
    action = str(route_decision.get("action") or "")
    secondary_count = len(route_decision.get("secondary_intents") or task_frame.get("secondary_intents") or [])
    return (
        task_type == "multi_intent"
        or action == "unsupported"
        or secondary_count >= 3
        or len(deterministic.get("tasks") or []) >= 4
    )


def _validate_llm_execution_plan(
    parsed: Dict[str, Any] | None,
    *,
    task_frame: Dict[str, Any],
    route_decision: Dict[str, Any],
    fallback: Dict[str, Any],
) -> ExecutionPlan | None:
    if not isinstance(parsed, dict):
        return None
    raw_tasks = parsed.get("tasks")
    if not isinstance(raw_tasks, list) or not raw_tasks:
        return None

    tasks: List[PlanTask] = []
    previous_task_id = None
    initial_action = _normalize_action(route_decision.get("action"))
    seen_actions: set[str] = set()
    for index, raw_task in enumerate(raw_tasks, start=1):
        if not isinstance(raw_task, dict):
            return None
        action = _normalize_action(raw_task.get("action"))
        if action == "unsupported" and raw_task.get("action") != "unsupported":
            return None
        if action in BOOKING_WRITE_ACTIONS and action != initial_action:
            return None
        if action in seen_actions:
            return None
        seen_actions.add(action)
        agent = raw_task.get("agent") or agent_for_action(action)
        if agent != agent_for_action(action):
            return None
        task = make_plan_task(
            index,
            agent=agent,
            action=action,
            reason=str(raw_task.get("reason") or "llm_supervisor_planner"),
            depends_on=[previous_task_id] if previous_task_id else [],
            input={
                "route_decision": {**route_decision, "action": action, "source": "llm_supervisor_planner"},
                "task_frame": task_frame,
                "llm_task_input": raw_task.get("input") if isinstance(raw_task.get("input"), dict) else {},
            },
            source="llm_supervisor_planner",
        )
        tasks.append(task)
        previous_task_id = task["task_id"]

    now = utc_now_iso()
    tasks[0]["status"] = "running"
    plan = normalize_execution_plan(
        {
            **fallback,
            "plan_id": new_plan_id(),
            "goal": str(parsed.get("goal") or fallback.get("goal") or _goal_for_plan(task_frame, route_decision)),
            "status": "running",
            "source": "llm_supervisor_planner",
            "created_at": now,
            "updated_at": now,
            "tasks": tasks,
            "current_task_id": tasks[0]["task_id"],
            "completed_task_ids": [],
            "waiting_task_id": None,
            "blocked_reason": None,
            "completion_reason": None,
            "requires_user_input": False,
            "next_expected_user_action": None,
            "suggested_task_reviews": [],
        }
    )
    return plan


def _extract_json_object(text: str) -> Dict[str, Any] | None:
    content = (text or "").strip()
    if not content:
        return None
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", content, flags=re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None
