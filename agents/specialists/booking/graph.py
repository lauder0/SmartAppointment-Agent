"""Booking specialist graph entrypoint."""

from __future__ import annotations

from agents.supervisor.state import (
    SupervisorState,
    merge_agent_action_update,
    state_for_agent_actions,
)
from agents.specialists.result_contract import attach_agent_result

from .flow import run_booking_flow
from .result_contract import build_booking_result_contract, booking_contract_to_specialist_result
from .state import normalize_booking_state


async def booking_subgraph_node(state: SupervisorState) -> SupervisorState:
    action = (state.get("route_decision") or {}).get("action")
    action_state = state_for_agent_actions(state)
    aggregate = await run_booking_flow(action, action_state)

    merged = merge_agent_action_update(state, aggregate)
    booking = normalize_booking_state(merged.get("booking") or state.get("booking"))
    merged["booking"] = booking
    contract = build_booking_result_contract(
        action=action,
        booking=booking,
        aggregate=aggregate,
        merged_state=merged,
    )
    result = booking_contract_to_specialist_result(contract)
    attach_agent_result(merged, state, result)
    return merged

