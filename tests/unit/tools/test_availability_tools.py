from __future__ import annotations

from datetime import timedelta

from config.time_config import time_config
from tools import availability_tools


class FakeAvailabilityService:
    def parse_query_criteria(self, text):
        start = time_config.today().replace(hour=15, minute=0) + timedelta(days=1)
        return {
            "date": start.replace(hour=0, minute=0),
            "duration_minutes": 60 if "一小时" in text else None,
            "gender": "女" if "女" in text else None,
            "technician_name": None,
            "service_type": "肩颈推拿" if "肩颈" in text else None,
            "preference": None,
            "start_time": start,
            "has_explicit_date": "明天" in text,
            "has_explicit_time": True,
            "has_explicit_duration": "一小时" in text,
            "has_explicit_gender": "女" in text,
            "has_explicit_technician_name": False,
            "has_explicit_service_type": "肩颈" in text,
            "has_explicit_preference": False,
        }

    def merge_query_criteria(self, base_criteria, current_criteria):
        merged = dict(base_criteria)
        for key, value in current_criteria.items():
            if value not in (None, "", []):
                merged[key] = value
        return merged

    def answer_availability_query(self, text, base_criteria=None):
        return "[REPLY][咨询机器人]李娜可约。"

    def extract_available_technician_names(self, response):
        return ["李娜"]


def test_query_availability_tool_returns_serialized_criteria(monkeypatch):
    monkeypatch.setattr(availability_tools, "AvailabilityService", FakeAvailabilityService)

    result = availability_tools.query_availability.invoke({"text": "明天下午三点女技师一小时可约吗"})

    assert result["success"] is True
    assert result["data"]["available_technician_names"] == ["李娜"]
    assert isinstance(result["data"]["criteria"]["start_time"], str)
    assert result["data"]["criteria"]["gender"] == "女"
    assert result["data"]["criteria"]["duration_minutes"] == 60


def test_query_availability_tool_merges_base_criteria(monkeypatch):
    monkeypatch.setattr(availability_tools, "AvailabilityService", FakeAvailabilityService)
    base_start = time_config.format_datetime(time_config.today().replace(hour=14, minute=0) + timedelta(days=1))

    result = availability_tools.query_availability.invoke(
        {
            "text": "女技师一小时",
            "base_criteria": {
                "start_time": base_start,
                "date": base_start,
                "service_type": "肩颈推拿",
            },
        }
    )

    assert result["success"] is True
    assert result["data"]["criteria"]["service_type"] == "肩颈推拿"
    assert result["data"]["criteria"]["gender"] == "女"
