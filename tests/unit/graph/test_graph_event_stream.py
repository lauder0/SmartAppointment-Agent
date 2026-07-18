from api.graph_chat_handler import (
    _persisted_plan_signature,
    _plan_event_if_changed,
    _result_event_for_update,
)
from agents.supervisor.planning.planner import _dedupe_actions


def test_historical_entry_result_is_not_published():
    result = {
        "agent_name": "recommendation",
        "status": "completed",
        "result_type": "technician_recommended",
    }

    assert _result_event_for_update("supervisor_entry", {"last_agent_result": result}) is None


def test_internal_specialist_result_is_not_published():
    result = {
        "agent_name": "availability",
        "status": "completed",
        "result_type": "availability_result",
        "visibility": "internal",
    }

    assert _result_event_for_update("availability_subgraph", {"last_agent_result": result}) is None


def test_plan_is_announced_only_once_per_plan_id():
    state = {
        "execution_plan": {
            "plan_id": "plan_1",
            "status": "running",
            "current_task_id": "t1",
            "tasks": [{"task_id": "t1", "agent": "availability", "action": "query_availability", "status": "running"}],
        }
    }

    event, signature = _plan_event_if_changed(state, None)
    assert event is not None

    state["execution_plan"]["tasks"][0]["status"] = "completed"
    repeated, _ = _plan_event_if_changed(state, signature)
    assert repeated is None


def test_plan_actions_are_idempotent_even_when_duplicates_are_not_adjacent():
    actions = ["query_availability", "generate_recommendation", "query_availability"]

    assert _dedupe_actions(actions) == ["query_availability", "generate_recommendation"]


def test_persisted_plan_is_not_reannounced_at_turn_entry():
    state = {"execution_plan": {"plan_id": "old_plan"}}

    assert _persisted_plan_signature(state) == ("old_plan",)
