"""Preference recall boundary for the recommendation agent."""

from __future__ import annotations

from typing import Any, Dict

from tools.preference_tools import recall_preferences as recall_preferences_tool


def recall_preferences(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return currently available preference signals.

    The recommendation agent is intentionally conservative in 3.0: it exposes
    a memory boundary without proactively generating user-facing suggestions
    until a recommendation route is explicitly added.
    """
    existing = dict((state.get("recommendation") or {}).get("recalled_preferences") or {})
    if existing:
        return existing
    try:
        result = recall_preferences_tool.invoke({"user_id": state.get("user_id") or "default_user"})
        return (result.get("data") or {}).get("profile") or {}
    except Exception:
        return {}
