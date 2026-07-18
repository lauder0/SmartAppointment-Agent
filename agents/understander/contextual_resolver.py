"""Context-aware intent resolution for confirmations, pending tasks, and references."""

from __future__ import annotations

from typing import Any, Dict, List

from .schemas import IntentSignal


def resolve_contextual_signals(
    signals: List[IntentSignal],
    state: Dict[str, Any],
) -> List[IntentSignal]:
    """Add context-specific signals such as pending task slot updates."""
    resolved = list(signals)
    names = {signal.get("name") for signal in signals}
    booking = state.get("booking") or {}
    recommendation = state.get("recommendation") or {}
    task_frame = state.get("task_frame") or {}
    availability = state.get("availability_result") or {}

    if booking.get("status") == "awaiting_confirmation":
        if "positive_confirmation" in names:
            resolved.append(_signal("confirm_pending_booking", 0.99, "context"))
        elif "modification_request" in names or "slot_update" in names:
            resolved.append(_signal("modify_pending_booking", 0.94, "context"))
        elif "negative_confirmation" in names:
            resolved.append(_signal("cancel_pending_booking", 0.99, "context"))
        elif "knowledge_query" in names:
            resolved.append(_signal("knowledge_interrupt_pending_booking", 0.94, "context"))

    if recommendation.get("status") == "awaiting_selection":
        if "recommendation_replacement" in names:
            resolved.append(_signal("replace_current_recommendation", 0.98, "context"))
        elif selected_candidate := _matched_recommendation_candidate(signals, recommendation):
            resolved.append(
                _signal(
                    "accept_current_recommendation",
                    0.98,
                    "context",
                    slots={
                        "technician_id": selected_candidate.get("technician_id"),
                        "technician_name": selected_candidate.get("technician_name"),
                    },
                )
            )
        elif "recommendation_selection" in names or "positive_confirmation" in names:
            resolved.append(_signal("accept_current_recommendation", 0.98, "context"))

    if availability.get("criteria_snapshot") or availability.get("options"):
        merged_slots = _merged_signal_slots(signals)
        if "recommendation_request" in names:
            resolved.append(_signal("recommend_from_available_options", 0.95, "context"))
        elif (
            ("availability_refinement" in names or "slot_update" in names)
            and "formal_booking_request" not in names
            and "service_selection" not in names
            and "service_selection_after_catalog" not in names
        ):
            resolved.append(
                _signal(
                    "continue_availability_query",
                    0.94,
                    "context",
                    slots=merged_slots,
                )
            )
        elif (
            "formal_booking_request" in names
            or (
                ("service_selection" in names or "service_selection_after_catalog" in names)
                and not merged_slots.get("duration_minutes")
            )
        ):
            resolved.append(_signal("availability_to_booking_selection", 0.94, "context"))

    if task_frame.get("status") in {"collecting_slots", "awaiting_user"}:
        if "slot_update" in names:
            resolved.append(
                _signal(
                    "continue_pending_task_with_slots",
                    0.9,
                    "context",
                    slots=_merged_signal_slots(signals),
                )
            )
        if task_frame.get("task_type") == "recommendation_before_booking":
            resolved.append(_signal("pending_recommendation_before_booking", 0.92, "context"))

    return resolved


def _signal(name: str, confidence: float, source: str, slots: Dict[str, Any] | None = None) -> IntentSignal:
    return {
        "name": name,
        "confidence": confidence,
        "source": source,
        "matched_text": "",
        "slots": slots or {},
    }


def _merged_signal_slots(signals: List[IntentSignal]) -> Dict[str, Any]:
    slots: Dict[str, Any] = {}
    for signal in signals:
        slots.update(signal.get("slots") or {})
    return {key: value for key, value in slots.items() if value not in (None, "", [], {})}


def _matched_recommendation_candidate(
    signals: List[IntentSignal],
    recommendation: Dict[str, Any],
) -> Dict[str, Any] | None:
    slots = _merged_signal_slots(signals)
    user_text = " ".join(str(signal.get("matched_text") or "") for signal in signals)
    requested_name = slots.get("technician_name")

    candidates = []
    for item in (
        recommendation.get("selected_recommendation"),
        *(recommendation.get("candidate_recommendations") or []),
        *(recommendation.get("alternative_recommendations") or []),
    ):
        if isinstance(item, dict):
            candidates.append(item)

    for candidate in candidates:
        name = candidate.get("technician_name")
        if not name:
            continue
        if requested_name == name or name in user_text:
            return candidate
    return None
