"""Internal nodes for the availability specialist agent."""

from __future__ import annotations

from agents.specialists.availability.actions import availability_query_node
from agents.supervisor.state import (
    SupervisorState,
    merge_agent_action_update,
    state_for_agent_actions,
)
from agents.specialists.common import agent_result

from .state import normalize_availability_state, status_from_result


async def query_realtime_schedule_node(state: SupervisorState) -> SupervisorState:
    action_update = await availability_query_node(state_for_agent_actions(state))
    merged = merge_agent_action_update(state, action_update)
    availability = normalize_availability_state(merged.get("availability"))
    availability["status"] = status_from_result(availability)
    merged["availability"] = availability
    merged["last_agent_result"] = agent_result(
        "availability",
        availability["status"],
        "availability_result",
        merged.get("final_response"),
        {"availability": availability},
        {
            "target_agent": "booking" if availability.get("options") else None,
            "reason": "availability_options_ready" if availability.get("options") else "",
            "payload": {"options": availability.get("options") or []},
        },
    )
    return merged

