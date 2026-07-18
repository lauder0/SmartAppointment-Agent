from __future__ import annotations

import asyncio

from langchain_core.messages import HumanMessage

import agents.specialists.booking_agent.actions as booking_actions
from agents.specialists.booking_agent.flow import run_booking_flow
from agents.supervisor.orchestration.nodes import supervisor_entry_node, supervisor_router_node
from agents.supervisor.state import (
    default_availability_state,
    default_booking_state,
    default_consultation_state,
    default_recommendation_state,
    default_shared_focus_context,
)


class EmptyPreferenceRecall:
    def invoke(self, _payload):
        return {"success": True, "data": {"profile": {}}}


def test_past_implicit_time_requests_a_date_instead_of_gender(monkeypatch):
    fixed_now = booking_actions.time_config.today().replace(hour=20, minute=0)
    monkeypatch.setattr(booking_actions.time_config, "now", lambda: fixed_now)
    monkeypatch.setattr(booking_actions, "recall_preferences_tool", EmptyPreferenceRecall())
    state = {
        "user_id": "u1",
        "messages": [HumanMessage(content="我想下午三点去")],
        "focus_context": {"service_type": "全身推拿", "duration_minutes": 60},
        "availability_result": {},
        "booking": default_booking_state(),
        "route_decision": {"action": "start_or_continue_booking"},
        "tool_results": {},
    }

    result = asyncio.run(run_booking_flow("start_or_continue_booking", state))

    assert result["booking"]["missing_fields"] == ["start_time"]
    assert "今天已经过去" in result["response_facts"]["body"]
    assert "男技师" not in result["response_facts"]["body"]


def test_gender_is_optional_when_matching_a_technician(monkeypatch):
    captured = {}

    class MatchAnyTechnician:
        def invoke(self, payload):
            captured.update(payload)
            return {
                "success": True,
                "data": {
                    "match_type": "direct",
                    "technician": {"id": 3, "name": "王强", "gender": "男"},
                },
            }

    monkeypatch.setattr(booking_actions, "recall_preferences_tool", EmptyPreferenceRecall())
    monkeypatch.setattr(booking_actions, "match_technician", MatchAnyTechnician())
    state = {
        "user_id": "u1",
        "messages": [HumanMessage(content="我想明天下午三点去")],
        "focus_context": {"service_type": "全身推拿", "duration_minutes": 60},
        "availability_result": {},
        "booking": default_booking_state(),
        "route_decision": {"action": "start_or_continue_booking"},
        "tool_results": {},
    }

    result = asyncio.run(run_booking_flow("start_or_continue_booking", state))

    assert captured["gender_preference"] is None
    assert result["booking"]["status"] == "awaiting_confirmation"
    assert result["booking"]["selected_option"]["technician_name"] == "王强"


def test_replace_technician_is_a_modification_not_a_cancellation():
    state = {
        "session_id": "replace-route",
        "user_id": "u1",
        "messages": [HumanMessage(content="换一个技师")],
        "shared_focus_context": default_shared_focus_context(),
        "consultation": default_consultation_state(),
        "availability": default_availability_state(),
        "booking": {
            **default_booking_state(),
            "status": "awaiting_confirmation",
            "draft": {
                "service_type": "全身推拿",
                "start_time": "2026-07-19 15:00",
                "duration_minutes": 60,
            },
            "selected_option": {"technician_id": 2, "technician_name": "李娜"},
        },
        "recommendation": default_recommendation_state(),
        "task_stack": [],
        "tool_results": {},
    }

    state.update(asyncio.run(supervisor_entry_node(state)))
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["route_decision"]["action"] == "start_or_continue_booking"
    assert state["route_decision"]["reason"] == "modify_pending_booking"


def test_replace_technician_excludes_current_selection(monkeypatch):
    captured = {}

    class MatchAnotherTechnician:
        def invoke(self, payload):
            captured.update(payload)
            return {
                "success": True,
                "data": {
                    "match_type": "direct",
                    "technician": {"id": 5, "name": "王强", "gender": "男"},
                },
            }

    monkeypatch.setattr(booking_actions, "recall_preferences_tool", EmptyPreferenceRecall())
    monkeypatch.setattr(booking_actions, "match_technician", MatchAnotherTechnician())
    state = {
        "user_id": "u1",
        "messages": [HumanMessage(content="我要换一个技师")],
        "focus_context": {},
        "availability_result": {},
        "booking": {
            **default_booking_state(),
            "status": "awaiting_confirmation",
            "draft": {
                "service_type": "全身推拿",
                "start_time": "2026-07-19 15:00",
                "duration_minutes": 60,
                "technician_id": 2,
                "technician_name": "李娜",
            },
            "selected_option": {"technician_id": 2, "technician_name": "李娜"},
        },
        "route_decision": {"action": "start_or_continue_booking"},
        "tool_results": {},
    }

    result = asyncio.run(run_booking_flow("start_or_continue_booking", state))

    assert captured["excluded_technician_ids"] == [2]
    assert result["booking"]["selected_option"]["technician_name"] == "王强"
    assert result["booking"]["status"] == "awaiting_confirmation"
