"""Small helpers shared by graph nodes."""

from __future__ import annotations

from typing import Any, Dict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from .state import (
    default_availability_result,
    default_booking_state,
    default_focus_context,
)


def last_user_text(state: Dict[str, Any]) -> str:
    """Return the latest user message content."""
    for message in reversed(state.get("messages", [])):
        if isinstance(message, HumanMessage) or getattr(message, "type", None) == "human":
            return str(message.content)
    return ""


def append_assistant_message(state_update: Dict[str, Any], content: str) -> Dict[str, Any]:
    """Append assistant message to a node update when a final response exists."""
    if content:
        state_update["messages"] = [AIMessage(content=content)]
    return state_update


def reset_active_booking_update() -> Dict[str, Any]:
    """Return an update that resets active booking context."""
    return {
        "booking": default_booking_state(),
        "availability_result": default_availability_result(),
        "focus_context": default_focus_context(),
    }


def message_to_history_line(message: BaseMessage) -> str:
    role = "用户" if getattr(message, "type", None) == "human" else "机器人"
    return f"{role}：{message.content}"


def merge_focus_context(current: Dict[str, Any] | None, updates: Dict[str, Any] | None) -> Dict[str, Any]:
    """Merge non-empty slot updates into the shared service-request context."""
    focus = dict(current or default_focus_context())
    if not updates:
        return focus
    for key, value in updates.items():
        if value not in (None, "", "未知", []):
            focus[key] = value
    return focus


def focus_updates_from_booking_draft(draft: Dict[str, Any] | None) -> Dict[str, Any]:
    """Map booking draft fields to focus-context fields."""
    draft = draft or {}
    return {
        "service_type": draft.get("service_type"),
        "start_time": draft.get("start_time"),
        "duration_minutes": draft.get("duration_minutes"),
        "gender_preference": draft.get("gender_preference"),
        "technician_name": draft.get("technician_name"),
        "technician_id": draft.get("technician_id"),
        "preference": draft.get("preference"),
    }


def focus_updates_from_availability_criteria(criteria: Dict[str, Any] | None) -> Dict[str, Any]:
    """Map availability criteria to focus-context fields."""
    criteria = criteria or {}
    return {
        "service_type": criteria.get("service_type"),
        "start_time": criteria.get("start_time"),
        "duration_minutes": criteria.get("duration_minutes"),
        "gender_preference": criteria.get("gender"),
        "technician_name": criteria.get("technician_name"),
        "preference": criteria.get("preference"),
    }


def booking_draft_from_focus(focus: Dict[str, Any] | None) -> Dict[str, Any]:
    """Build a booking draft from the shared focus context."""
    focus = focus or {}
    return {
        "service_type": focus.get("service_type"),
        "start_time": focus.get("start_time"),
        "duration_minutes": focus.get("duration_minutes"),
        "gender_preference": focus.get("gender_preference"),
        "technician_name": focus.get("technician_name"),
        "technician_id": focus.get("technician_id"),
        "preference": focus.get("preference"),
    }
