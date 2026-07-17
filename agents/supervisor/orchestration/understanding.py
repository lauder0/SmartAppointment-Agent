"""Main conversation router for state-aware flow dispatch.

The supervisor router is intentionally thin. Intent understanding, task
modeling, context resolution, and decision arbitration live in
``agents.understander``.
"""

from __future__ import annotations

from agents._shared.state import AgentState, ensure_state_defaults
from agents.understander.decision_arbiter import understand_user_turn


async def main_router_node(state: AgentState) -> AgentState:
    """Choose the next graph action from state and the latest user input."""
    state = ensure_state_defaults(state)
    return await understand_user_turn(state)
