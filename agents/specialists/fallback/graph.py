"""Fallback and clarification specialist adapter."""

from __future__ import annotations

from agents.specialists.fallback.actions import clarification_node, unsupported_node
from agents.supervisor.state import SupervisorState, merge_agent_action_update, state_for_agent_actions

from agents.specialists.result_contract import agent_result, attach_agent_result


async def fallback_subgraph_node(state: SupervisorState) -> SupervisorState:
    action_state = state_for_agent_actions(state)
    action = (state.get("route_decision") or {}).get("action")
    update = await clarification_node(action_state) if action == "ask_clarification" else await unsupported_node(action_state)
    merged = merge_agent_action_update(state, update)
    result = agent_result(
        "fallback",
        "completed",
        action or "unsupported",
        merged.get("final_response"),
    )
    attach_agent_result(merged, state, result)
    return merged

