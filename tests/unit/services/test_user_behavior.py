from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta

from services.preference_recall_service import PreferenceRecallService
from services.recommendation_service import RecommendationService
from services.user_behavior_service import UserBehaviorService
from services.appointment_service import AppointmentService


def _db_url(tmp_path: Path) -> str:
    return "sqlite:///" + str(tmp_path / "user_behavior_test.db").replace("\\", "/")


def test_recording_appointment_updates_preferences(tmp_path):
    db_url = _db_url(tmp_path)
    service = UserBehaviorService(db_url)
    technician_id = service.db_router.technicians.add_technician(
        name="Alice",
        gender="female",
        strength="strong pressure",
    )

    ok = service.record_behavior(
        user_id="u1",
        action_type="appointment",
        action_data={
            "service_name": "shoulder massage",
            "start_time": "2026-06-08 19:00",
            "duration_minutes": 60,
            "gender_preference": "female",
            "preference": "strong pressure",
        },
        technician_id=technician_id,
        session_id="s1",
    )

    preferences = service.get_user_preferences("u1")
    by_type = {item["preference_type"]: item["preference_value"] for item in preferences}

    assert ok is True
    assert by_type["technician"] == str(technician_id)
    assert by_type["service"] == "shoulder massage"
    assert by_type["duration"] == "60"
    assert by_type["gender"] == "female"
    assert by_type["style"] == "strong pressure"
    assert by_type["time_period"] == "evening"

    service.db_router.close()


def test_preference_recall_returns_compact_profile(tmp_path):
    db_url = _db_url(tmp_path)
    appointment_service = AppointmentService(db_url)
    technician_id = appointment_service.add_technician("Alice", gender="female", strength="relaxing")
    start_time = datetime(2026, 6, 8, 10, 0)
    appointment_service.save_appointment(
        technician_id=str(technician_id),
        start_time=start_time,
        end_time=start_time + timedelta(minutes=45),
        appointment_history={"project": "foot massage", "duration": "45 minutes", "gender": "female"},
        session_id="s1",
        user_id="u1",
    )

    recall = PreferenceRecallService(db_url)
    profile = recall.recall("u1")

    assert profile["preferred_service"] == "foot massage"
    assert profile["preferred_duration_minutes"] == 45
    assert profile["preferred_technician_id"] == technician_id
    assert profile["preferred_time_period"] == "morning"

    appointment_service.db_router.close()
    recall.appointment_preference_service.appointment_service.db_router.close()


def test_recommendation_preview_is_safe_for_new_user():
    result = RecommendationService().preview_return_reminder("brand_new_user")

    assert result["message"]
    assert isinstance(result["technician_available_times"], list)


def test_recommendation_generation_uses_appointment_history(tmp_path):
    db_url = _db_url(tmp_path)
    appointment_service = AppointmentService(db_url)
    technician_id = appointment_service.add_technician("Alice", gender="female", strength="relaxing")
    first = datetime.utcnow() - timedelta(days=40)
    second = datetime.utcnow() - timedelta(days=20)

    for index, start_time in enumerate([first, second], start=1):
        appointment_service.save_appointment(
            technician_id=str(technician_id),
            start_time=start_time.replace(hour=19, minute=0, second=0, microsecond=0),
            end_time=start_time.replace(hour=20, minute=0, second=0, microsecond=0),
            appointment_history={"project": "foot massage", "duration": "60 minutes", "gender": "female"},
            session_id=f"s{index}",
            user_id="u1",
        )

    service = RecommendationService(db_url)
    generated = service.generate_recommendations_job()

    assert generated
    assert generated[0]["user_id"] == "u1"
    assert generated[0]["recommendation_type"] == "return_reminder"
    assert generated[0]["status"] == "generated"
    assert generated[0]["is_sent"] is False

    appointment_service.db_router.close()
    service.db_router.close()
    service.appointment_service.db_router.close()
    service.preference_service.appointment_service.db_router.close()
