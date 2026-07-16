"""Appointment write tools.

Write tools should be called only by guarded graph nodes after validation and
user confirmation.
"""

from __future__ import annotations

from datetime import timedelta

from langchain_core.tools import tool

from config.time_config import time_config
from services.appointment_service import AppointmentService
from .schemas import CreateAppointmentInput, tool_result


def _tool_result(*args, **kwargs) -> dict:
    return tool_result(*args, tool_name="create_appointment", **kwargs)


@tool(args_schema=CreateAppointmentInput)
def create_appointment(
    user_id: str,
    session_id: str,
    technician_id: int,
    service_name: str,
    start_time: str,
    duration_minutes: int,
    gender_preference: str | None = None,
    preference: str | None = None,
    idempotency_key: str | None = None,
) -> dict:
    """Create an appointment after the graph has validated all fields and user confirmation."""
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

        history = {
            "project": service_name,
            "duration": f"{duration_minutes}分钟",
            "gender": gender_preference,
            "preference": preference or "",
        }
        service = AppointmentService()
        save_result = service.save_appointment_result(
            technician_id=str(technician_id),
            start_time=start_dt,
            end_time=end_dt,
            appointment_history=history,
            session_id=session_id,
            user_id=user_id or "default_user",
            idempotency_key=idempotency_key,
        )
        success = bool(save_result.get("success"))
        created = save_result.get("created")
        reason = save_result.get("reason")
        if success and created is False:
            message = "预约已存在，已复用上次创建结果"
        elif success:
            message = "预约创建成功"
        else:
            message = "预约创建失败，可能存在时间冲突"
        return _tool_result(
            success,
            data={
                "user_id": user_id or "default_user",
                "technician_id": technician_id,
                "service_name": service_name,
                "start_time": time_config.format_datetime(start_dt),
                "end_time": time_config.format_datetime(end_dt),
                "duration_minutes": duration_minutes,
                "gender_preference": gender_preference,
                "preference": preference,
                "idempotency_key": idempotency_key,
                "created": created,
                "reason": reason,
                "appointment_id": save_result.get("appointment_id"),
                "appointment_no": save_result.get("appointment_no"),
            },
            message=message,
            error=None if success else reason,
        )
    except Exception as e:
        return _tool_result(False, message="预约创建失败", error=str(e))
