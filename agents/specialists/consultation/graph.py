"""Consultation specialist graph entrypoint."""

from __future__ import annotations

from agents.supervisor.state import SupervisorState

from .nodes import answer_knowledge_node


async def consultation_subgraph_node(state: SupervisorState) -> SupervisorState:
    return await answer_knowledge_node(state)
