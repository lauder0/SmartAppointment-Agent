"""Normalize rule, context, and LLM outputs into one understanding result."""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Set

from agents.shared.slot_utils import default_duration_for_service

from .schemas import IntentSignal, LLMPlan, TaskFrame, UnderstandingResult, compact_slots, default_task_frame, now_iso


BOOKING_REQUIRED_SLOTS = ["service_type", "start_time", "duration_minutes"]
RECOMMENDATION_REQUIRED_SLOTS = ["service_type", "start_time", "duration_minutes"]


def build_understanding_result(
    raw_text: str,
    normalized_text: str,
    signals: List[IntentSignal],
    state: Dict[str, Any],
    llm_result: LLMPlan | None = None,
) -> UnderstandingResult:
    """Build one normalized decision input from rule/context/LLM outputs."""
    names = _signal_names(signals)
    slots = compact_slots(_merged_signal_slots(signals))
    existing_task = dict(state.get("task_frame") or default_task_frame())
    booking = state.get("booking") or {}
    availability = state.get("availability_result") or {}

    primary_intent = "unsupported"
    secondary_intents: List[str] = []
    task_type = "unsupported"
    next_action = "unsupported"
    route_reason = "default_unsupported"
    confidence = _max_confidence(signals, 0.7)
    clarification_question = None
    risk_level = "low"
    safety_flags: List[str] = []
    requires_confirmation = False
    execution_policy = "single_action"

    if "unsafe_or_unsupported" in names or _has_unsafe_signal(raw_text):
        primary_intent = "unsafe_or_unsupported"
        task_type = "unsupported"
        next_action = "unsupported"
        route_reason = "safety_or_permission_boundary"
        safety_flags = ["permission_or_privacy_risk"]
        risk_level = "high"
    elif "confirm_pending_booking" in names:
        primary_intent = "confirm_booking"
        task_type = "booking_confirmation"
        next_action = "confirm_booking"
        route_reason = "booking_awaiting_confirmation"
        requires_confirmation = True
    elif "cancel_pending_booking" in names:
        primary_intent = "cancel_booking"
        task_type = "booking_cancellation"
        next_action = "cancel_booking"
        route_reason = "cancel_pending_booking"
    elif "modify_pending_booking" in names:
        primary_intent = "modify_booking"
        task_type = "booking_modification"
        next_action = "start_or_continue_booking"
        route_reason = "modify_pending_booking"
    elif "knowledge_interrupt_pending_booking" in names:
        primary_intent = "answer_knowledge"
        task_type = "knowledge_consultation"
        next_action = "answer_knowledge"
        route_reason = "knowledge_interrupt_pending_booking"
        secondary_intents = ["suspended_booking_confirmation"]
    elif _should_continue_booking_draft(booking, names, raw_text):
        primary_intent = "continue_booking"
        task_type = "booking_creation"
        next_action = "start_or_continue_booking"
        route_reason = "continue_booking_draft"
    elif "replace_current_recommendation" in names:
        primary_intent = "replace_recommendation"
        task_type = "recommendation_replacement"
        next_action = "replace_recommendation"
        route_reason = "replace_current_recommendation"
    elif "accept_current_recommendation" in names:
        primary_intent = "select_recommended_technician"
        task_type = "recommendation_selection"
        next_action = "select_recommended_technician"
        route_reason = "accept_current_recommendation"
    elif _is_query_first_knowledge_then_work(names, slots, existing_task, raw_text):
        primary_intent = "answer_knowledge"
        secondary_intents = _query_first_secondary_intents(names, slots, existing_task, raw_text)
        task_type = _query_first_task_type(names, slots, existing_task, raw_text)
        next_action = "answer_knowledge"
        route_reason = "query_first_knowledge_plan"
        execution_policy = "query_first_plan"
    elif _is_query_first_availability_then_work(names, slots, existing_task, raw_text):
        if _has_recommendation_intent(names, slots, existing_task):
            primary_intent = "recommend_technician"
            task_type = "recommendation_before_booking"
        else:
            primary_intent = "start_booking"
            task_type = "booking_creation"
        secondary_intents = _query_first_secondary_intents(names, slots, existing_task, raw_text)
        next_action = "query_availability"
        route_reason = "query_first_availability_plan"
        execution_policy = "query_first_plan"
    elif _is_recommendation_before_booking(names, slots, existing_task):
        primary_intent = "recommend_technician"
        secondary_intents = _secondary(names, ["service_selection", "service_selection_after_catalog", "slot_update"])
        task_type = "recommendation_before_booking"
        next_action = "query_availability"
        route_reason = "prepare_candidates_for_recommendation"
    elif "recommend_from_available_options" in names or (
        "recommendation_request" in names and (availability.get("criteria_snapshot") or availability.get("options"))
    ):
        primary_intent = "recommend_technician"
        task_type = "technician_recommendation"
        next_action = "generate_recommendation"
        route_reason = "recommend_from_available_options"
    elif "continue_availability_query" in names:
        primary_intent = "query_availability"
        task_type = "availability_query"
        next_action = "query_availability"
        route_reason = "refine_availability_context"
    elif "recommendation_request" in names:
        primary_intent = "recommend_technician"
        task_type = "recommendation_before_booking"
        next_action = "query_availability"
        route_reason = "prepare_candidates_for_recommendation"
    elif "availability_to_booking_selection" in names:
        primary_intent = "start_booking"
        task_type = "booking_creation"
        next_action = "start_or_continue_booking"
        route_reason = (
            "service_selection_after_availability"
            if ("service_selection" in names or "service_selection_after_catalog" in names)
            else "availability_to_booking_selection"
        )
    elif "knowledge_query" in names:
        primary_intent = "answer_knowledge"
        task_type = "knowledge_consultation"
        next_action = "answer_knowledge"
        route_reason = "rule_knowledge_query"
    elif "service_recommendation_request" in names:
        primary_intent = "recommend_service"
        task_type = "service_recommendation"
        next_action = "recommend_service"
        route_reason = "rule_service_recommendation"
    elif "appointment_request" in names or "formal_booking_request" in names:
        primary_intent = "start_booking"
        task_type = "booking_creation"
        next_action = "start_or_continue_booking"
        route_reason = "rule_booking_request"
    elif "availability_query" in names or _should_use_availability_refinement(names, availability, raw_text):
        primary_intent = "query_availability"
        task_type = "availability_query"
        next_action = "query_availability"
        route_reason = "rule_availability_query" if "availability_query" in names else "refine_availability_context"
    elif "service_selection_after_catalog" in names or "service_selection" in names:
        primary_intent = "start_booking"
        task_type = "booking_creation"
        next_action = "start_or_continue_booking"
        route_reason = "service_catalog_selection"
    elif "greeting" in names or "courtesy" in names:
        primary_intent = "smalltalk"
        task_type = "fallback_smalltalk"
        next_action = "unsupported"
        route_reason = "rule_greeting" if "greeting" in names else "rule_courtesy"
    elif llm_result and llm_result.get("action"):
        next_action = str(llm_result["action"])
        route_reason = str(llm_result.get("reason") or "llm_planner")
        task_type = str(llm_result.get("task_type") or next_action)
        primary_intent = str(llm_result.get("primary_intent") or next_action)
        secondary_intents = list(llm_result.get("secondary_intents") or [])
        slots.update(compact_slots(llm_result.get("slot_updates") or {}))
        confidence = float(llm_result.get("confidence") or confidence)
    elif "positive_confirmation" in names or "negative_confirmation" in names:
        primary_intent = "ambiguous_confirmation"
        task_type = "fallback_clarification"
        next_action = "ask_clarification"
        route_reason = "confirmation_without_active_task"
        clarification_question = "请问您是想确认哪一项操作？如果要预约，请告诉我时间、项目和技师偏好。"

    if task_type in {"booking_creation", "booking_modification", "recommendation_before_booking"}:
        slots = _apply_slot_defaults(slots, state, existing_task)

    missing_slots = _missing_slots(task_type, slots, existing_task, state)
    invalidates = _invalidated_state(slots, state)
    conflicts = _detect_conflicts(slots, state)
    subtasks = _build_subtasks(task_type, slots, missing_slots)

    if conflicts and task_type not in {"booking_modification", "recommendation_before_booking"}:
        next_action = "ask_clarification"
        route_reason = "slot_conflict_requires_clarification"
        clarification_question = "我发现您这次提供的信息和前面的条件有冲突，请确认要以哪个时间、项目或技师偏好为准。"
        confidence = min(confidence, 0.65)

    task_frame = _build_task_frame(
        existing_task=existing_task,
        task_type=task_type,
        primary_intent=primary_intent,
        secondary_intents=secondary_intents,
        slots=slots,
        missing_slots=missing_slots,
        subtasks=subtasks,
        confidence=confidence,
        source="decision_builder",
        risk_level=risk_level,
        safety_flags=safety_flags,
        invalidates=invalidates,
        conflicts=conflicts,
        next_action=next_action,
        execution_policy=execution_policy,
    )

    return {
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "signals": signals,
        "primary_intent": primary_intent,
        "secondary_intents": secondary_intents,
        "task_type": task_type,
        "confidence": confidence,
        "slot_updates": slots,
        "missing_slots": missing_slots,
        "conflicts": conflicts,
        "invalidates": invalidates,
        "safety_flags": safety_flags,
        "risk_level": risk_level,
        "subtasks": subtasks,
        "next_action": next_action,
        "execution_policy": execution_policy,
        "route_reason": route_reason,
        "requires_confirmation": requires_confirmation,
        "clarification_question": clarification_question,
        "task_frame": task_frame,
        "trace": {
            "signal_names": sorted(names),
            "policy": execution_policy if execution_policy != "single_action" else _selected_policy(task_type, names),
            "source": "rule+context+llm+decision_builder",
        },
    }


def _is_recommendation_before_booking(names: Set[str], slots: Dict[str, Any], existing_task: Dict[str, Any]) -> bool:
    if "recommendation_request" in names and (
        "service_selection" in names
        or "service_selection_after_catalog" in names
        or slots.get("service_type")
    ):
        return True
    return (
        existing_task.get("task_type") == "recommendation_before_booking"
        and "continue_pending_task_with_slots" in names
    )


def _should_continue_booking_draft(booking: Dict[str, Any], names: Set[str], raw_text: str) -> bool:
    if booking.get("status") != "drafting" or "slot_update" not in names:
        return False
    if "knowledge_query" in names or "recommendation_request" in names:
        return False
    if "availability_query" in names and _has_explicit_availability_question(raw_text):
        return False
    return True


def _should_use_availability_refinement(names: Set[str], availability: Dict[str, Any], raw_text: str) -> bool:
    if "availability_refinement" not in names:
        return False
    if availability.get("criteria_snapshot") or availability.get("options"):
        return True
    return _has_explicit_availability_question(raw_text)


def _is_query_first_knowledge_then_work(
    names: Set[str],
    slots: Dict[str, Any],
    existing_task: Dict[str, Any],
    raw_text: str,
) -> bool:
    if "knowledge_query" not in names:
        return False
    return (
        _has_booking_intent(names)
        or _has_recommendation_intent(names, slots, existing_task)
        or _has_availability_query_intent(names, raw_text)
    )


def _is_query_first_availability_then_work(
    names: Set[str],
    slots: Dict[str, Any],
    existing_task: Dict[str, Any],
    raw_text: str,
) -> bool:
    if not _has_availability_query_intent(names, raw_text):
        return False
    return _has_booking_intent(names) or _has_recommendation_intent(names, slots, existing_task)


def _has_availability_query_intent(names: Set[str], raw_text: str) -> bool:
    if "availability_query" in names:
        return True
    if "availability_refinement" not in names:
        return False
    return _has_explicit_availability_question(raw_text)


def _has_explicit_availability_question(raw_text: str) -> bool:
    text = raw_text.strip()
    if not text:
        return False
    question_markers = ("?", "？", "吗", "么", "嘛", "呢")
    availability_terms = (
        "有哪些技师",
        "哪些技师",
        "哪位技师",
        "哪个技师",
        "哪个师傅",
        "哪位师傅",
        "谁可以",
        "谁能",
        "有谁",
        "有空",
        "空闲",
        "空位",
        "可约",
        "可以约",
        "能约",
        "还能约",
        "排班",
        "档期",
        "有没有",
        "还有没有",
    )
    return any(term in text for term in availability_terms) and (
        any(marker in text for marker in question_markers)
        or any(term in text for term in ("有哪些", "哪些", "谁可以", "谁能", "有空", "可约", "可以约", "能约", "排班", "档期"))
    )


def _has_booking_intent(names: Set[str]) -> bool:
    return bool({"appointment_request", "formal_booking_request", "availability_to_booking_selection"} & names)


def _has_recommendation_intent(names: Set[str], slots: Dict[str, Any], existing_task: Dict[str, Any]) -> bool:
    return "recommendation_request" in names or _is_recommendation_before_booking(names, slots, existing_task)


def _query_first_task_type(
    names: Set[str],
    slots: Dict[str, Any],
    existing_task: Dict[str, Any],
    raw_text: str,
) -> str:
    if _has_recommendation_intent(names, slots, existing_task):
        return "recommendation_before_booking"
    if _has_booking_intent(names):
        return "booking_creation"
    if _has_availability_query_intent(names, raw_text):
        return "availability_query"
    return "knowledge_consultation"


def _query_first_secondary_intents(
    names: Set[str],
    slots: Dict[str, Any],
    existing_task: Dict[str, Any],
    raw_text: str,
) -> List[str]:
    secondary: List[str] = []
    if "knowledge_query" in names:
        secondary.append("knowledge_query")
    if _has_availability_query_intent(names, raw_text):
        secondary.append("availability_query")
    if _has_recommendation_intent(names, slots, existing_task):
        secondary.append("recommend_technician")
    if _has_booking_intent(names):
        secondary.append("start_booking")
    return list(dict.fromkeys(secondary))


def _missing_slots(
    task_type: str,
    slots: Dict[str, Any],
    existing_task: Dict[str, Any],
    state: Dict[str, Any],
) -> List[str]:
    collected = dict(existing_task.get("collected_slots") or {})
    focus = state.get("focus_context") or {}
    for key in RECOMMENDATION_REQUIRED_SLOTS + ["gender_preference", "technician_name", "preference"]:
        if focus.get(key):
            collected[key] = focus[key]
    collected.update(slots)
    collected = _apply_slot_defaults(collected, state, existing_task)

    if task_type == "recommendation_before_booking":
        required = RECOMMENDATION_REQUIRED_SLOTS
    elif task_type in {"booking_creation", "booking_modification"}:
        required = BOOKING_REQUIRED_SLOTS
    else:
        return []
    return [field for field in required if not collected.get(field)]


def _apply_slot_defaults(
    slots: Dict[str, Any],
    state: Dict[str, Any],
    existing_task: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    enriched = dict(slots)
    if enriched.get("duration_minutes"):
        return compact_slots(enriched)

    focus = state.get("focus_context") or {}
    booking = state.get("booking") or {}
    booking_draft = booking.get("draft") or {}
    task_slots = (existing_task or {}).get("collected_slots") or {}
    service_type = (
        enriched.get("service_type")
        or focus.get("service_type")
        or booking_draft.get("service_type")
        or task_slots.get("service_type")
    )
    default_duration = default_duration_for_service(service_type)
    if default_duration:
        enriched["duration_minutes"] = default_duration
    return compact_slots(enriched)


def _invalidated_state(slots: Dict[str, Any], state: Dict[str, Any]) -> List[str]:
    invalidates: List[str] = []
    downstream_fields = {
        "service_type",
        "start_time",
        "duration_minutes",
        "gender_preference",
        "technician_name",
        "technician_id",
        "preference",
    }
    if not downstream_fields.intersection(slots):
        return invalidates
    if (state.get("availability_result") or {}).get("criteria_snapshot"):
        invalidates.append("availability.criteria_snapshot")
        invalidates.append("availability.options")
    if (state.get("recommendation") or {}).get("selected_recommendation"):
        invalidates.append("recommendation.selected_recommendation")
        invalidates.append("recommendation.candidate_recommendations")
    booking = state.get("booking") or {}
    if booking.get("selected_option"):
        invalidates.append("booking.selected_option")
    if booking.get("confirmation_summary"):
        invalidates.append("booking.confirmation_summary")
    return sorted(set(invalidates))


def _detect_conflicts(slots: Dict[str, Any], state: Dict[str, Any]) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    focus = state.get("focus_context") or {}
    for field in ("service_type", "start_time", "duration_minutes", "technician_name"):
        old = focus.get(field)
        new = slots.get(field)
        if old and new and str(old) != str(new):
            conflicts.append(
                {
                    "field": field,
                    "previous": old,
                    "current": new,
                    "resolution": "treat_as_modification",
                }
            )
    return conflicts


def _build_subtasks(task_type: str, slots: Dict[str, Any], missing_slots: List[str]) -> List[Dict[str, Any]]:
    if task_type == "recommendation_before_booking":
        return [
            {"name": "collect_service_type", "status": "completed" if slots.get("service_type") else "pending"},
            {"name": "collect_start_time", "status": "pending" if "start_time" in missing_slots else "completed"},
            {"name": "query_availability", "status": "blocked" if missing_slots else "pending"},
            {"name": "rank_technicians", "status": "blocked"},
            {"name": "ask_recommendation_selection", "status": "blocked"},
        ]
    if task_type in {"booking_creation", "booking_modification"}:
        return [
            {"name": "collect_booking_slots", "status": "pending" if missing_slots else "completed"},
            {"name": "match_slot", "status": "blocked" if missing_slots else "pending"},
            {"name": "ask_confirmation", "status": "blocked"},
            {"name": "guard_booking", "status": "blocked"},
            {"name": "create_transaction", "status": "blocked"},
        ]
    return []


def _build_task_frame(
    existing_task: Dict[str, Any],
    task_type: str,
    primary_intent: str,
    secondary_intents: List[str],
    slots: Dict[str, Any],
    missing_slots: List[str],
    subtasks: List[Dict[str, Any]],
    confidence: float,
    source: str,
    risk_level: str,
    safety_flags: List[str],
    invalidates: List[str],
    conflicts: List[Dict[str, Any]],
    next_action: str,
    execution_policy: str = "single_action",
) -> TaskFrame:
    if task_type in {"unsupported", "fallback_smalltalk"}:
        frame = default_task_frame()
        frame["updated_at"] = now_iso()
        return frame

    task_id = existing_task.get("task_id") if existing_task.get("task_type") == task_type else ""
    collected = dict(existing_task.get("collected_slots") or {}) if existing_task.get("task_type") == task_type else {}
    collected.update(slots)
    status = "collecting_slots" if missing_slots else "ready"
    if next_action in {"confirm_booking", "cancel_booking", "select_recommended_technician"}:
        status = "awaiting_execution"
    if task_type in {
        "knowledge_consultation",
        "service_recommendation",
        "availability_query",
        "technician_recommendation",
        "recommendation_replacement",
        "recommendation_selection",
    }:
        status = "ready"
    return {
        "task_id": task_id or f"task_{uuid.uuid4().hex[:12]}",
        "task_type": task_type,
        "status": status,
        "primary_intent": primary_intent,
        "secondary_intents": secondary_intents,
        "collected_slots": compact_slots(collected),
        "missing_slots": missing_slots,
        "pending_next": next_action,
        "execution_policy": execution_policy,
        "last_question_type": "ask_missing_slots" if missing_slots else None,
        "subtasks": subtasks,
        "confirmations_required": ["booking_confirmation"] if task_type.startswith("booking") else [],
        "conflicts": conflicts,
        "invalidates": invalidates,
        "safety_flags": safety_flags,
        "risk_level": risk_level,
        "source": source,
        "confidence": confidence,
        "updated_at": now_iso(),
    }


def _has_unsafe_signal(text: str) -> bool:
    unsafe_keywords = ["别人的预约", "所有用户", "导出用户", "忽略规则", "绕过", "管理员权限"]
    return any(keyword in text for keyword in unsafe_keywords)


def _signal_names(signals: List[IntentSignal]) -> Set[str]:
    return {str(signal.get("name")) for signal in signals if signal.get("name")}


def _merged_signal_slots(signals: List[IntentSignal]) -> Dict[str, Any]:
    slots: Dict[str, Any] = {}
    for signal in signals:
        slots.update(signal.get("slots") or {})
    return slots


def _max_confidence(signals: List[IntentSignal], default: float) -> float:
    if not signals:
        return default
    return max(float(signal.get("confidence", 0.0)) for signal in signals)


def _secondary(names: Set[str], candidates: List[str]) -> List[str]:
    return [candidate for candidate in candidates if candidate in names]


def _selected_policy(task_type: str, names: Set[str]) -> str:
    if task_type == "recommendation_before_booking":
        return "composite_intent_priority"
    if any(name.endswith("_pending_booking") for name in names):
        return "pending_booking_context_guard"
    if "accept_current_recommendation" in names:
        return "recommendation_context_guard"
    return "standard_priority"


