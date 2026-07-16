"""Supervisor response outlet that delegates final wording to Response Writer."""

from __future__ import annotations

from typing import Any, List

from langchain_core.messages import AIMessage

from agents.response_writer.schema import build_writer_input
from agents.response_writer.writer import writer
from agents.supervisor.state import SupervisorState, ensure_supervisor_defaults


async def supervisor_response_node(state: SupervisorState) -> SupervisorState:
    """Publish one user-facing response from structured AgentResults."""
    state = ensure_supervisor_defaults(state)
    turn_results = list(state.get("turn_results") or [])
    last_result = state.get("last_agent_result") or {}
    writer_output = await writer.write(build_writer_input(state))
    final_response = writer_output.get("final_response") or state.get("final_response") or last_result.get("message")

    update: SupervisorState = {
        "turn_results": turn_results,
        "final_response": final_response,
        "turn_trace": {
            **(state.get("turn_trace") or {}),
            "writer_input_summary": writer_output.get("input_summary"),
            "writer_strategy": writer_output.get("writer_strategy"),
        },
        "tool_results": {
            **(state.get("tool_results") or {}),
            "supervisor_response": {
                "published": bool(final_response),
                "result_count": len(turn_results),
                "last_agent": last_result.get("agent_name"),
                "last_result_type": last_result.get("result_type"),
                "response_type": last_result.get("response_type"),
                "writer": {
                    "selected_label": writer_output.get("selected_label"),
                    "rendered_result_count": writer_output.get("rendered_result_count"),
                    "skipped_result_count": writer_output.get("skipped_result_count"),
                    "strategy": writer_output.get("writer_strategy"),
                },
            },
        },
    }
    if final_response and not _last_ai_message_matches(state.get("messages") or [], final_response):
        update["messages"] = [AIMessage(content=final_response)]
    return update


def _last_ai_message_matches(messages: List[Any], content: str) -> bool:
    for message in reversed(messages):
        if getattr(message, "type", None) == "ai":
            return str(getattr(message, "content", "")) == content
    return False
