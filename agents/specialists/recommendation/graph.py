"""Recommendation specialist graph entrypoint."""

from __future__ import annotations

from agents.specialists.result_contract import attach_agent_result
from agents.supervisor.state import SupervisorState

from .nodes import recommend_service_node, recommend_technician_node


async def recommendation_subgraph_node(state: SupervisorState) -> SupervisorState:
    action = (state.get("route_decision") or {}).get("action")
    if action == "recommend_service":
        result = await recommend_service_node(state)
    else:
        result = await recommend_technician_node(
            state,
            replace_current=action == "replace_recommendation",
        )
    if result.get("last_agent_result"):
        attach_agent_result(result, state, result["last_agent_result"])
    return result
