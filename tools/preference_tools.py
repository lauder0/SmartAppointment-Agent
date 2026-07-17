"""Preference recall tools."""

from __future__ import annotations

from langchain_core.tools import tool

from services.preference_recall_service import PreferenceRecallService
from .schemas import RecallPreferencesInput, tool_result


@tool(args_schema=RecallPreferencesInput)
def recall_preferences(user_id: str = "default_user") -> dict:
    """Recall durable user preference profile."""
    try:
        profile = PreferenceRecallService().recall(user_id or "default_user")
        return tool_result(
            True,
            data={"profile": profile},
            message="preferences recalled",
            tool_name="recall_preferences",
        )
    except Exception as e:
        return tool_result(
            False,
            data={"profile": {}},
            message="preference recall failed",
            error=str(e),
            tool_name="recall_preferences",
        )
