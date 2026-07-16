"""Technician matching tools."""

from __future__ import annotations

from datetime import timedelta

from langchain_core.tools import tool

from config.time_config import time_config
from services.preference_recall_service import PreferenceRecallService
from .schemas import MatchTechnicianInput, tool_result
from .technician_finder import TechnicianFinder


def _tool_result(*args, **kwargs) -> dict:
    return tool_result(*args, tool_name="match_technician", **kwargs)


@tool(args_schema=MatchTechnicianInput)
def match_technician(
    start_time: str,
    duration_minutes: int,
    gender_preference: str | None = None,
    preference: str | None = None,
    technician_name: str | None = None,
    excluded_technician_ids: list[int] | None = None,
    user_id: str | None = "default_user",
) -> dict:
    """Match an available technician by time, gender, named technician, and semantic preference."""
    try:
        start_dt = time_config.parse_datetime(start_time)
        if start_dt is None:
            return _tool_result(False, message="预约开始时间格式无效", error="invalid_start_time")

        end_dt = start_dt + timedelta(minutes=duration_minutes)
        valid_time, invalid_reason = time_config.validate_booking_time(start_dt, end_dt)
        if not valid_time:
            return _tool_result(
                False,
                data={
                    "start_time": time_config.format_datetime(start_dt),
                    "end_time": time_config.format_datetime(end_dt),
                    "booking_window_days": time_config.get_booking_window_days(),
                    "business_hours": time_config.get_business_hours(),
                },
                message="Requested time is outside the bookable window.",
                error=invalid_reason,
            )

        recalled = PreferenceRecallService().recall(user_id or "default_user")
        if not technician_name:
            technician_name = recalled.get("preferred_technician_name")
        if not gender_preference:
            gender_preference = recalled.get("preferred_gender")
        if not preference:
            preference = recalled.get("preferred_style")

        history = {
            "start_time": time_config.format_datetime(start_dt),
            "duration": f"{duration_minutes}分钟",
            "gender": gender_preference or "未知",
            "preference": preference or "无",
            "technician_name": technician_name or "未知",
            "excluded_technician_ids": excluded_technician_ids or [],
        }
        finder = TechnicianFinder()
        thought_messages: list[str] = []
        tech = finder.find_technician_with_thought(history, thought_messages.append)

        if not tech:
            return _tool_result(
                False,
                data={
                    "start_time": time_config.format_datetime(start_dt),
                    "end_time": time_config.format_datetime(end_dt),
                    "thoughts": thought_messages,
                },
                message="没有找到可用技师",
            )

        if tech.get("requires_confirmation"):
            return _tool_result(
                True,
                data={
                    "match_type": "recommendation",
                    "original_technician": tech.get("original_technician"),
                    "recommended_technician": tech.get("recommended_technician"),
                    "requires_confirmation": True,
                    "thoughts": thought_messages,
                },
                message="指定技师不可用，已找到相似可用技师",
            )

        return _tool_result(
            True,
            data={
                "match_type": "direct",
                "technician": tech,
                "requires_confirmation": False,
                "thoughts": thought_messages,
            },
            message="已找到可用技师",
        )
    except Exception as e:
        return _tool_result(False, message="技师匹配失败", error=str(e))
