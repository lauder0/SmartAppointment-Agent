from datetime import timedelta

from config.time_config import time_config
from services.availability_service import AvailabilityService


class AlwaysAvailableAppointmentService:
    def is_technician_available(self, _technician_id, _start_time, _end_time):
        return True


def test_afternoon_query_creates_a_time_window_without_exact_start():
    service = AvailabilityService(AlwaysAvailableAppointmentService())

    criteria = service.parse_query_criteria("明天下午来")

    assert criteria["start_time"] is None
    assert criteria["time_period"] == "afternoon"
    assert criteria["has_explicit_period"] is True


def test_afternoon_slots_stay_inside_afternoon_window():
    service = AvailabilityService(AlwaysAvailableAppointmentService())
    target_date = time_config.today() + timedelta(days=1)
    criteria = {"date": target_date, "time_period": "afternoon"}
    window_start, window_end = service._availability_window(criteria)

    slots = service._find_available_slots(
        technicians=[{"id": 1, "name": "王强"}],
        target_date=target_date,
        duration_minutes=40,
        max_slots=20,
        window_start=window_start,
        window_end=window_end,
    )

    assert slots
    assert all(slot["start"] >= "13:00" for slot in slots)
    assert all(slot["end"] <= "18:00" for slot in slots)
