from __future__ import annotations

import pytest

from agents.understander.rules import (
    classify_rule_matches,
    classify_rule_intent,
    is_appointment_policy_question,
    is_business_hours_question,
    is_contact_question,
    is_knowledge_question,
    is_location_question,
    is_price_question,
    is_service_catalog_question,
    is_service_recommendation_request,
    is_technician_info_question,
)
from agents.understander.contextual_resolver import resolve_contextual_signals
from agents.understander.llm_planner import should_call_llm
from agents.understander.decision_builder import build_understanding_result
from agents.understander.normalizer import normalize_user_input
from agents.understander.rule_signals import collect_rule_signals


@pytest.mark.parametrize(
    ("text", "matcher"),
    [
        ("你们有什么项目", is_service_catalog_question),
        ("有哪些推拿项目", is_service_catalog_question),
        ("你们的位置在哪", is_location_question),
        ("门店在哪儿", is_location_question),
        ("怎么过去", is_location_question),
        ("你们怎么收费", is_price_question),
        ("全身推拿多少钱", is_price_question),
        ("今天营业到几点", is_business_hours_question),
        ("你们几点开门", is_business_hours_question),
        ("客服电话是多少", is_contact_question),
        ("有会员优惠吗", is_knowledge_question),
        ("怎么预约", is_appointment_policy_question),
        ("有哪些技师", is_technician_info_question),
        ("全身推拿和肩颈推拿有什么区别", is_knowledge_question),
    ],
)
def test_clear_consultation_questions_are_rule_knowledge(text, matcher):
    assert matcher(text) is True
    assert is_knowledge_question(text) is True
    assert classify_rule_intent(text) == "knowledge_query"


def test_location_synonym_routes_to_knowledge_without_llm():
    text = "你们的位置在哪"
    normalized = normalize_user_input(text)
    signals = collect_rule_signals(text, normalized, {})
    context_signals = resolve_contextual_signals(signals, {})

    assert any(signal["name"] == "knowledge_query" for signal in context_signals)
    assert any(signal["intent_group"] == "static_consultation" and signal["subtype"] == "location" for signal in context_signals)
    assert should_call_llm(context_signals, text) is False


def test_availability_question_is_not_misclassified_as_technician_intro():
    text = "明天下午有哪些技师可约"
    normalized = normalize_user_input(text)
    signals = collect_rule_signals(text, normalized, {})

    assert is_technician_info_question(text) is False
    assert any(signal["name"] == "availability_query" for signal in signals)
    assert classify_rule_intent(text) == "availability_query"


def test_rule_matches_keep_multiple_consultation_subtypes():
    matches = classify_rule_matches("你们地址在哪，电话是多少")

    subtypes = {match.subtype for match in matches}
    assert {"location", "contact"}.issubset(subtypes)


def test_booking_request_has_booking_group_and_slots():
    text = "我要预约明天下午五点全身推拿"
    normalized = normalize_user_input(text)
    signals = collect_rule_signals(text, normalized, {})

    assert any(
        signal["name"] == "appointment_request"
        and signal["intent_group"] == "booking"
        and signal["subtype"] == "booking_start"
        for signal in signals
    )
    assert any(signal["slots"].get("service_type") == "全身推拿" for signal in signals)


def test_technician_recommendation_is_not_service_recommendation():
    text = "我想做全身推拿，你有推荐的技师吗"
    normalized = normalize_user_input(text)
    signals = collect_rule_signals(text, normalized, {})

    assert any(
        signal["name"] == "recommendation_request"
        and signal["intent_group"] == "recommendation"
        and signal["subtype"] == "technician_recommendation"
        for signal in signals
    )
    assert not any(signal["name"] == "service_recommendation_request" for signal in signals)


def test_service_recommendation_routes_to_consultation():
    text = "肩颈酸适合做什么项目"
    normalized = normalize_user_input(text)
    signals = collect_rule_signals(text, normalized, {})
    result = build_understanding_result(text, normalized["normalized_text"], signals, {})

    assert is_service_recommendation_request(text) is True
    assert result["next_action"] == "recommend_service"
    assert result["task_type"] == "service_recommendation"
    assert result["route_reason"] == "rule_service_recommendation"


def test_confirmation_signal_requires_context():
    text = "确认"
    normalized = normalize_user_input(text)
    signals = collect_rule_signals(text, normalized, {})

    assert any(
        signal["name"] == "positive_confirmation"
        and signal["intent_group"] == "context_operation"
        and signal["requires_context"] is True
        for signal in signals
    )


def test_named_candidate_selection_resolves_recommendation_context():
    text = "我选王强吧"
    normalized = normalize_user_input(text)
    signals = collect_rule_signals(text, normalized, {})
    resolved = resolve_contextual_signals(
        signals,
        {
            "recommendation": {
                "status": "awaiting_selection",
                "selected_recommendation": {"technician_id": 2, "technician_name": "李娜"},
                "candidate_recommendations": [
                    {"technician_id": 2, "technician_name": "李娜"},
                    {"technician_id": 1, "technician_name": "王强"},
                ],
            }
        },
    )

    accept_signal = next(signal for signal in resolved if signal["name"] == "accept_current_recommendation")
    assert accept_signal["slots"]["technician_name"] == "王强"
    assert should_call_llm(resolved, text) is False
