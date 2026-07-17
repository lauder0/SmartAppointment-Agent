"""Availability specialist graph entrypoint."""

from __future__ import annotations

from agents.supervisor.state import SupervisorState

from .nodes import query_realtime_schedule_node


async def availability_subgraph_node(state: SupervisorState) -> SupervisorState:
    return await query_realtime_schedule_node(state)
