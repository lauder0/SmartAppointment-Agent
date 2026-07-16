"""Realtime availability tools."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from langchain_core.tools import tool

from config.time_config import time_config
from services.availability_service import AvailabilityService
from .schemas import QueryAvailabilityInput, tool_result


def _tool_result(*args, **kwargs) -> dict:
    return tool_result(*args, tool_name="query_availability", **kwargs)


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return time_config.format_datetime(value)
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def _deserialize_criteria(criteria: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Convert serialized datetime strings back to datetime objects for AvailabilityService."""
    if not criteria:
        return criteria

    restored = dict(criteria)
    for field in ("date", "start_time"):
        value = restored.get(field)
        if isinstance(value, str):
            restored[field] = time_config.parse_datetime(value)
    return restored


@tool(args_schema=QueryAvailabilityInput)
def query_availability(text: str, base_criteria: Dict[str, Any] | None = None) -> dict:
    """Query realtime technician availability, schedules, free slots, and bookable time windows."""
    try:
        service = AvailabilityService()
        base_criteria = _deserialize_criteria(base_criteria)
        current_criteria = service.parse_query_criteria(text)
        merged_criteria = (
            service.merge_query_criteria(base_criteria, current_criteria)
            if base_criteria
            else current_criteria
        )
        answer = service.answer_availability_query(text, base_criteria)
        available_names = service.extract_available_technician_names(answer)
        return _tool_result(
            True,
            data={
                "answer": answer,
                "criteria": _serialize_value(merged_criteria),
                "available_technician_names": available_names,
            },
            message="实时排班查询成功",
        )
    except Exception as e:
        return _tool_result(False, data={"text": text}, message="实时排班查询失败", error=str(e))
