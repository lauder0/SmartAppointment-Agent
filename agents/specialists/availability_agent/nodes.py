"""Internal nodes for the availability specialist agent."""

from __future__ import annotations

from agents.specialists.availability_agent.actions import availability_query_node
from agents.supervisor.state import (
    SupervisorState,
    merge_agent_action_update,
    state_for_agent_actions,
)
from agents.specialists.result_contract import agent_result, attach_agent_result

from .state import normalize_availability_state, status_from_result


async def query_realtime_schedule_node(state: SupervisorState) -> SupervisorState:
    action_update = await availability_query_node(state_for_agent_actions(state))
    merged = merge_agent_action_update(state, action_update)
    availability = normalize_availability_state(merged.get("availability"))
    availability["status"] = status_from_result(availability)
    merged["availability"] = availability
    response_type = action_update.get("response_type") or "availability_result"
    response_facts = action_update.get("response_facts") or {}
    result_type = "availability_failed" if response_type == "availability_failed" else "availability_result"
    route_reason = (state.get("route_decision") or {}).get("reason")
    plan = state.get("execution_plan") or {}
    suppress_response = bool(availability.get("options")) and (
        route_reason == "prepare_candidates_for_recommendation"
        or _plan_has_recommendation_task(plan)
    )
    result = agent_result(
        "availability",
        availability["status"],
        result_type,
        None,
        {"availability": availability},
        response_type=response_type,
        facts=response_facts,
        suggested_next_tasks=_availability_suggested_next_tasks(route_reason, availability, plan),
    )
    if suppress_response:
        result["suppress_response"] = True
        result["visibility"] = "internal"
    attach_agent_result(merged, state, result)
    return merged


def _availability_suggested_next_tasks(
    route_reason: str | None,
    availability: dict,
    plan: dict | None = None,
) -> list[dict]:
    options = availability.get("options") or []
    if not options:
        return []

    if route_reason == "prepare_candidates_for_recommendation" and not _plan_has_recommendation_task(plan):
        return [
            {
                "agent": "recommendation",
                "action": "generate_recommendation",
                "reason": "availability_candidates_ready_for_recommendation",
                "input": {
                    "options": options,
                    "criteria_snapshot": availability.get("criteria_snapshot") or {},
                },
                "auto_continue": True,
                "task_type": "recommendation_before_booking",
                "primary_intent": "recommend_technician",
                "secondary_intents": ["availability_query"],
            }
        ]

    return []


def _plan_has_recommendation_task(plan: dict | None) -> bool:
    return any(
        task.get("action") in {"generate_recommendation", "replace_recommendation"}
        for task in (plan or {}).get("tasks") or []
        if isinstance(task, dict)
    )
