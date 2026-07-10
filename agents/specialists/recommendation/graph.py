"""Recommendation specialist graph entrypoint."""

from __future__ import annotations

from agents.supervisor.state import SupervisorState

from .nodes import prepare_recommendation_node


async def recommendation_subgraph_node(state: SupervisorState) -> SupervisorState:
    return await prepare_recommendation_node(state)
