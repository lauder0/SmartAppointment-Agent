"""Internal nodes for the consultation specialist agent."""

from __future__ import annotations

from typing import Any, Dict

from agents.specialists.consultation.actions import knowledge_consult_node
from agents.supervisor.state import (
    SupervisorState,
    merge_agent_action_update,
    state_for_agent_actions,
)
from agents.specialists.common import agent_result

from .state import completed_consultation_state, consultation_state_from_supervisor


async def answer_knowledge_node(state: SupervisorState) -> SupervisorState:
    action_update = await knowledge_consult_node(state_for_agent_actions(state))
    merged = merge_agent_action_update(state, action_update)
    docs = ((merged.get("tool_results") or {}).get("search_knowledge") or {}).get("data", {}).get("documents", [])
    consultation = completed_consultation_state(
        consultation_state_from_supervisor(state),
        merged.get("final_response"),
        docs,
    )
    merged["consultation"] = consultation
    merged["last_agent_result"] = agent_result(
        "consultation",
        "completed",
        "knowledge_answer",
        merged.get("final_response"),
        {"consultation": consultation},
    )
    return merged

