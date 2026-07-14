"""Recommendation specialist graph entrypoint."""

from __future__ import annotations

from langchain_core.messages import AIMessage

from agents.supervisor.state import SupervisorState

from .nodes import recommend_technician_node


async def recommendation_subgraph_node(state: SupervisorState) -> SupervisorState:
    action = (state.get("route_decision") or {}).get("action")
    result = await recommend_technician_node(
        state,
        replace_current=action == "replace_recommendation",
    )
    pending_responses = list(
        ((state.get("tool_results") or {}).get("query_first_intermediate_responses") or [])
    )
    if pending_responses and result.get("final_response"):
        final_response = "\n\n".join([*pending_responses, result["final_response"]])
        result["final_response"] = final_response
        result["messages"] = [AIMessage(content=final_response)]
        result["tool_results"] = {
            **(state.get("tool_results") or {}),
            **(result.get("tool_results") or {}),
            "query_first_intermediate_responses": [],
        }
    return result
