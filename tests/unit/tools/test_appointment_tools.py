from __future__ import annotations

from datetime import timedelta

from config.time_config import time_config
from db.db_router import DatabaseRouter
from services.appointment_service import AppointmentService
from tools import appointment_tools


def test_create_appointment_tool_rejects_invalid_time():
    result = appointment_tools.create_appointment.invoke(
        {
            "user_id": "u1",
            "session_id": "s1",
            "technician_id": 1,
            "service_name": "肩颈推拿",
            "start_time": "not-a-time",
            "duration_minutes": 60,
        }
    )

    assert result["success"] is False
    assert result["error"] == "invalid_start_time"


def test_create_appointment_tool_is_idempotent(tmp_db_url, monkeypatch):
    router = DatabaseRouter(tmp_db_url)
    technician_id = router.technicians.add_technician("李娜", gender="女", strength="肩颈放松")
    router.appointments.add_service("肩颈推拿", default_duration_minutes=60, price_cents=8000)
    router.close()

    monkeypatch.setattr(
        appointment_tools,
        "AppointmentService",
        lambda: AppointmentService(tmp_db_url),
    )
    start = time_config.format_datetime(time_config.today().replace(hour=15, minute=0) + timedelta(days=1))
    payload = {
        "user_id": "u1",
        "session_id": "s1",
        "technician_id": technician_id,
        "service_name": "肩颈推拿",
        "start_time": start,
        "duration_minutes": 60,
        "gender_preference": "女",
        "idempotency_key": "tool-idempotent-key",
    }

    first = appointment_tools.create_appointment.invoke(payload)
    second = appointment_tools.create_appointment.invoke(payload)

    verify_router = DatabaseRouter(tmp_db_url)
    appointments = verify_router.appointments.get_user_appointments("u1")
    schedules = verify_router.technicians.get_technician_schedules(
        technician_id,
        time_config.parse_datetime(start),
    )
    verify_router.close()

    assert first["success"] is True
    assert second["success"] is True
    assert len(appointments) == 1
    assert len(schedules) == 1


def test_create_appointment_tool_blocks_overlap(tmp_db_url, monkeypatch):
    router = DatabaseRouter(tmp_db_url)
    technician_id = router.technicians.add_technician("李娜", gender="女", strength="肩颈放松")
    router.appointments.add_service("肩颈推拿", default_duration_minutes=60, price_cents=8000)
    router.close()

    monkeypatch.setattr(
        appointment_tools,
        "AppointmentService",
        lambda: AppointmentService(tmp_db_url),
    )
    start_dt = time_config.today().replace(hour=15, minute=0) + timedelta(days=1)
    first_payload = {
        "user_id": "u1",
        "session_id": "s1",
        "technician_id": technician_id,
        "service_name": "肩颈推拿",
        "start_time": time_config.format_datetime(start_dt),
        "duration_minutes": 60,
        "idempotency_key": "tool-first-key",
    }
    overlap_payload = {
        **first_payload,
        "start_time": time_config.format_datetime(start_dt + timedelta(minutes=30)),
        "idempotency_key": "tool-overlap-key",
    }

    first = appointment_tools.create_appointment.invoke(first_payload)
    second = appointment_tools.create_appointment.invoke(overlap_payload)

    assert first["success"] is True
    assert second["success"] is False
