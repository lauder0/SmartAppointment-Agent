from __future__ import annotations

from datetime import timedelta

import pytest

import api.graph_chat_handler as graph_chat_handler
from agents._shared.state import default_availability_result, default_focus_context
from config.time_config import time_config
from services.session_state_store import MemorySessionStateStore
from tools import availability_tools


class FakeAvailabilityService:
    def parse_query_criteria(self, text):
        start = time_config.today().replace(hour=15, minute=0) + timedelta(days=1)
        return {
            "date": start.replace(hour=0, minute=0),
            "duration_minutes": None,
            "gender": "�?,
            "technician_name": None,
            "service_type": None,
            "preference": None,
            "start_time": start,
            "has_explicit_date": True,
            "has_explicit_time": True,
            "has_explicit_duration": False,
            "has_explicit_gender": True,
            "has_explicit_technician_name": False,
            "has_explicit_service_type": False,
            "has_explicit_preference": False,
        }

    def merge_query_criteria(self, base_criteria, current_criteria):
        return {**(base_criteria or {}), **current_criteria}

    def answer_availability_query(self, text, base_criteria=None):
        return "[REPLY][咨询机器人]明天下午三点女技师李娜可约�?

    def extract_available_technician_names(self, response):
        return ["李娜"]


@pytest.fixture
def graph_memory_store(monkeypatch):
    store = MemorySessionStateStore(ttl_seconds=60)
    monkeypatch.setattr(graph_chat_handler, "_session_store", store)
    monkeypatch.setattr(graph_chat_handler, "_graph", None)
    return store


@pytest.mark.asyncio
async def test_availability_query_flow_persists_result(monkeypatch, graph_memory_store):
    monkeypatch.setattr(availability_tools, "AvailabilityService", FakeAvailabilityService)

    result = await graph_chat_handler.process_user_input_graph(
        "明天下午三点有哪些女技师可约？",
        session_id="e2e-availability",
        user_id="u1",
    )

    assert result["route_decision"]["action"] == "query_availability"
    assert "李娜" in result["final_response"]
    assert result["availability"]["available_technician_names"] == ["李娜"]

    stored = await graph_chat_handler.get_graph_session_state("e2e-availability")
    assert stored["availability"]["available_technician_names"] == ["李娜"]


@pytest.mark.asyncio
async def test_pending_confirmation_can_be_cancelled(graph_memory_store):
    await graph_memory_store.set(
        "e2e-cancel",
        {
            "session_id": "e2e-cancel",
            "user_id": "u1",
            "messages": [],
            "focus_context": default_focus_context(),
            "availability_result": default_availability_result(),
            "booking": {
                "status": "awaiting_confirmation",
                "draft": {
                    "service_type": "肩颈推拿",
                    "start_time": "2026-06-11 15:00",
                    "duration_minutes": 60,
                },
                "missing_fields": [],
                "confirmation_summary": "待确认预�?,
                "selected_option": {
                    "technician_id": 1,
                    "technician_name": "李娜",
                },
                "guard_result": None,
            },
            "tool_results": {},
        },
    )

    result = await graph_chat_handler.process_user_input_graph(
        "取消",
        session_id="e2e-cancel",
        user_id="u1",
    )

    assert result["route_decision"]["action"] == "cancel_booking"
    assert result["booking"]["status"] == "cancelled"
    assert result["booking"]["draft"] == {}
    assert "已取�? in result["final_response"]
