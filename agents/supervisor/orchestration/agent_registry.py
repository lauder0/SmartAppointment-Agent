"""Allowed Supervisor actions and their specialist-agent targets."""

from __future__ import annotations


ACTION_TO_AGENT = {
    "answer_knowledge": "consultation",
    "query_availability": "availability",
    "recommend_service": "recommendation",
    "generate_recommendation": "recommendation",
    "answer_recommendation": "recommendation",
    "replace_recommendation": "recommendation",
    "start_or_continue_booking": "booking",
    "modify_booking": "booking",
    "confirm_booking": "booking",
    "cancel_booking": "booking",
    "select_recommended_technician": "booking",
    "ask_clarification": "fallback",
    "unsupported": "fallback",
}

TASK_BY_ACTION = {
    "answer_knowledge": "answer_knowledge",
    "query_availability": "query_availability",
    "recommend_service": "recommendation",
    "generate_recommendation": "recommendation",
    "answer_recommendation": "recommendation",
    "replace_recommendation": "recommendation",
    "start_or_continue_booking": "start_or_continue_booking",
    "modify_booking": "modify_booking",
    "confirm_booking": "booking_confirmation",
    "cancel_booking": "booking_confirmation",
    "select_recommended_technician": "booking_confirmation",
}

BOOKING_WRITE_ACTIONS = {"confirm_booking", "cancel_booking"}


def agent_for_action(action: str | None) -> str:
    return ACTION_TO_AGENT.get(action or "", "fallback")


def task_for_action(action: str | None) -> str | None:
    return TASK_BY_ACTION.get(action or "")
