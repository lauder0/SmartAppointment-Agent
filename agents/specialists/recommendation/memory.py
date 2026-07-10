"""Preference recall boundary for the recommendation agent."""

from __future__ import annotations

from typing import Any, Dict


def recall_preferences(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return currently available preference signals.

    The recommendation agent is intentionally conservative in 3.0: it exposes
    a memory boundary without proactively generating user-facing suggestions
    until a recommendation route is explicitly added.
    """
    return dict((state.get("recommendation") or {}).get("recalled_preferences") or {})
