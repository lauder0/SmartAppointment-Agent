"""Recommendation specialist graph entrypoint."""

from __future__ import annotations

from agents.supervisor.state import SupervisorState

from .nodes import recommend_technician_node


async def recommendation_subgraph_node(state: SupervisorState) -> SupervisorState:
    action = (state.get("route_decision") or {}).get("action")
    return await recommend_technician_node(
        state,
        replace_current=action == "replace_recommendation",
    )
