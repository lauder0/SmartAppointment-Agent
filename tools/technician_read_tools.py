"""Read-only technician tools."""

from __future__ import annotations

from datetime import timedelta

from langchain_core.tools import tool

from config.time_config import time_config
from services.appointment_service import AppointmentService
from .schemas import CheckTechnicianAvailableInput, EmptyToolInput, GetTechnicianByNameInput, tool_result


@tool(args_schema=EmptyToolInput)
def get_all_technicians() -> dict:
    """Return all technicians as structured data."""
    try:
        technicians = AppointmentService().get_all_technicians()
        return tool_result(
            True,
            data={"technicians": technicians},
            message="technicians loaded",
            tool_name="get_all_technicians",
        )
    except Exception as e:
        return tool_result(
            False,
            data={"technicians": []},
            message="technician query failed",
            error=str(e),
            tool_name="get_all_technicians",
        )


@tool(args_schema=GetTechnicianByNameInput)
def get_technician_by_name(technician_name: str) -> dict:
    """Return one technician by name."""
    try:
        technician = AppointmentService().get_technician_by_name(technician_name)
        return tool_result(
            bool(technician),
            data={"technician": technician},
            message="technician loaded" if technician else "technician not found",
            error=None if technician else "technician_not_found",
            tool_name="get_technician_by_name",
        )
    except Exception as e:
        return tool_result(
            False,
            data={"technician": None},
            message="technician query failed",
            error=str(e),
            tool_name="get_technician_by_name",
        )


@tool(args_schema=CheckTechnicianAvailableInput)
def check_technician_available(technician_id: int, start_time: str, duration_minutes: int) -> dict:
    """Return whether a technician is available for the requested interval."""
    try:
        start_dt = time_config.parse_datetime(start_time)
        if start_dt is None:
            return tool_result(
                False,
                message="invalid start time",
                error="invalid_start_time",
                tool_name="check_technician_available",
            )
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        available = AppointmentService().is_technician_available(technician_id, start_dt, end_dt)
        return tool_result(
            True,
            data={
                "technician_id": technician_id,
                "start_time": time_config.format_datetime(start_dt),
                "end_time": time_config.format_datetime(end_dt),
                "available": bool(available),
            },
            message="technician availability checked",
            tool_name="check_technician_available",
        )
    except Exception as e:
        return tool_result(
            False,
            message="technician availability check failed",
            error=str(e),
            tool_name="check_technician_available",
        )
