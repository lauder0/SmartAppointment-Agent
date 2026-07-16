"""Supervisor-only nodes for 3.0 orchestration."""

from __future__ import annotations

from agents.shared.context_manager import (
    apply_state_invalidations,
    changed_dependency_fields,
    invalidations_for_focus_changes,
)
from agents.supervisor.orchestration.completion import complete_current_task_from_result, start_next_task
from agents.supervisor.orchestration.controller import (
    active_agent_for_plan,
    active_task_for_plan,
    append_suggested_tasks,
    route_decision_from_current_task,
    task_trace,
)
from agents.supervisor.planning.planner import build_execution_plan_with_optional_llm
from agents.supervisor.planning.plan_reviewer import review_plan_after_result_with_optional_llm
from agents.supervisor.router_actions import main_router_node
from agents.supervisor.state import (
    SupervisorState,
    ensure_supervisor_defaults,
    state_for_agent_actions,
)


async def supervisor_entry_node(state: SupervisorState) -> SupervisorState:
    state = ensure_supervisor_defaults(state)
    return {
        "active_agent": state.get("active_agent"),
        "active_task": state.get("active_task"),
        "task_stack": state.get("task_stack", []),
        "shared_focus_context": state.get("shared_focus_context"),
        "consultation": state.get("consultation"),
        "availability": state.get("availability"),
        "booking": state.get("booking"),
        "recommendation": state.get("recommendation"),
        "task_frame": state.get("task_frame"),
        "execution_plan": state.get("execution_plan"),
        "route_decision": None,
        "last_agent_result": state.get("last_agent_result"),
        "turn_results": [],
        "turn_trace": None,
        "trace_history": state.get("trace_history", []),
        "last_completed_booking": state.get("last_completed_booking"),
        "tool_results": state.get("tool_results", {}),
        "final_response": None,
        "error": None,
    }


async def supervisor_router_node(state: SupervisorState) -> SupervisorState:
    state = ensure_supervisor_defaults(state)
    router_update = await main_router_node(state_for_agent_actions(state))
    decision = router_update.get("route_decision") or {"action": "unsupported", "reason": "no_decision"}
    next_focus = router_update.get("focus_context", state.get("shared_focus_context"))
    changed_fields = changed_dependency_fields(state.get("shared_focus_context"), next_focus)
    invalidates = sorted(set((decision.get("invalidates") or []) + invalidations_for_focus_changes(changed_fields)))
    invalidation_update = apply_state_invalidations(state, invalidates)
    planning_state = {
        **state,
        **invalidation_update,
        "shared_focus_context": next_focus,
    }
    plan = await build_execution_plan_with_optional_llm(
        task_frame=router_update.get("task_frame", state.get("task_frame")),
        route_decision=decision,
        state=planning_state,
    )
    planned_decision = route_decision_from_current_task(plan, decision)
    return {
        **invalidation_update,
        "route_decision": planned_decision,
        "active_agent": active_agent_for_plan(plan, planned_decision.get("action")),
        "active_task": active_task_for_plan(plan, planned_decision.get("action")),
        "shared_focus_context": next_focus,
        "task_frame": router_update.get("task_frame", state.get("task_frame")),
        "execution_plan": plan,
        "turn_trace": {
            "understanding_source": decision.get("source"),
            "invalidated_state": invalidates,
            **task_trace(plan),
        },
        "tool_results": {
            **(state.get("tool_results") or {}),
            **(router_update.get("tool_results") or {}),
            "supervisor_router": planned_decision,
            "execution_plan": task_trace(plan),
        },
    }


async def supervisor_continue_node(state: SupervisorState) -> SupervisorState:
    """Advance the execution plan and expose the next task as a route decision."""
    state = ensure_supervisor_defaults(state)
    current_decision = state.get("route_decision") or {}
    plan = complete_current_task_from_result(state)
    plan = append_suggested_tasks(plan, state.get("last_agent_result"))
    plan = start_next_task(plan)
    review = await review_plan_after_result_with_optional_llm(plan, state.get("last_agent_result"))
    next_decision = route_decision_from_current_task(plan, current_decision)
    if not plan.get("current_task_id"):
        return {
            "execution_plan": plan,
            "route_decision": current_decision,
            "active_agent": active_agent_for_plan(plan, current_decision.get("action")),
            "active_task": active_task_for_plan(plan, current_decision.get("action")),
            "turn_trace": {
                **(state.get("turn_trace") or {}),
                **task_trace(plan),
                "plan_review": review,
            },
            "tool_results": {
                **(state.get("tool_results") or {}),
                "supervisor_continue": {"decision": "response", "reason": review.get("reason")},
                "execution_plan": task_trace(plan),
                "plan_review": review,
            },
        }

    return {
        "execution_plan": plan,
        "route_decision": next_decision,
        "active_agent": active_agent_for_plan(plan, next_decision.get("action")),
        "active_task": active_task_for_plan(plan, next_decision.get("action")),
        "final_response": None,
        "turn_trace": {
            **(state.get("turn_trace") or {}),
            **task_trace(plan),
            "plan_review": review,
        },
        "tool_results": {
            **(state.get("tool_results") or {}),
            "supervisor_continue": next_decision,
            "execution_plan": task_trace(plan),
            "plan_review": review,
        },
    }

