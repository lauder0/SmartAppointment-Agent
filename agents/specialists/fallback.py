"""Fallback and clarification specialist adapter."""

from __future__ import annotations

from agents.specialists.fallback_actions import clarification_node, unsupported_node
from agents.supervisor.state import SupervisorState, merge_agent_action_update, state_for_agent_actions

from .common import agent_result


async def fallback_subgraph_node(state: SupervisorState) -> SupervisorState:
    action_state = state_for_agent_actions(state)
    action = (state.get("route_decision") or {}).get("action")
    update = await clarification_node(action_state) if action == "ask_clarification" else await unsupported_node(action_state)
    merged = merge_agent_action_update(state, update)
    merged["last_agent_result"] = agent_result(
        "fallback",
        "completed",
        action or "unsupported",
        merged.get("final_response"),
    )
    return merged

