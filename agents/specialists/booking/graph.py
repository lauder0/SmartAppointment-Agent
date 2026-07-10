"""Booking specialist graph entrypoint."""

from __future__ import annotations

from agents.supervisor.state import (
    SupervisorState,
    merge_agent_action_update,
    state_for_agent_actions,
)
from agents.specialists.common import agent_result

from .flow import run_booking_flow
from .state import booking_result_type, normalize_booking_state


async def booking_subgraph_node(state: SupervisorState) -> SupervisorState:
    action = (state.get("route_decision") or {}).get("action")
    action_state = state_for_agent_actions(state)
    aggregate = await run_booking_flow(action, action_state)

    merged = merge_agent_action_update(state, aggregate)
    booking = normalize_booking_state(merged.get("booking") or state.get("booking"))
    result_type = booking_result_type(booking, merged)
    merged["booking"] = booking
    merged["last_agent_result"] = agent_result(
        "booking",
        booking.get("status", "unknown"),
        result_type,
        merged.get("final_response"),
        {"booking": booking},
    )
    return merged
