from __future__ import annotations

import asyncio

from langchain_core.messages import HumanMessage

from agents.supervisor.nodes import supervisor_entry_node, supervisor_router_node
from agents.supervisor.routing import route_supervisor_decision
from agents.supervisor.state import (
    default_availability_state,
    default_booking_state,
    default_consultation_state,
    default_recommendation_state,
    default_shared_focus_context,
)


def _state(user_text: str) -> dict:
    return {
        "session_id": "contract-session",
        "user_id": "contract-user",
        "messages": [HumanMessage(content=user_text)],
        "shared_focus_context": default_shared_focus_context(),
        "consultation": default_consultation_state(),
        "availability": default_availability_state(),
        "booking": default_booking_state(),
        "recommendation": default_recommendation_state(),
        "task_stack": [],
        "tool_results": {},
    }


async def _route(user_text: str) -> dict:
    state = _state(user_text)
    state.update(await supervisor_entry_node(state))
    state.update(await supervisor_router_node(state))
    return state


def test_entry_initializes_3_0_state_containers():
    state = _state("\u4f60\u597d")
    update = asyncio.run(supervisor_entry_node(state))

    assert "shared_focus_context" in update
    assert "consultation" in update
    assert "availability" in update
    assert "booking" in update
    assert "recommendation" in update
    assert update["route_decision"] is None


def test_supervisor_routes_knowledge_query_without_llm():
    state = asyncio.run(_route("\u4f60\u4eec\u6709\u54ea\u4e9b\u670d\u52a1\u9879\u76ee\uff1f"))

    assert state["active_agent"] == "consultation"
    assert state["route_decision"]["action"] == "answer_knowledge"


def test_supervisor_routes_availability_query_without_llm():
    state = asyncio.run(_route("\u660e\u5929\u4e0b\u5348\u56db\u70b9\u6709\u54ea\u4e9b\u5973\u6280\u5e08\u53ef\u4ee5\u7ea6\u4e00\u4e2a\u5c0f\u65f6\uff1f"))

    assert state["active_agent"] == "availability"
    assert state["route_decision"]["action"] == "query_availability"


def test_supervisor_routes_booking_request_without_llm():
    state = asyncio.run(_route("\u5e2e\u6211\u9884\u7ea6\u660e\u5929\u4e0b\u5348\u4e09\u70b9\u505a\u6309\u6469"))

    assert state["active_agent"] == "booking"
    assert state["route_decision"]["action"] == "start_or_continue_booking"


def test_pending_booking_confirmation_is_guarded_by_supervisor_rules():
    state = _state("\u786e\u8ba4")
    booking = default_booking_state()
    booking["status"] = "awaiting_confirmation"
    state["booking"] = booking

    state.update(asyncio.run(supervisor_entry_node(state)))
    state["booking"] = booking
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["active_agent"] == "booking"
    assert state["route_decision"]["action"] == "confirm_booking"


def test_recommendation_route_is_registered():
    state = {"route_decision": {"action": "generate_recommendation"}}

    assert route_supervisor_decision(state) == "recommendation"
