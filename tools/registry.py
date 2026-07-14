"""Tool protocol metadata for routing, risk control, and test contracts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "search_knowledge": {
        "description": "查询服务项目、门店规则、常见问题等知识。",
        "permission": "read",
        "timeout_ms": 3000,
        "retryable": True,
        "idempotent": True,
        "risk_level": "low",
        "error_codes": ["knowledge_search_failed"],
    },
    "query_availability": {
        "description": "查询指定时间、服务、时长和偏好下的可约技师。",
        "permission": "read",
        "timeout_ms": 3000,
        "retryable": True,
        "idempotent": True,
        "risk_level": "low",
        "error_codes": ["invalid_start_time", "availability_query_failed", "no_availability"],
    },
    "match_technician": {
        "description": "为完整预约草稿匹配或推荐技师。",
        "permission": "read",
        "timeout_ms": 3000,
        "retryable": True,
        "idempotent": True,
        "risk_level": "low",
        "error_codes": ["invalid_start_time", "no_available_technician", "technician_match_failed"],
    },
    "create_appointment": {
        "description": "在用户确认后创建预约和技师忙碌排班。",
        "permission": "write",
        "timeout_ms": 5000,
        "retryable": False,
        "idempotent": True,
        "risk_level": "high",
        "requires_confirmation": True,
        "idempotency_key_fields": [
            "session_id",
            "technician_id",
            "service_name",
            "start_time",
            "duration_minutes",
        ],
        "error_codes": [
            "invalid_start_time",
            "outside_booking_window",
            "appointment_conflict",
            "schedule_conflict",
            "technician_unavailable",
            "service_exception",
        ],
    },
    "record_user_behavior": {
        "description": "记录用户预约行为，用于后续偏好召回。",
        "permission": "write",
        "timeout_ms": 2000,
        "retryable": True,
        "idempotent": False,
        "risk_level": "medium",
        "error_codes": ["missing_action_type", "record_behavior_failed"],
    },
    "get_weather": {
        "description": "查询天气信息，用于闲聊或外部上下文补充。",
        "permission": "read",
        "timeout_ms": 3000,
        "retryable": True,
        "idempotent": True,
        "risk_level": "low",
        "error_codes": ["weather_query_failed"],
    },
}


def get_tool_metadata(name: str) -> dict[str, Any] | None:
    metadata = TOOL_REGISTRY.get(name)
    return deepcopy(metadata) if metadata else None
