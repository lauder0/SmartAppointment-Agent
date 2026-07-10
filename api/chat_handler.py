"""Unified chat entrypoint backed by the LangGraph workflow."""

from __future__ import annotations

from api.graph_chat_handler import ProcessUserInput_graph_stream, reset_graph_session


async def reset_session(session_id: str) -> None:
    await reset_graph_session(session_id)


async def ProcessUserInput_stream(user_input, session_id=None, state=None, context=None):
    """Compatibility wrapper used by Web UI and evaluation scripts."""
    user_id = _extract_user_id(state, context)
    async for token in ProcessUserInput_graph_stream(
        user_input,
        session_id=session_id,
        user_id=user_id,
    ):
        yield token


def _extract_user_id(state=None, context=None) -> str:
    if isinstance(context, dict) and context.get("user_id"):
        return context["user_id"]
    if isinstance(state, dict) and state.get("user_id"):
        return state["user_id"]
    return "default_user"
