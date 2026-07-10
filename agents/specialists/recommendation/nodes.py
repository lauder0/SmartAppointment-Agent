"""Internal nodes for the recommendation specialist agent."""

from __future__ import annotations

from agents.supervisor.state import SupervisorState, ensure_supervisor_defaults
from agents.specialists.common import agent_result

from .memory import recall_preferences
from .state import normalize_recommendation_state


async def prepare_recommendation_node(state: SupervisorState) -> SupervisorState:
    state = ensure_supervisor_defaults(state)
    recommendation = normalize_recommendation_state(state.get("recommendation"))
    recommendation.update(
        {
            "status": "idle",
            "recalled_preferences": recall_preferences(state),
            "trigger_reason": "not_requested",
        }
    )
    return {
        "recommendation": recommendation,
        "last_agent_result": agent_result(
            "recommendation",
            "idle",
            "recommendation_not_requested",
            None,
            {"recommendation": recommendation},
        ),
    }
