"""Recommendation tools wrapping recommendation services."""

from __future__ import annotations

from langchain_core.tools import tool

from services.service_recommendation_service import ServiceRecommendationService
from services.technician_recommendation_service import (
    TechnicianRecommendationService,
    parse_recommendation_preference,
)
from .schemas import RecommendServiceInput, RankTechniciansInput, tool_result


@tool(args_schema=RecommendServiceInput)
def recommend_service_item(user_text: str, focus_context: dict | None = None) -> dict:
    """Recommend a service item from symptoms, needs, or shared context."""
    try:
        result = ServiceRecommendationService().recommend(user_text, focus_context or {})
        return tool_result(
            bool(result.get("success")),
            data=result,
            message="service recommendation completed",
            tool_name="recommend_service_item",
        )
    except Exception as e:
        return tool_result(False, data={}, message="service recommendation failed", error=str(e), tool_name="recommend_service_item")


@tool(args_schema=RankTechniciansInput)
def rank_technicians(
    candidate_options: list[dict] | None = None,
    preference: dict | None = None,
    service_type: str | None = None,
    recalled_preferences: dict | None = None,
    excluded_technician_ids: list[int] | None = None,
) -> dict:
    """Rank verified available technician candidates."""
    try:
        ranked = TechnicianRecommendationService().rank(
            candidate_options=candidate_options or [],
            preference=preference or {},
            service_type=service_type,
            recalled_preferences=recalled_preferences or {},
            excluded_technician_ids=excluded_technician_ids or [],
        )
        return tool_result(
            True,
            data={"ranked": ranked},
            message="technicians ranked",
            tool_name="rank_technicians",
        )
    except Exception as e:
        return tool_result(False, data={"ranked": []}, message="technician ranking failed", error=str(e), tool_name="rank_technicians")


def parse_preference(text: str, fallback: str | None = None) -> dict:
    """Small pure helper for existing non-tool call sites."""
    return parse_recommendation_preference(text, fallback=fallback)
