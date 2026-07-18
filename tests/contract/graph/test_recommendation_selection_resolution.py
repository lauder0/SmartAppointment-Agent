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


def test_named_recommendation_selection_routes_to_booking():
    state = {
        "session_id": "named-selection-route",
        "user_id": "u1",
        "messages": [HumanMessage(content="那我选择王强")],
        "shared_focus_context": default_shared_focus_context(),
        "consultation": default_consultation_state(),
        "availability": default_availability_state(),
        "booking": default_booking_state(),
        "recommendation": {
            **default_recommendation_state(),
            "status": "awaiting_selection",
            "selected_recommendation": {"technician_id": 7, "technician_name": "王强"},
        },
        "task_stack": [],
        "tool_results": {},
    }

    state.update(asyncio.run(supervisor_entry_node(state)))
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["route_decision"]["action"] == "select_recommended_technician"
    assert state["route_decision"]["slot_updates"]["technician_name"] == "王强"


def test_accepting_named_candidate_resolves_missing_internal_id(monkeypatch):
    class FakeTechnicianLookup:
        def invoke(self, payload):
            assert payload == {"technician_name": "王强"}
            return {
                "success": True,
                "data": {"technician": {"id": 7, "name": "王强", "strength": "力气大"}},
            }

    monkeypatch.setattr(booking_actions, "get_technician_by_name", FakeTechnicianLookup())
    state = {
        "session_id": "resolve-technician-id",
        "user_id": "u1",
        "messages": [HumanMessage(content="那我选择王强")],
        "focus_context": {
            "service_type": "背部推拿",
            "start_time": "2026-07-19 15:00",
            "duration_minutes": 40,
        },
        "availability_result": {
            "criteria_snapshot": {
                "service_type": "背部推拿",
                "start_time": "2026-07-19 15:00",
                "duration_minutes": 40,
            },
            "options": [],
        },
        "booking": default_booking_state(),
        "recommendation": {
            **default_recommendation_state(),
            "status": "awaiting_selection",
            "selected_recommendation": {
                "technician_name": "王强",
                "strength": "力气大",
            },
        },
        "route_decision": {
            "action": "select_recommended_technician",
            "slot_updates": {"technician_name": "王强"},
        },
        "tool_results": {},
    }

    result = asyncio.run(run_booking_flow("select_recommended_technician", state))

    assert result["booking"]["status"] == "awaiting_confirmation"
    assert result["booking"]["selected_option"]["technician_id"] == 7
    assert result["booking"]["draft"]["technician_name"] == "王强"
    assert result["response_type"] == "booking_confirmation"


def test_unresolved_technician_never_asks_user_for_internal_id(monkeypatch):
    class MissingTechnicianLookup:
        def invoke(self, _payload):
            return {"success": False, "data": {"technician": None}}

    monkeypatch.setattr(booking_actions, "get_technician_by_name", MissingTechnicianLookup())
    state = {
        "messages": [HumanMessage(content="我选择不存在的技师")],
        "focus_context": {},
        "availability_result": {"criteria_snapshot": {}, "options": []},
        "booking": default_booking_state(),
        "recommendation": {
            **default_recommendation_state(),
            "status": "awaiting_selection",
        },
        "route_decision": {
            "action": "select_recommended_technician",
            "slot_updates": {"technician_name": "不存在的技师"},
        },
        "tool_results": {},
    }

    result = asyncio.run(run_booking_flow("select_recommended_technician", state))

    assert result["booking"]["selected_option"] is None
    assert result["booking"]["missing_fields"] == []
    assert "technician_id" not in result["response_facts"]["body"]
