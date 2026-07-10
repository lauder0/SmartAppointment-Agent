from __future__ import annotations

from datetime import timedelta

from config.time_config import time_config
from tools import technician_tools
from tools.technician_finder import TechnicianFinder


def test_match_technician_tool_rejects_invalid_time():
    result = technician_tools.match_technician.invoke(
        {
            "start_time": "bad-time",
            "duration_minutes": 60,
        }
    )

    assert result["success"] is False
    assert result["error"] == "invalid_start_time"


def test_match_technician_tool_returns_direct_match(monkeypatch):
    class FakeRecall:
        def recall(self, user_id):
            return {}

    class FakeFinder:
        def find_technician_with_thought(self, history, on_thought):
            on_thought("checked availability")
            return {"id": 3, "name": "李娜", "gender": "女"}

    monkeypatch.setattr(technician_tools, "PreferenceRecallService", lambda: FakeRecall())
    monkeypatch.setattr(technician_tools, "TechnicianFinder", lambda: FakeFinder())
    start = time_config.format_datetime(time_config.today().replace(hour=15, minute=0) + timedelta(days=1))

    result = technician_tools.match_technician.invoke(
        {
            "start_time": start,
            "duration_minutes": 60,
            "gender_preference": "女",
        }
    )

    assert result["success"] is True
    assert result["data"]["match_type"] == "direct"
    assert result["data"]["technician"]["name"] == "李娜"


def test_match_technician_tool_returns_recommendation(monkeypatch):
    class FakeRecall:
        def recall(self, user_id):
            return {}

    class FakeFinder:
        def find_technician_with_thought(self, history, on_thought):
            return {
                "requires_confirmation": True,
                "original_technician": {"id": 1, "name": "张伟"},
                "recommended_technician": {"id": 2, "name": "王强"},
            }

    monkeypatch.setattr(technician_tools, "PreferenceRecallService", lambda: FakeRecall())
    monkeypatch.setattr(technician_tools, "TechnicianFinder", lambda: FakeFinder())
    start = time_config.format_datetime(time_config.today().replace(hour=15, minute=0) + timedelta(days=1))

    result = technician_tools.match_technician.invoke(
        {
            "start_time": start,
            "duration_minutes": 60,
            "technician_name": "张伟",
        }
    )

    assert result["success"] is True
    assert result["data"]["match_type"] == "recommendation"
    assert result["data"]["recommended_technician"]["name"] == "王强"


def test_match_technician_tool_passes_excluded_ids_to_finder(monkeypatch):
    captured = {}

    class FakeRecall:
        def recall(self, user_id):
            return {}

    class FakeFinder:
        def find_technician_with_thought(self, history, on_thought):
            captured.update(history)
            return {"id": 3, "name": "李娜", "gender": "女"}

    monkeypatch.setattr(technician_tools, "PreferenceRecallService", lambda: FakeRecall())
    monkeypatch.setattr(technician_tools, "TechnicianFinder", lambda: FakeFinder())
    start = time_config.format_datetime(time_config.today().replace(hour=15, minute=0) + timedelta(days=1))

    result = technician_tools.match_technician.invoke(
        {
            "start_time": start,
            "duration_minutes": 60,
            "gender_preference": "女",
            "excluded_technician_ids": [4],
        }
    )

    assert result["success"] is True
    assert captured["excluded_technician_ids"] == [4]


def test_technician_finder_skips_excluded_available_technician(monkeypatch):
    class FakeAppointmentService:
        def get_all_technicians(self):
            return [
                {"id": 4, "name": "赵敏", "gender": "女", "strength": "全身放松"},
                {"id": 3, "name": "李娜", "gender": "女", "strength": "肩颈放松"},
            ]

        def is_technician_available(self, technician_id, start_time, end_time):
            return True

    monkeypatch.setattr(
        "services.appointment_service.AppointmentService",
        lambda: FakeAppointmentService(),
    )
    start = time_config.format_datetime(time_config.today().replace(hour=15, minute=0) + timedelta(days=1))

    result = TechnicianFinder().find_technician_with_thought(
        {
            "start_time": start,
            "duration": "60分钟",
            "gender": "女",
            "preference": "无",
            "technician_name": "未知",
            "excluded_technician_ids": [4],
        }
    )

    assert result["name"] == "李娜"
