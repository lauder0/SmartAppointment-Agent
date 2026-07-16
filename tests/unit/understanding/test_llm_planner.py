from __future__ import annotations

from agents.understander.llm_planner import (
    assess_understanding_certainty,
    should_call_llm,
    validate_llm_plan,
)


def test_should_call_llm_when_rules_have_no_signal():
    assert assess_understanding_certainty([]) == "none"
    assert should_call_llm([], "你们有什么项目") is True


def test_should_not_call_llm_when_strong_rule_signal_exists():
    signals = [{"name": "knowledge_query"}]

    assert assess_understanding_certainty(signals) == "certain"
    assert should_call_llm(signals, "你们有哪些服务项目") is False


def test_should_not_call_llm_for_empty_text():
    assert should_call_llm([], "  ") is False


def test_should_call_llm_for_only_weak_other_signal():
    signals = [{"name": "other"}]

    assert assess_understanding_certainty(signals) == "uncertain"
    assert should_call_llm(signals, "那个合适的") is True


def test_should_call_llm_for_unresolved_context_signal():
    signals = [{"name": "positive_confirmation", "requires_context": True}]

    assert assess_understanding_certainty(signals) == "uncertain"
    assert should_call_llm(signals, "确认") is True


def test_should_not_call_llm_for_resolved_context_signal():
    signals = [
        {"name": "positive_confirmation", "requires_context": True},
        {"name": "confirm_pending_booking", "source": "context"},
    ]

    assert assess_understanding_certainty(signals) == "certain"
    assert should_call_llm(signals, "确认") is False


def test_should_not_call_llm_for_service_selection_after_catalog():
    signals = [
        {
            "name": "service_selection_after_catalog",
            "intent_group": "context_operation",
            "requires_context": True,
        }
    ]

    assert assess_understanding_certainty(signals) == "certain"
    assert should_call_llm(signals, "我想做全身推拿") is False


def test_validate_llm_plan_rejects_unknown_action():
    assert validate_llm_plan({"action": "create_database_backup"}, {}) is None


def test_validate_llm_plan_sanitizes_slots_and_task_type():
    plan = validate_llm_plan(
        {
            "action": "query_availability",
            "task_type": "booking_creation",
            "primary_intent": "query_availability",
            "secondary_intents": ["availability_query", None],
            "confidence": 1.3,
            "slot_updates": {
                "service_type": "全身推拿",
                "duration_minutes": 60,
                "admin": True,
                "technician_id": "t001",
            },
            "missing_slots": ["start_time", "admin"],
            "risk_level": "strange",
            "evidence": ["有哪些技师"],
        },
        {},
    )

    assert plan is not None
    assert plan["task_type"] == "availability_query"
    assert plan["confidence"] == 1.0
    assert plan["slot_updates"] == {"service_type": "全身推拿", "duration_minutes": 60}
    assert plan["missing_slots"] == ["start_time"]
    assert plan["risk_level"] == "low"
    assert plan["secondary_intents"] == ["availability_query"]


def test_validate_llm_plan_requires_context_for_confirmation():
    plan = validate_llm_plan(
        {
            "action": "confirm_booking",
            "task_type": "booking_confirmation",
            "confidence": 0.9,
            "reason": "用户说确认",
        },
        {"booking": {"status": "idle"}},
    )

    assert plan is not None
    assert plan["action"] == "ask_clarification"
    assert plan["reason"] == "llm_action_requires_missing_context"


def test_validate_llm_plan_allows_contextual_confirmation():
    plan = validate_llm_plan(
        {
            "action": "confirm_booking",
            "task_type": "booking_confirmation",
            "primary_intent": "confirm_booking",
            "confidence": 0.9,
            "reason": "用户确认待确认预约",
        },
        {"booking": {"status": "awaiting_confirmation"}},
    )

    assert plan is not None
    assert plan["action"] == "confirm_booking"
    assert plan["task_type"] == "booking_confirmation"


def test_validate_llm_plan_low_confidence_becomes_clarification():
    plan = validate_llm_plan(
        {
            "action": "query_availability",
            "task_type": "availability_query",
            "confidence": 0.3,
        },
        {},
    )

    assert plan is not None
    assert plan["action"] == "ask_clarification"
    assert plan["reason"] == "llm_low_confidence"
