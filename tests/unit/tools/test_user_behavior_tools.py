from __future__ import annotations

from services.user_behavior_service import UserBehaviorService
from tools import user_behavior_tools


def test_record_user_behavior_tool_requires_action_type():
    result = user_behavior_tools.record_user_behavior.invoke(
        {
            "user_id": "u1",
            "action_type": "",
            "action_data": {},
            "session_id": "s1",
        }
    )

    assert result["success"] is False
    assert result["error"] == "missing_action_type"


def test_record_user_behavior_tool_records_appointment(tmp_db_url, monkeypatch):
    service = UserBehaviorService(tmp_db_url)
    technician_id = service.db_router.technicians.add_technician("李娜", gender="女", strength="肩颈放松")
    service.db_router.close()

    monkeypatch.setattr(
        user_behavior_tools,
        "UserBehaviorService",
        lambda: UserBehaviorService(tmp_db_url),
    )

    result = user_behavior_tools.record_user_behavior.invoke(
        {
            "user_id": "u1",
            "action_type": "appointment",
            "action_data": {
                "service_name": "肩颈推拿",
                "start_time": "2026-06-11 15:00",
                "duration_minutes": 60,
            },
            "technician_id": str(technician_id),
            "session_id": "s1",
        }
    )

    verify = UserBehaviorService(tmp_db_url)
    behaviors = verify.get_user_behaviors("u1")
    verify.db_router.close()

    assert result["success"] is True
    assert len(behaviors) == 1
