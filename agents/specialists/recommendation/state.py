"""Recommendation agent private state helpers."""

from __future__ import annotations

from typing import Any, Dict

from agents.supervisor.state import default_recommendation_state


def normalize_recommendation_state(raw: Dict[str, Any] | None) -> Dict[str, Any]:
    recommendation = dict(raw or default_recommendation_state())
    recommendation.setdefault("status", "idle")
    recommendation.setdefault("recalled_preferences", {})
    recommendation.setdefault("candidate_recommendations", [])
    recommendation.setdefault("selected_recommendation", None)
    recommendation.setdefault("alternative_recommendations", [])
    recommendation.setdefault("preference", None)
    recommendation.setdefault("recommendation_reason", None)
    recommendation.setdefault("confidence", None)
    recommendation.setdefault("excluded_technician_ids", [])
    recommendation.setdefault("trigger_reason", None)
    return recommendation
