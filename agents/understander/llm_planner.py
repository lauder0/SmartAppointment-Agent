"""LLM fallback planner for low-confidence or complex turns."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Literal, Optional

from config.model_provider import create_chat_model

from .prompts import understanding_fallback_prompt
from .schemas import LLMPlan, ROUTER_ACTIONS


UnderstandingCertainty = Literal["certain", "uncertain", "none"]

CERTAIN_CONTEXT_SIGNALS = {
    "confirm_pending_booking",
    "cancel_pending_booking",
    "modify_pending_booking",
    "knowledge_interrupt_pending_booking",
    "replace_current_recommendation",
    "accept_current_recommendation",
    "recommend_from_available_options",
    "availability_to_booking_selection",
    "continue_pending_task_with_slots",
    "service_selection",
    "service_selection_after_catalog",
}

WEAK_SIGNALS = {
    "slot_update",
    "other",
}

UNRESOLVED_CONTEXT_SIGNALS = {
    "positive_confirmation",
    "negative_confirmation",
    "recommendation_selection",
    "recommendation_replacement",
    "modification_request",
    "availability_refinement",
    "booking_confirmation_context",
    "recommendation_selection_context",
}

ALLOWED_SLOT_FIELDS = {
    "service_type",
    "start_time",
    "duration_minutes",
    "gender_preference",
    "technician_name",
    "preference",
}

ALLOWED_MISSING_SLOTS = ALLOWED_SLOT_FIELDS
RISK_LEVELS = {"low", "medium", "high"}
MIN_LLM_CONFIDENCE = 0.55

DEFAULT_TASK_TYPE_BY_ACTION = {
    "answer_knowledge": "knowledge_consultation",
    "recommend_service": "service_recommendation",
    "query_availability": "availability_query",
    "start_or_continue_booking": "booking_creation",
    "modify_booking": "booking_modification",
    "confirm_booking": "booking_confirmation",
    "cancel_booking": "booking_cancellation",
    "generate_recommendation": "technician_recommendation",
    "replace_recommendation": "recommendation_replacement",
    "select_recommended_technician": "recommendation_selection",
    "ask_clarification": "fallback_clarification",
    "unsupported": "unsupported",
}

ALLOWED_TASK_TYPES_BY_ACTION = {
    "answer_knowledge": {"knowledge_consultation", "answer_knowledge"},
    "recommend_service": {"service_recommendation", "recommend_service"},
    "query_availability": {"availability_query", "query_availability"},
    "start_or_continue_booking": {"booking_creation", "booking_modification", "start_or_continue_booking"},
    "modify_booking": {"booking_modification", "modify_booking"},
    "confirm_booking": {"booking_confirmation", "confirm_booking"},
    "cancel_booking": {"booking_cancellation", "cancel_booking"},
    "generate_recommendation": {
        "technician_recommendation",
        "recommendation_before_booking",
        "generate_recommendation",
    },
    "replace_recommendation": {"recommendation_replacement", "replace_recommendation"},
    "select_recommended_technician": {"recommendation_selection", "select_recommended_technician"},
    "ask_clarification": {"fallback_clarification", "ask_clarification"},
    "unsupported": {"unsupported"},
}

CONTEXT_REQUIRED_ACTIONS = {
    "confirm_booking": ("booking", "awaiting_confirmation"),
    "cancel_booking": ("booking", "awaiting_confirmation"),
    "replace_recommendation": ("recommendation", "awaiting_selection"),
    "select_recommended_technician": ("recommendation", "awaiting_selection"),
}


def assess_understanding_certainty(signals: list[dict]) -> UnderstandingCertainty:
    """Return whether rules plus context are enough to skip LLM fallback."""
    if not signals:
        return "none"

    names = {str(signal.get("name")) for signal in signals if signal.get("name")}
    if not names:
        return "none"

    if names & CERTAIN_CONTEXT_SIGNALS:
        return "certain"

    direct_signals = names - WEAK_SIGNALS - UNRESOLVED_CONTEXT_SIGNALS
    if direct_signals:
        return "certain"

    return "uncertain"


def should_call_llm(signals: list[dict], user_text: str) -> bool:
    """Call LLM only when rules plus context are not certain enough."""
    text = (user_text or "").strip()
    if not text:
        return False

    return assess_understanding_certainty(signals) in {"uncertain", "none"}


async def llm_plan_decision(state: Dict[str, Any], user_text: str) -> Optional[LLMPlan]:
    """Ask a model for a structured plan when rules are insufficient."""
    prompt = _build_prompt(state, user_text)
    try:
        message = await create_chat_model(temperature=0).ainvoke(prompt)
    except Exception:
        return None
    parsed = _extract_json_object(str(getattr(message, "content", "")))
    if not parsed:
        return None
    return validate_llm_plan(parsed, state)


def validate_llm_plan(parsed: Dict[str, Any], state: Dict[str, Any]) -> Optional[LLMPlan]:
    """Validate and normalize the candidate plan produced by the LLM."""
    action = str(parsed.get("action") or "")
    if action not in ROUTER_ACTIONS:
        return None

    confidence = _coerce_confidence(parsed.get("confidence"))
    if not _context_allows_action(action, state):
        return _clarification_plan("llm_action_requires_missing_context", confidence)
    if confidence < MIN_LLM_CONFIDENCE and action != "unsupported":
        return _clarification_plan("llm_low_confidence", confidence)

    task_type = str(parsed.get("task_type") or "")
    if task_type not in ALLOWED_TASK_TYPES_BY_ACTION[action]:
        task_type = DEFAULT_TASK_TYPE_BY_ACTION[action]

    risk_level = str(parsed.get("risk_level") or "low").lower()
    if risk_level not in RISK_LEVELS:
        risk_level = "low"

    return {
        "action": action,
        "task_type": task_type,
        "primary_intent": str(parsed.get("primary_intent") or action),
        "secondary_intents": _string_list(parsed.get("secondary_intents")),
        "confidence": confidence,
        "slot_updates": _sanitize_slot_updates(parsed.get("slot_updates")),
        "missing_slots": _sanitize_missing_slots(parsed.get("missing_slots")),
        "risk_level": risk_level,
        "requires_confirmation": bool(parsed.get("requires_confirmation", False)),
        "reason": str(parsed.get("reason") or "llm_planner"),
        "evidence": _string_list(parsed.get("evidence")),
    }


def _build_prompt(state: Dict[str, Any], user_text: str) -> str:
    return understanding_fallback_prompt(
        user_text=user_text,
        state_summary=_state_summary(state),
        allowed_actions=ROUTER_ACTIONS,
        allowed_slot_fields=ALLOWED_SLOT_FIELDS,
    )


def _state_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "focus_context": state.get("focus_context"),
        "task_frame": state.get("task_frame"),
        "booking": {
            "status": (state.get("booking") or {}).get("status"),
            "missing_fields": (state.get("booking") or {}).get("missing_fields"),
        },
        "availability": {
            "criteria_snapshot": (state.get("availability_result") or {}).get("criteria_snapshot"),
            "available_technician_names": (state.get("availability_result") or {}).get("available_technician_names"),
        },
        "recommendation": {
            "status": (state.get("recommendation") or {}).get("status"),
            "selected_recommendation": (state.get("recommendation") or {}).get("selected_recommendation"),
        },
    }


def _coerce_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, confidence))


def _sanitize_slot_updates(value: Any) -> Dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        key: slot_value
        for key, slot_value in value.items()
        if key in ALLOWED_SLOT_FIELDS and slot_value not in (None, "", [], {})
    }


def _sanitize_missing_slots(value: Any) -> list[str]:
    return [item for item in _string_list(value) if item in ALLOWED_MISSING_SLOTS]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item not in (None, "", [], {})]


def _context_allows_action(action: str, state: Dict[str, Any]) -> bool:
    requirement = CONTEXT_REQUIRED_ACTIONS.get(action)
    if not requirement:
        return True
    container_name, required_status = requirement
    container = state.get(container_name) or {}
    return container.get("status") == required_status


def _clarification_plan(reason: str, confidence: float) -> LLMPlan:
    return {
        "action": "ask_clarification",
        "task_type": "fallback_clarification",
        "primary_intent": "ask_clarification",
        "secondary_intents": [],
        "confidence": max(0.0, min(confidence, MIN_LLM_CONFIDENCE)),
        "slot_updates": {},
        "missing_slots": [],
        "risk_level": "low",
        "requires_confirmation": False,
        "reason": reason,
        "evidence": [],
    }


def _extract_json_object(text: str) -> Optional[Dict[str, Any]]:
    content = (text or "").strip()
    if not content:
        return None
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", content, flags=re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None
