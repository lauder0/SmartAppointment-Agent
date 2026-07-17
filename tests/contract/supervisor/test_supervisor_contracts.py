from __future__ import annotations

import asyncio

from langchain_core.messages import HumanMessage

import agents.specialists.booking_agent.graph as booking_graph
from agents.specialists.result_contract import agent_result
from agents.specialists.booking_agent.result_contract import (
    BOOKING_RESULT_CONTRACT_VERSION,
    booking_contract_to_specialist_result,
    build_booking_result_contract,
)
from agents.supervisor.orchestration.nodes import supervisor_entry_node, supervisor_router_node
from agents.supervisor.orchestration.nodes import supervisor_continue_node
from agents.supervisor.orchestration.response import supervisor_response_node
from agents.supervisor.orchestration.routing import route_after_agent_result
from agents.supervisor.orchestration.routing import route_supervisor_decision
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
    assert update["turn_results"] == []


def test_entry_resets_turn_results_for_each_user_turn():
    state = _state("浣犲�?)
    state["turn_results"] = [{"agent_name": "consultation", "result_type": "old"}]

    update = asyncio.run(supervisor_entry_node(state))

    assert update["turn_results"] == []


def test_specialist_result_contract_contains_supervisor_fields():
    result = agent_result(
        "availability",
        "completed",
        "availability_result",
        "这里是排班结果�?,
        {"availability": {"status": "completed"}},
    )

    assert result["agent_name"] == "availability"
    assert result["response_type"] == "availability_result"
    assert result["facts"]["availability"]["status"] == "completed"
    assert result["suggested_next_tasks"] == []


def test_booking_subgraph_returns_structured_confirmation_contract(monkeypatch):
    async def fake_run_booking_flow(action, _state):
        assert action == "select_recommended_technician"
        return {
            "booking": {
                "status": "awaiting_confirmation",
                "draft": {
                    "service_type": "鍏ㄨ韩鎺ㄦ嬁",
                    "start_time": "2026-07-16 15:00",
                    "duration_minutes": 60,
                    "technician_name": "鐜嬪�?,
                    "technician_id": 1,
                },
                "missing_fields": [],
                "selected_option": {
                    "technician_id": 1,
                    "technician_name": "鐜嬪�?,
                },
            },
            "result_type": "booking_confirmation",
            "response_type": "booking_confirmation",
            "response_facts": {
                "time_line": "2026�?7�?6�?15:00-16:00",
                "service_type": "鍏ㄨ韩鎺ㄦ嬁",
                "duration_minutes": 60,
                "technician_name": "鐜嬪�?,
            },
        }

    monkeypatch.setattr(booking_graph, "run_booking_flow", fake_run_booking_flow)
    state = _state("就他�?)
    state["route_decision"] = {"action": "select_recommended_technician"}

    result = asyncio.run(booking_graph.booking_subgraph_node(state))

    agent_result_payload = result["last_agent_result"]
    booking_result = agent_result_payload["facts"]["booking_result"]
    assert agent_result_payload["agent_name"] == "booking"
    assert agent_result_payload["result_type"] == "booking_confirmation"
    assert agent_result_payload["response_type"] == "booking_confirmation"
    assert booking_result["version"] == BOOKING_RESULT_CONTRACT_VERSION
    assert booking_result["requires_user_input"] is True
    assert booking_result["next_expected_user_action"] == "confirm_or_cancel_booking"
    assert booking_result["write_performed"] is False
    assert booking_result["draft_snapshot"]["service_type"] == "鍏ㄨ韩鎺ㄦ嬁"
    assert booking_result["selected_option"]["technician_name"] == "鐜嬪�?
    assert result["turn_results"][-1]["facts"]["booking_result"]["status"] == "awaiting_confirmation"


def test_booking_created_contract_marks_write_and_safety_fields():
    booking = default_booking_state()
    completed = {
        "draft": {
            "service_type": "鑳岄儴鎺ㄦ嬁",
            "start_time": "2026-07-16 15:00",
            "duration_minutes": 40,
        },
        "selected_option": {
            "technician_id": 2,
            "technician_name": "鏉庡�?,
        },
        "create_result": {"appointment_id": 99},
    }
    aggregate = {
        "result_type": "booking_created",
        "response_type": "booking_success",
        "response_facts": {
            "technician_name": "鏉庡�?,
            "start_time": "2026-07-16 15:00",
            "end_time_text": "15:40",
            "service_type": "鑳岄儴鎺ㄦ嬁",
            "duration_minutes": 40,
        },
    }
    merged_state = {
        "last_completed_booking": completed,
        "tool_results": {
            "booking_guard": {"success": True, "reason": "ready_to_create"},
            "create_appointment": {
                "success": True,
                "data": {"idempotency_key": "idem-1", "appointment_id": 99},
            },
        },
    }

    contract = build_booking_result_contract(
        action="confirm_booking",
        booking=booking,
        aggregate=aggregate,
        merged_state=merged_state,
    )
    specialist_result = booking_contract_to_specialist_result(contract)

    assert contract["status"] == "completed"
    assert contract["result_type"] == "booking_created"
    assert contract["response_type"] == "booking_success"
    assert contract["requires_user_input"] is False
    assert contract["write_performed"] is True
    assert contract["safety"]["confirmed"] is True
    assert contract["safety"]["guard_success"] is True
    assert contract["safety"]["idempotency_key"] == "idem-1"
    assert specialist_result["facts"]["booking_result"]["completed_booking"] == completed
    assert specialist_result["state_updates"]["last_completed_booking"] == completed


def test_supervisor_response_node_publishes_last_agent_result_message():
    state = _state("查一下排�?)
    result = agent_result(
        "availability",
        "completed",
        "availability_result",
        "这里是排班结果�?,
    )
    state["last_agent_result"] = result
    state["turn_results"] = [result]

    update = asyncio.run(supervisor_response_node(state))

    assert update["final_response"].endswith("这里是排班结果�?)
    assert update["tool_results"]["supervisor_response"]["published"] is True
    assert update["tool_results"]["supervisor_response"]["result_count"] == 1
    assert update["tool_results"]["supervisor_response"]["writer"]["rendered_result_count"] == 1


def test_supervisor_response_composes_query_first_from_turn_results_only():
    state = _state("先查排班再预�?)
    availability_result = agent_result(
        "availability",
        "completed",
        "availability_result",
        "这里是排班查询结果�?,
    )
    booking_result = agent_result(
        "booking",
        "awaiting_confirmation",
        "booking_confirmation",
        None,
        response_type="booking_confirmation",
        facts={
            "time_line": "2026�?7�?6�?15:00-16:00",
            "service_type": "鍏ㄨ韩鎺ㄦ嬁",
            "duration_minutes": 60,
            "technician_name": "鐜嬪�?,
        },
    )
    state["turn_results"] = [availability_result, booking_result]
    state["last_agent_result"] = booking_result
    state["tool_results"] = {}

    update = asyncio.run(supervisor_response_node(state))

    assert "这里是排班查询结果�? in update["final_response"]
    assert "请问是否确认预约" in update["final_response"]
    assert "query_first_intermediate_responses" not in update["tool_results"]


def test_supervisor_routes_knowledge_query_without_llm():
    state = asyncio.run(_route("\u4f60\u4eec\u6709\u54ea\u4e9b\u670d\u52a1\u9879\u76ee\uff1f"))

    assert state["active_agent"] == "consultation"
    assert state["route_decision"]["action"] == "answer_knowledge"


def test_supervisor_routes_service_catalog_short_question_without_llm():
    state = asyncio.run(_route("你们有什么项�?))

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
    assert state["route_decision"]["slot_updates"]["service_type"] == "全身推拿"
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


def test_knowledge_plus_booking_uses_query_first_plan():
    state = _state("你们有哪些服务项目？帮我预约明天下午三点做全身推�?)

    state.update(asyncio.run(supervisor_entry_node(state)))
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["active_agent"] == "consultation"
    assert state["route_decision"]["action"] == "answer_knowledge"
    assert state["route_decision"]["reason"] == "query_first_knowledge_plan"
    assert state["route_decision"]["execution_policy"] == "query_first_plan"
    assert "continuation" not in state["route_decision"]
    assert state["task_frame"]["execution_policy"] == "query_first_plan"
    assert [task["action"] for task in state["execution_plan"]["tasks"]] == [
        "answer_knowledge",
        "start_or_continue_booking",
    ]


def test_availability_plus_booking_uses_query_first_plan():
    state = _state("明天下午三点有哪些技师可以约？有合适的帮我预约全身推拿")

    state.update(asyncio.run(supervisor_entry_node(state)))
    state.update(asyncio.run(supervisor_router_node(state)))

    assert state["active_agent"] == "availability"
    assert state["route_decision"]["action"] == "query_availability"
    assert state["route_decision"]["reason"] == "query_first_availability_plan"
    assert state["route_decision"]["execution_policy"] == "query_first_plan"
    assert "continuation" not in state["route_decision"]
    assert [task["action"] for task in state["execution_plan"]["tasks"]] == [
        "query_availability",
        "start_or_continue_booking",
    ]


def test_continue_node_promotes_pending_plan_task_without_stashing_reply():
    state = _state("明天下午三点有哪些技师可以约？有合适的帮我预约全身推拿")
    state["route_decision"] = {
        "action": "query_availability",
        "reason": "query_first_availability_plan",
        "execution_policy": "query_first_plan",
    }
    state["execution_plan"] = {
        "plan_id": "plan_contract",
        "status": "running",
        "tasks": [
            {
                "task_id": "t1",
                "agent": "availability",
                "action": "query_availability",
                "status": "running",
                "depends_on": [],
                "required": True,
                "input": {"route_decision": state["route_decision"]},
                "result_ref": None,
                "error": None,
                "reason": "query_first_availability_plan",
                "source": "deterministic_planner",
            },
            {
                "task_id": "t2",
                "agent": "booking",
                "action": "start_or_continue_booking",
                "status": "pending",
                "depends_on": ["t1"],
                "required": True,
                "input": {
                    "route_decision": {
                        **state["route_decision"],
                        "action": "start_or_continue_booking",
                        "reason": "planned_followup_task",
                    }
                },
                "result_ref": None,
                "error": None,
                "reason": "planned_followup_task",
                "source": "deterministic_planner",
            },
        ],
        "current_task_id": "t1",
        "completed_task_ids": [],
    }
    result = agent_result("availability", "completed", "availability_result", "这里是排班查询结果�?)
    state["last_agent_result"] = result
    state["turn_results"] = [result]
    state["final_response"] = "这里是排班查询结果�?

    update = asyncio.run(supervisor_continue_node(state))

    assert update["active_agent"] == "booking"
    assert update["route_decision"]["action"] == "start_or_continue_booking"
    assert update["final_response"] is None
    assert "query_first_intermediate_responses" not in update["tool_results"]
    assert update["route_decision"]["trace"]["task_id"] == "t2"


def test_availability_suggested_next_task_routes_through_supervisor_continue():
    state = _state("我想做全身推拿，你推荐个技�?)
    state["route_decision"] = {
        "action": "query_availability",
        "reason": "prepare_candidates_for_recommendation",
        "task_type": "recommendation_before_booking",
    }
    state["execution_plan"] = {
        "plan_id": "plan_contract",
        "status": "running",
        "tasks": [
            {
                "task_id": "t1",
                "agent": "availability",
                "action": "query_availability",
                "status": "running",
                "depends_on": [],
                "required": True,
                "input": {"route_decision": state["route_decision"]},
                "result_ref": None,
                "error": None,
                "reason": "prepare_candidates_for_recommendation",
                "source": "deterministic_planner",
            }
        ],
        "current_task_id": "t1",
        "completed_task_ids": [],
    }
    state["availability"] = {"options": [{"technician_id": 1, "technician_name": "鐜嬪�?}]}
    result = agent_result(
        "availability",
        "completed",
        "availability_result",
        None,
        {"availability": state["availability"]},
        response_type="availability_result",
        facts={"suppress_response": True},
        suggested_next_tasks=[
            {
                "agent": "recommendation",
                "action": "generate_recommendation",
                "reason": "availability_candidates_ready_for_recommendation",
                "input": {"options": state["availability"]["options"]},
                "auto_continue": True,
            }
        ],
    )
    state["last_agent_result"] = result
    state["turn_results"] = [result]

    assert route_after_agent_result(state) == "continue"
    update = asyncio.run(supervisor_continue_node(state))

    assert update["active_agent"] == "recommendation"
    assert update["route_decision"]["action"] == "generate_recommendation"
    assert update["route_decision"]["source"] == "execution_plan"
    assert update["execution_plan"]["tasks"][-1]["source"] == "agent_suggestion"


def test_recommendation_non_auto_suggestion_does_not_auto_book():
    state = _state("推荐一个技�?)
    state["route_decision"] = {"action": "generate_recommendation"}
    state["execution_plan"] = {
        "plan_id": "plan_contract",
        "status": "running",
        "tasks": [
            {
                "task_id": "t1",
                "agent": "recommendation",
                "action": "generate_recommendation",
                "status": "running",
                "depends_on": [],
                "required": True,
                "input": {"route_decision": state["route_decision"]},
                "result_ref": None,
                "error": None,
                "reason": "recommendation_requested",
                "source": "deterministic_planner",
            }
        ],
        "current_task_id": "t1",
        "completed_task_ids": [],
    }
    state["last_agent_result"] = agent_result(
        "recommendation",
        "awaiting_selection",
        "technician_recommended",
        None,
        {"recommendation": {"status": "awaiting_selection"}},
        response_type="technician_recommendation",
        facts={"recommended_technician": {"technician_name": "鐜嬪�?}},
        suggested_next_tasks=[
            {
                "agent": "booking",
                "action": "select_recommended_technician",
                "reason": "recommendation_ready_for_selection",
                "input": {"selected_recommendation": {"technician_name": "鐜嬪�?}},
                "auto_continue": False,
            }
        ],
        requires_user_input=True,
    )

    update = asyncio.run(supervisor_continue_node(state))

    assert update["execution_plan"]["status"] == "waiting_user"
    assert update["execution_plan"]["current_task_id"] == "t1"


def test_query_first_routes_via_execution_plan_only():
    state = {
        "route_decision": {"action": "query_availability"},
        "availability": {"options": [{"technician_id": 1}]},
    }

    assert route_after_agent_result(state) == "end"

    state["execution_plan"] = {
        "plan_id": "plan_contract",
        "status": "running",
        "tasks": [
            {
                "task_id": "t1",
                "agent": "availability",
                "action": "query_availability",
                "status": "running",
                "depends_on": [],
            }
        ],
        "current_task_id": "t1",
        "completed_task_ids": [],
    }
    assert route_after_agent_result(state) == "continue"
