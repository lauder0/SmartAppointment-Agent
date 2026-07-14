from __future__ import annotations

import asyncio

from langchain_core.messages import HumanMessage

from agents.supervisor.nodes import supervisor_entry_node, supervisor_router_node
from agents.supervisor.nodes import supervisor_continue_node
from agents.supervisor.routing import route_after_availability, route_after_consultation
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


def test_supervisor_routes_service_catalog_short_question_without_llm():
    state = asyncio.run(_route("你们有什么项目"))

    assert state["active_agent"] == "consultation"
    assert state["route_decision"]["action"] == "answer_knowledge"
    assert state["route_decision"]["reason"] == "rule_knowledge_query"


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


def test_service_selection_with_recommendation_becomes_recommendation_task():
    state = _state("我想做全身推拿，你有推荐的技师吗")
    state["shared_focus_context"]["last_offer"] = "service_catalog"

    state.update(asyncio.run(supervisor_entry_node(state)))
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["active_agent"] == "availability"
    assert state["route_decision"]["action"] == "query_availability"
    assert state["route_decision"]["reason"] == "prepare_candidates_for_recommendation"
    assert state["route_decision"]["task_type"] == "recommendation_before_booking"
    assert state["route_decision"]["primary_intent"] == "recommend_technician"
    assert "service_selection" in state["route_decision"]["secondary_intents"]
    assert state["route_decision"]["slot_updates"]["service_type"] in {"全身推拿", "鍏ㄨ韩鎺ㄦ嬁"}
    assert state["task_frame"]["task_type"] == "recommendation_before_booking"


def test_recommendation_task_continues_when_user_provides_time():
    state = _state("今天下午五点")
    state["shared_focus_context"]["service_type"] = "全身推拿"
    state["task_frame"] = {
        "task_id": "task_contract_recommendation",
        "task_type": "recommendation_before_booking",
        "status": "collecting_slots",
        "primary_intent": "recommend_technician",
        "secondary_intents": ["service_selection"],
        "collected_slots": {"service_type": "全身推拿"},
        "missing_slots": ["start_time"],
        "pending_next": "query_availability",
        "last_question_type": "ask_missing_slots",
        "subtasks": [],
        "confirmations_required": [],
        "conflicts": [],
        "invalidates": [],
        "safety_flags": [],
        "risk_level": "low",
        "source": "test",
        "confidence": 0.9,
        "updated_at": "",
    }

    state.update(asyncio.run(supervisor_entry_node(state)))
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["active_agent"] == "availability"
    assert state["route_decision"]["action"] == "query_availability"
    assert state["route_decision"]["task_type"] == "recommendation_before_booking"
    assert state["route_decision"]["reason"] == "prepare_candidates_for_recommendation"
    assert "start_time" in state["route_decision"]["slot_updates"]


def test_booking_confirmation_context_overrides_generic_confirmation():
    state = _state("可以")
    booking = default_booking_state()
    booking["status"] = "awaiting_confirmation"
    state["booking"] = booking

    state.update(asyncio.run(supervisor_entry_node(state)))
    state["booking"] = booking
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["active_agent"] == "booking"
    assert state["route_decision"]["action"] == "confirm_booking"
    assert state["route_decision"]["task_type"] == "booking_confirmation"


def test_knowledge_plus_booking_uses_query_first_continuation():
    state = _state("你们有哪些服务项目？帮我预约明天下午三点做全身推拿")

    state.update(asyncio.run(supervisor_entry_node(state)))
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["active_agent"] == "consultation"
    assert state["route_decision"]["action"] == "answer_knowledge"
    assert state["route_decision"]["reason"] == "query_first_knowledge_then_continue"
    assert state["route_decision"]["execution_policy"] == "query_first_then_continue"
    assert state["route_decision"]["continuation"]["action"] == "start_or_continue_booking"
    assert state["task_frame"]["execution_policy"] == "query_first_then_continue"


def test_availability_plus_booking_uses_query_first_continuation():
    state = _state("明天下午三点有哪些技师可以约？有合适的帮我预约全身推拿")

    state.update(asyncio.run(supervisor_entry_node(state)))
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["active_agent"] == "availability"
    assert state["route_decision"]["action"] == "query_availability"
    assert state["route_decision"]["reason"] == "query_first_availability_then_continue"
    assert state["route_decision"]["execution_policy"] == "query_first_then_continue"
    assert state["route_decision"]["continuation"]["action"] == "start_or_continue_booking"


def test_continue_node_promotes_pending_continuation_and_stashes_query_reply():
    state = _state("明天下午三点有哪些技师可以约？有合适的帮我预约全身推拿")
    state["route_decision"] = {
        "action": "query_availability",
        "reason": "query_first_availability_then_continue",
        "continuation": {
            "action": "start_or_continue_booking",
            "reason": "continue_booking_after_availability_query",
            "task_type": "booking_creation",
            "primary_intent": "start_booking",
            "secondary_intents": ["availability_query"],
        },
    }
    state["final_response"] = "这里是排班查询结果。"

    update = asyncio.run(supervisor_continue_node(state))

    assert update["active_agent"] == "booking"
    assert update["route_decision"]["action"] == "start_or_continue_booking"
    assert update["tool_results"]["query_first_intermediate_responses"] == ["这里是排班查询结果。"]


def test_query_first_routes_continue_after_consultation_or_availability():
    state = {
        "route_decision": {"continuation": {"action": "start_or_continue_booking"}},
        "availability": {"options": [{"technician_id": 1}]},
    }

    assert route_after_consultation(state) == "continue"
    assert route_after_availability(state) == "continue"
