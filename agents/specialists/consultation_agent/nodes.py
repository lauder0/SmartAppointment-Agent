"""Internal nodes for the consultation specialist agent."""

from __future__ import annotations

from agents.specialists.consultation_agent.actions import knowledge_consult_node
from agents.supervisor.state import (
    SupervisorState,
    merge_agent_action_update,
    state_for_agent_actions,
)
from agents.specialists.result_contract import agent_result, attach_agent_result

from .state import completed_consultation_state, consultation_state_from_supervisor


async def answer_knowledge_node(state: SupervisorState) -> SupervisorState:
    action_update = await knowledge_consult_node(state_for_agent_actions(state))
    merged = merge_agent_action_update(state, action_update)
    docs = ((merged.get("tool_results") or {}).get("search_knowledge") or {}).get("data", {}).get("documents", [])
    response_type = action_update.get("response_type") or "knowledge_answer"
    response_facts = action_update.get("response_facts") or {}
    answer = response_facts.get("answer")
    consultation = completed_consultation_state(
        consultation_state_from_supervisor(state),
        answer,
        docs,
        "service_catalog" if response_type == "service_catalog" else "knowledge",
    )
    merged["consultation"] = consultation
    result_type = "service_catalog" if response_type == "service_catalog" else "knowledge_answer"
    result = agent_result(
        "consultation",
        "completed",
        result_type,
        None,
        {"consultation": consultation},
        response_type=response_type,
        facts=response_facts,
    )
    attach_agent_result(merged, state, result)
    return merged

