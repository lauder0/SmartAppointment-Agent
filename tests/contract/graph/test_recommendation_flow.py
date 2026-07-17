from __future__ import annotations

import asyncio

from langchain_core.messages import HumanMessage

import agents.specialists.recommendation_agent.nodes as recommendation_nodes
from agents.specialists.booking_agent.flow import run_booking_flow
from agents.specialists.recommendation_agent.nodes import recommend_technician_node
from agents.supervisor.orchestration.nodes import supervisor_entry_node, supervisor_router_node
from agents.supervisor.state import (
    default_booking_state,
    default_consultation_state,
    default_recommendation_state,
    default_shared_focus_context,
)


def _supervisor_state(user_text: str) -> dict:
    return {
        "session_id": "recommendation-contract",
        "user_id": "u1",
        "messages": [HumanMessage(content=user_text)],
        "shared_focus_context": {
            **default_shared_focus_context(),
            "service_type": "全身推拿",
            "start_time": "2026-07-11 15:00",
            "duration_minutes": 60,
        },
        "consultation": default_consultation_state(),
        "availability": {
            "status": "completed",
            "criteria_snapshot": {
                "service_type": "全身推拿",
                "start_time": "2026-07-11 15:00",
                "duration_minutes": 60,
            },
            "options": [
                {
                    "technician_id": 1,
                    "technician_name": "张伟",
                    "service_type": "全身推拿",
                    "start_time": "2026-07-11 15:00",
                    "duration_minutes": 60,
                },
                {
                    "technician_id": 2,
                    "technician_name": "李娜",
                    "service_type": "全身推拿",
                    "start_time": "2026-07-11 15:00",
                    "duration_minutes": 60,
                },
            ],
            "available_technician_names": ["张伟", "李娜"],
            "last_answer": None,
        },
        "booking": default_booking_state(),
        "recommendation": default_recommendation_state(),
        "task_stack": [],
        "tool_results": {},
    }


def test_supervisor_routes_preference_request_to_recommendation():
    state = _supervisor_state("我想要力气大一点的，你帮我推荐一个吧")
    state.update(asyncio.run(supervisor_entry_node(state)))
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["active_agent"] == "recommendation"
    assert state["route_decision"]["action"] == "generate_recommendation"


def test_supervisor_routes_colloquial_recommendation_selection_to_booking():
    state = _supervisor_state("就他吧")
    state["recommendation"] = {
        **default_recommendation_state(),
        "status": "awaiting_selection",
        "selected_recommendation": {
            "technician_id": 1,
            "technician_name": "张伟",
        },
    }
    state.update(asyncio.run(supervisor_entry_node(state)))
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["active_agent"] == "booking"
    assert state["route_decision"]["action"] == "select_recommended_technician"


def test_recommendation_node_saves_ranked_result(monkeypatch):
    class FakeRanker:
        def rank(self, **_kwargs):
            return [
                {
                    "technician_id": 1,
                    "technician_name": "张伟",
                    "gender": "男",
                    "strength": "力气大，擅长深层组织按摩",
                    "score": 0.91,
                    "matched_features": ["力气大", "深层"],
                },
                {
                    "technician_id": 2,
                    "technician_name": "李娜",
                    "gender": "女",
                    "strength": "手法细腻",
                    "score": 0.55,
                    "matched_features": [],
                },
            ]

    class FakeRankTool:
        def invoke(self, payload):
            return {"success": True, "data": {"ranked": FakeRanker().rank(**payload)}}

    monkeypatch.setattr(recommendation_nodes, "rank_technicians", FakeRankTool())
    monkeypatch.setattr(recommendation_nodes, "recall_preferences", lambda _state: {})

    result = asyncio.run(
        recommend_technician_node(
            _supervisor_state("我想要力气大一点的，你帮我推荐一个吧")
        )
    )

    assert result["recommendation"]["status"] == "awaiting_selection"
    assert result["recommendation"]["selected_recommendation"]["technician_name"] == "张伟"
    assert result.get("final_response") is None
    assert result["last_agent_result"]["response_type"] == "technician_recommendation"
    assert result["last_agent_result"]["facts"]["recommended_technician"]["technician_name"] == "张伟"
    assert "张伟" in result["last_agent_result"]["facts"]["body"]


def test_accepting_recommendation_enters_booking_confirmation():
    state = {
        "session_id": "accept-recommendation",
        "user_id": "u1",
        "messages": [HumanMessage(content="就他吧")],
        "focus_context": {
            "service_type": "全身推拿",
            "start_time": "2026-07-11 15:00",
            "duration_minutes": 60,
        },
        "availability_result": {
            "criteria_snapshot": {
                "service_type": "全身推拿",
                "start_time": "2026-07-11 15:00",
                "duration_minutes": 60,
            },
            "options": [],
        },
        "booking": default_booking_state(),
        "recommendation": {
            **default_recommendation_state(),
            "status": "awaiting_selection",
            "selected_recommendation": {
                "technician_id": 1,
                "technician_name": "张伟",
                "gender": "男",
                "strength": "力气大",
            },
        },
        "route_decision": {"action": "select_recommended_technician"},
        "tool_results": {},
    }

    result = asyncio.run(run_booking_flow("select_recommended_technician", state))

    assert result["booking"]["status"] == "awaiting_confirmation"
    assert result["booking"]["selected_option"]["technician_name"] == "张伟"
    assert result["response_type"] == "booking_confirmation"
    assert result["response_facts"]["technician_name"] == "张伟"
    assert result.get("final_response") is None


def test_accepting_named_candidate_overrides_current_recommendation():
    state = {
        "session_id": "accept-named-candidate",
        "user_id": "u1",
        "messages": [HumanMessage(content="我选王强吧")],
        "focus_context": {
            "service_type": "背部推拿",
            "start_time": "2026-07-11 15:00",
            "duration_minutes": 40,
        },
        "availability_result": {
            "criteria_snapshot": {
                "start_time": "2026-07-11 15:00",
            },
            "options": [],
        },
        "booking": default_booking_state(),
        "recommendation": {
            **default_recommendation_state(),
            "status": "awaiting_selection",
            "selected_recommendation": {
                "technician_id": 2,
                "technician_name": "李娜",
            },
            "candidate_recommendations": [
                {
                    "technician_id": 2,
                    "technician_name": "李娜",
                },
                {
                    "technician_id": 1,
                    "technician_name": "王强",
                },
            ],
        },
        "route_decision": {
            "action": "select_recommended_technician",
            "slot_updates": {"technician_name": "王强"},
        },
        "tool_results": {},
    }

    result = asyncio.run(run_booking_flow("select_recommended_technician", state))

    draft = result["booking"]["draft"]
    assert result["booking"]["status"] == "awaiting_confirmation"
    assert result["booking"]["selected_option"]["technician_name"] == "王强"
    assert draft["service_type"] == "背部推拿"
    assert draft["duration_minutes"] == 40
    assert result["response_type"] == "booking_confirmation"
    assert result["response_facts"]["technician_name"] == "王强"
    assert result.get("final_response") is None


