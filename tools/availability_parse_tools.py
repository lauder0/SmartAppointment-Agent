"""Read-only availability parsing tools."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from langchain_core.tools import tool

from config.time_config import time_config
from services.availability_service import AvailabilityService
from .schemas import ParseAvailabilitySlotsInput, tool_result


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return time_config.format_datetime(value)
    if isinstance(value, dict):
        return {key: _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


@tool(args_schema=ParseAvailabilitySlotsInput)
def parse_availability_slots(text: str) -> dict:
    """Parse availability and booking slots from user text."""
    try:
        service = AvailabilityService()
        criteria = service.parse_query_criteria(text)
        return tool_result(
            True,
            data={
                "criteria": _serialize_value(criteria),
                "service_type": service.parse_service_type(text),
                "preference": service.parse_preference(text),
            },
            message="availability slots parsed",
            tool_name="parse_availability_slots",
        )
    except Exception as e:
        return tool_result(
            False,
            data={"text": text},
            message="availability slot parse failed",
            error=str(e),
            tool_name="parse_availability_slots",
        )
