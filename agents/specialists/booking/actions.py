"""Booking transaction graph nodes."""

from __future__ import annotations

import re
import hashlib
from datetime import timedelta
from typing import Any, Dict

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage

from agents.specialists.booking.parser import InputParser
from agents.specialists.booking.message_builder import MessageBuilder
from agents.shared.context.rules import (
    is_negative_confirmation,
    is_positive_confirmation,
    is_technician_replacement_request,
)
from agents.shared.node_utils import (
    append_assistant_message,
    booking_draft_from_focus,
    focus_updates_from_booking_draft,
    last_user_text,
    merge_focus_context,
    reset_active_booking_update,
)
from agents.shared.response_composer import composer
from agents.shared.state import AgentState, default_booking_state, ensure_state_defaults
from config.model_provider import create_chat_model
from config.time_config import time_config
from services.appointment_service import AppointmentService
from services.availability_service import AvailabilityService
from services.preference_recall_service import PreferenceRecallService
from tools.appointment_tools import create_appointment
from tools.technician_tools import match_technician


def _duration_to_minutes(duration: str | int | None) -> int | None:
    if isinstance(duration, int):
        return duration
    if not duration or duration == "未知":
        return None
    digits = "".join(filter(str.isdigit, str(duration)))
    return int(digits) if digits else None


def _draft_missing_fields(draft: Dict[str, Any]) -> list[str]:
    missing = []
    if not draft.get("start_time"):
        missing.append("start_time")
    if not draft.get("service_type"):
        missing.append("project")
    if not draft.get("duration_minutes"):
        missing.append("duration")
    if not draft.get("technician_name") and not draft.get("technician_id") and not draft.get("gender_preference"):
        missing.append("gender")
    return missing


def _seed_draft_from_availability(state: AgentState, draft: Dict[str, Any]) -> Dict[str, Any]:
    seeded = dict(draft)
    availability_result = state.get("availability_result") or {}
    criteria = availability_result.get("criteria_snapshot") or {}
    mapping = {
        "start_time": "start_time",
        "duration_minutes": "duration_minutes",
        "gender": "gender_preference",
        "technician_name": "technician_name",
        "service_type": "service_type",
        "preference": "preference",
    }
    for source, target in mapping.items():
        if criteria.get(source) not in (None, "", "未知", []) and not seeded.get(target):
            seeded[target] = criteria[source]
    return seeded


def _build_chat_history(state: AgentState) -> InMemoryChatMessageHistory:
    history = InMemoryChatMessageHistory()
    messages = state.get("messages", [])
    for message in messages[:-1]:
        if getattr(message, "type", None) == "human":
            history.add_message(HumanMessage(content=str(message.content)))
        elif getattr(message, "type", None) == "ai":
            history.add_message(AIMessage(content=str(message.content)))
    return history


def _apply_recalled_preferences(
    draft: Dict[str, Any],
    recalled: Dict[str, Any],
    include_technician: bool = True,
) -> None:
    if not recalled:
        return
    if not draft.get("service_type") and recalled.get("preferred_service"):
        draft["service_type"] = recalled["preferred_service"]
    if not draft.get("duration_minutes") and recalled.get("preferred_duration_minutes"):
        draft["duration_minutes"] = recalled["preferred_duration_minutes"]
    if not draft.get("gender_preference") and recalled.get("preferred_gender"):
        draft["gender_preference"] = recalled["preferred_gender"]
    if not draft.get("preference") and recalled.get("preferred_style"):
        draft["preference"] = recalled["preferred_style"]
    if include_technician and not draft.get("technician_name") and recalled.get("preferred_technician_name"):
        draft["technician_name"] = recalled["preferred_technician_name"]


def _has_time_expression(text: str) -> bool:
    lowered = text.lower()
    if re.search(r"(力气|手劲|力度|用力|按|轻|重|大|小|温柔|舒服).{0,6}一点", text):
        return False
    return bool(
        re.search(r"\d{1,2}[:：]\d{2}", text)
        or re.search(r"\b\d{1,2}\s*(?:am|pm)\b", lowered)
        or re.search(r"(今天|明天|后天|\d{1,2}月\d{1,2}[日号]?)", text)
        or re.search(r"\b(today|tomorrow)\b", lowered)
        or re.search(r"(上午|早上|中午|下午|晚上)?\s*[一二两三四五六七八九十\d]{1,3}\s*点", text)
    )


def _has_duration_expression(text: str) -> bool:
    return bool(
        re.search(
            r"(\d+(?:\.\d+)?|[一二两三四五六七八九十]+)\s*(?:个)?小时|"
            r"(\d{2,3}|[一二两三四五六七八九十]{2,})\s*分钟|半小时|"
            r"\b\d+(?:\.\d+)?\s*(?:h|hr|hrs|hour|hours|min|mins|minute|minutes)\b",
            text.lower(),
        )
    )


def _merge_rule_start_time(draft: Dict[str, Any], rule_criteria: Dict[str, Any]) -> str | None:
    rule_start = rule_criteria.get("start_time")
    if not rule_start:
        return None
    if rule_criteria.get("has_explicit_date") or not draft.get("start_time"):
        return time_config.format_datetime(rule_start)

    existing_start = time_config.parse_datetime(str(draft.get("start_time")))
    if not existing_start:
        return time_config.format_datetime(rule_start)
    merged = existing_start.replace(
        hour=rule_start.hour,
        minute=rule_start.minute,
        second=0,
        microsecond=0,
    )
    return time_config.format_datetime(merged)


def _normalize_selected_option(raw: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not raw:
        return None
    tech_id = raw.get("id") or raw.get("technician_id")
    name = raw.get("name") or raw.get("technician_name")
    return {
        "technician_id": tech_id,
        "technician_name": name,
        "raw": raw,
    }


def _selected_technician_id(booking: Dict[str, Any]) -> Any:
    selected = booking.get("selected_option") or {}
    return selected.get("technician_id") or (booking.get("draft") or {}).get("technician_id")


def _selected_technician_name(booking: Dict[str, Any]) -> str:
    selected = booking.get("selected_option") or {}
    return selected.get("technician_name") or (booking.get("draft") or {}).get("technician_name") or "系统推荐技师"


def _booking_idempotency_key(state: AgentState, booking: Dict[str, Any]) -> str:
    draft = booking.get("draft") or {}
    raw = "|".join(
        [
            str(state.get("session_id") or "default_session"),
            str(_selected_technician_id(booking) or ""),
            str(draft.get("service_type") or ""),
            str(draft.get("start_time") or ""),
            str(draft.get("duration_minutes") or ""),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def booking_parse_node(state: AgentState) -> AgentState:
    """Parse user input and merge it into the active booking draft."""
    state = ensure_state_defaults(state)
    user_input = last_user_text(state)
    booking = dict(state.get("booking") or default_booking_state())
    draft = _seed_draft_from_availability(state, booking.get("draft") or {})
    user_id = state.get("user_id") or "default_user"
    replace_technician = is_technician_replacement_request(user_input)

    if replace_technician:
        excluded_ids = list(booking.get("excluded_technician_ids") or [])
        current_technician_id = _selected_technician_id(booking)
        if current_technician_id and current_technician_id not in excluded_ids:
            excluded_ids.append(current_technician_id)
        booking["excluded_technician_ids"] = excluded_ids
        booking["selected_option"] = None
        booking["match_result"] = None
        booking["match_type"] = None

    service = AvailabilityService()
    rule_criteria = service.parse_query_criteria(user_input)
    rule_service_type = service.parse_service_type(user_input)
    rule_preference = service.parse_preference(user_input)
    explicit_technician_name = False

    parser = InputParser(create_chat_model(temperature=0))
    ai_content = ""
    for token in parser.parse_stream(user_input, _build_chat_history(state)):
        ai_content += token
    parsed = parser.parse_data(ai_content)

    if parsed.get("start_time") and parsed["start_time"] != "未知" and _has_time_expression(user_input):
        draft["start_time"] = parsed["start_time"]
    if rule_criteria.get("start_time") and _has_time_expression(user_input):
        draft["start_time"] = _merge_rule_start_time(draft, rule_criteria)
    if parsed.get("duration") and parsed["duration"] != "未知" and (
        draft.get("duration_minutes") or _has_duration_expression(user_input)
    ):
        draft["duration_minutes"] = _duration_to_minutes(parsed["duration"])
    if rule_criteria.get("duration_minutes") is not None:
        draft["duration_minutes"] = rule_criteria["duration_minutes"]
    if parsed.get("project") and parsed["project"] != "未知":
        draft["service_type"] = parsed["project"]
    if rule_service_type:
        draft["service_type"] = rule_service_type
    if parsed.get("gender") and parsed["gender"] != "未知":
        draft["gender_preference"] = parsed["gender"]
    if rule_criteria.get("gender"):
        draft["gender_preference"] = rule_criteria["gender"]
    if parsed.get("preference") and parsed["preference"] != "未知":
        draft["preference"] = parsed["preference"]
    if rule_preference:
        draft["preference"] = rule_preference
    if parsed.get("technician_name") and parsed["technician_name"] != "未知":
        draft["technician_name"] = parsed["technician_name"]
        explicit_technician_name = True
    if rule_criteria.get("technician_name"):
        draft["technician_name"] = rule_criteria["technician_name"]
        explicit_technician_name = True

    if replace_technician and not explicit_technician_name:
        draft.pop("technician_name", None)
        draft.pop("technician_id", None)

    recalled_preferences = PreferenceRecallService().recall(user_id)
    _apply_recalled_preferences(
        draft,
        recalled_preferences,
        include_technician=not replace_technician,
    )

    missing = _draft_missing_fields(draft)
    focus_context = merge_focus_context(
        state.get("focus_context"),
        focus_updates_from_booking_draft(draft),
    )
    booking.update(
        {
            "draft": draft,
            "missing_fields": missing,
            "selected_option": None if missing or replace_technician else booking.get("selected_option"),
            "guard_result": None,
            "status": "drafting" if missing else "draft_ready",
        }
    )
    return {
        "focus_context": focus_context,
        "booking": booking,
        "tool_results": {
            **(state.get("tool_results") or {}),
            "booking_parse": parsed,
            "preference_recall": recalled_preferences,
            "replace_technician": replace_technician,
        },
    }


async def booking_missing_node(state: AgentState) -> AgentState:
    """Ask for missing booking fields."""
    state = ensure_state_defaults(state)
    booking = dict(state.get("booking") or default_booking_state())
    missing = booking.get("missing_fields") or _draft_missing_fields(booking.get("draft") or {})
    booking["missing_fields"] = missing
    booking["status"] = "drafting"
    reply = composer.reply(
        "booking_missing_slots",
        {
            "body": MessageBuilder().create_missing_info_questions(missing),
            "agent_label": "预约机器人",
        },
    )
    return append_assistant_message(
        {
            "booking": booking,
            "final_response": reply,
        },
        reply,
    )


async def booking_match_node(state: AgentState) -> AgentState:
    """Match a technician for a complete booking draft."""
    state = ensure_state_defaults(state)
    booking = dict(state.get("booking") or default_booking_state())
    draft = booking.get("draft") or {}
    result = match_technician.invoke(
        {
            "start_time": draft["start_time"],
            "duration_minutes": draft["duration_minutes"],
            "gender_preference": draft.get("gender_preference"),
            "preference": draft.get("preference"),
            "technician_name": draft.get("technician_name"),
            "excluded_technician_ids": booking.get("excluded_technician_ids") or [],
            "user_id": state.get("user_id") or "default_user",
        }
    )

    if result.get("success"):
        data = result.get("data", {})
        booking["status"] = "matched"
        booking["match_type"] = data.get("match_type")
        booking["match_result"] = data
        if data.get("match_type") == "recommendation":
            booking["selected_option"] = _normalize_selected_option(data.get("recommended_technician"))
            booking["original_option"] = _normalize_selected_option(data.get("original_technician"))
        else:
            booking["selected_option"] = _normalize_selected_option(data.get("technician"))
        booking["missing_fields"] = []
    else:
        booking["status"] = "drafting"

    return {
        "booking": booking,
        "tool_results": {
            **(state.get("tool_results") or {}),
            "match_technician": result,
        },
    }


async def booking_accept_recommendation_node(state: AgentState) -> AgentState:
    """Transfer an accepted recommendation into the booking draft."""
    state = ensure_state_defaults(state)
    booking = dict(state.get("booking") or default_booking_state())
    recommendation = dict(state.get("recommendation") or {})
    selected = recommendation.get("selected_recommendation") or {}
    criteria = (state.get("availability_result") or {}).get("criteria_snapshot") or {}

    technician_id = selected.get("technician_id")
    technician_name = selected.get("technician_name")
    if not technician_id or not technician_name:
        booking["status"] = "drafting"
        booking["missing_fields"] = ["technician_id"]
        reply = composer.reply(
            "booking_failed",
            {"body": "当前没有可接受的推荐技师，请先让我重新推荐一位。"},
        )
        return append_assistant_message(
            {
                "booking": booking,
                "final_response": reply,
            },
            reply,
        )

    draft = dict(booking.get("draft") or {})
    field_mapping = {
        "start_time": "start_time",
        "duration_minutes": "duration_minutes",
        "service_type": "service_type",
        "gender": "gender_preference",
        "preference": "preference",
    }
    for source, target in field_mapping.items():
        value = selected.get(source)
        if value in (None, "", "未知", []):
            value = criteria.get(source)
        if value not in (None, "", "未知", []):
            draft[target] = value

    draft["technician_id"] = technician_id
    draft["technician_name"] = technician_name
    booking.update(
        {
            "status": "matched",
            "draft": draft,
            "missing_fields": _draft_missing_fields(draft),
            "selected_option": {
                "technician_id": technician_id,
                "technician_name": technician_name,
                "raw": selected,
            },
            "match_type": "selected_recommendation",
            "match_result": {
                "recommended_technician": {
                    "id": technician_id,
                    "name": technician_name,
                    "gender": selected.get("gender"),
                    "strength": selected.get("strength"),
                }
            },
            "guard_result": None,
        }
    )
    recommendation["status"] = "selected"
    focus_context = merge_focus_context(
        state.get("focus_context"),
        focus_updates_from_booking_draft(draft),
    )
    return {
        "focus_context": focus_context,
        "booking": booking,
        "recommendation": recommendation,
        "tool_results": {
            **(state.get("tool_results") or {}),
            "accepted_recommendation": selected,
        },
    }


async def booking_confirmation_prompt_node(state: AgentState) -> AgentState:
    """Render the booking confirmation prompt."""
    state = ensure_state_defaults(state)
    booking = dict(state.get("booking") or default_booking_state())
    draft = booking.get("draft") or {}
    builder = MessageBuilder()

    if booking.get("match_type") == "recommendation":
        match_result = booking.get("match_result") or {}
        reply_body = builder.create_technician_recommendation_message(
            match_result.get("original_technician") or {},
            match_result.get("recommended_technician") or {},
            {
                "project": draft.get("service_type"),
                "start_time": draft.get("start_time"),
            },
        )
        reply = await composer.areply(
            "booking_recommendation",
            {
                "body": reply_body,
                "agent_label": "预约机器人",
                "original_technician": match_result.get("original_technician") or {},
                "recommended_technician": match_result.get("recommended_technician") or {},
                "service_type": draft.get("service_type"),
                "start_time": draft.get("start_time"),
            },
            {"user_input": last_user_text(state)},
        )
    else:
        start_time = draft.get("start_time")
        duration = draft.get("duration_minutes")
        start_text = start_time
        end_text = ""
        try:
            parsed_start = time_config.parse_datetime(start_time) if isinstance(start_time, str) else start_time
            start_text = time_config.format_datetime(parsed_start, "%Y年%m月%d日 %H:%M")
            end_text = time_config.format_datetime(parsed_start + timedelta(minutes=duration), "%H:%M")
        except Exception:
            end_text = ""
        time_line = f"{start_text}-{end_text}" if end_text else str(start_text)
        composed = composer.compose(
            "booking_confirmation",
            {
                "time_line": time_line,
                "service_type": draft.get("service_type"),
                "duration_minutes": duration,
                "technician_name": _selected_technician_name(booking),
            },
        )
        reply = composed.reply
        reply_body = composed.body

    booking["status"] = "awaiting_confirmation"
    booking["confirmation_summary"] = reply_body
    return append_assistant_message(
        {
            "booking": booking,
            "final_response": reply,
        },
        reply,
    )


async def booking_confirmation_node(state: AgentState) -> AgentState:
    """Handle a user's response to a pending booking confirmation."""
    state = ensure_state_defaults(state)
    booking = dict(state.get("booking") or default_booking_state())
    route_action = (state.get("route_decision") or {}).get("action")
    user_input = last_user_text(state).strip().lower()
    positive = is_positive_confirmation(user_input)
    negative = is_negative_confirmation(user_input)

    if route_action == "cancel_booking" or negative:
        update = reset_active_booking_update()
        cancelled = dict(update["booking"])
        cancelled["status"] = "cancelled"
        update["booking"] = cancelled
        reply = composer.reply("booking_cancelled")
        update["final_response"] = reply
        return append_assistant_message(update, reply)

    if positive and booking.get("status") == "awaiting_confirmation":
        booking["status"] = "confirmed"
        return {"booking": booking}

    booking["status"] = "awaiting_confirmation"
    reply = composer.reply("booking_unclear_confirmation")
    return append_assistant_message(
        {
            "booking": booking,
            "final_response": reply,
        },
        reply,
    )


async def booking_guard_node(state: AgentState) -> AgentState:
    """Validate a confirmed booking before write-side tools run."""
    state = ensure_state_defaults(state)
    booking = dict(state.get("booking") or default_booking_state())
    draft = booking.get("draft") or {}
    selected_id = _selected_technician_id(booking)
    required = {
        "service_type": draft.get("service_type"),
        "start_time": draft.get("start_time"),
        "duration_minutes": draft.get("duration_minutes"),
        "technician_id": selected_id,
    }
    missing = [key for key, value in required.items() if value in (None, "", "未知", [])]
    if booking.get("status") != "confirmed":
        missing.append("confirmation")

    if missing:
        booking["status"] = "drafting"
        booking["missing_fields"] = missing
        booking["guard_result"] = {"success": False, "reason": "missing_required_fields", "missing": missing}
        reply = composer.reply("booking_guard_missing")
        return append_assistant_message(
            {
                "booking": booking,
                "final_response": reply,
                "tool_results": {**(state.get("tool_results") or {}), "booking_guard": booking["guard_result"]},
            },
            reply,
        )

    try:
        start_dt = time_config.parse_datetime(str(required["start_time"]))
        duration_minutes = int(required["duration_minutes"])
        technician_id = int(required["technician_id"])
    except Exception:
        start_dt = None
        duration_minutes = 0
        technician_id = 0

    if not start_dt or duration_minutes <= 0 or technician_id <= 0:
        booking["status"] = "drafting"
        booking["missing_fields"] = ["start_time", "duration_minutes", "technician_id"]
        booking["guard_result"] = {"success": False, "reason": "invalid_guard_fields"}
        reply = composer.reply("booking_guard_invalid")
        return append_assistant_message(
            {
                "booking": booking,
                "final_response": reply,
                "tool_results": {**(state.get("tool_results") or {}), "booking_guard": booking["guard_result"]},
            },
            reply,
        )

    end_dt = start_dt + timedelta(minutes=duration_minutes)
    valid_time, invalid_reason = time_config.validate_booking_time(start_dt, end_dt)
    if not valid_time:
        booking["status"] = "drafting"
        booking["selected_option"] = None
        booking["missing_fields"] = ["start_time"]
        booking["guard_result"] = {"success": False, "reason": invalid_reason}
        start_hour, end_hour = time_config.get_business_hours()
        window_days = time_config.get_booking_window_days()
        reply = composer.reply(
            "booking_guard_time_invalid",
            {
                "booking_window_days": window_days,
                "business_start": start_hour,
                "business_end": end_hour,
            },
        )
        return append_assistant_message(
            {
                "booking": booking,
                "final_response": reply,
                "tool_results": {**(state.get("tool_results") or {}), "booking_guard": booking["guard_result"]},
            },
            reply,
        )

    if not AppointmentService().is_technician_available(technician_id, start_dt, end_dt):
        booking["status"] = "drafting"
        booking["selected_option"] = None
        booking["missing_fields"] = ["start_time"]
        booking["guard_result"] = {"success": False, "reason": "technician_unavailable"}
        reply = composer.reply("booking_guard_technician_unavailable")
        return append_assistant_message(
            {
                "booking": booking,
                "final_response": reply,
                "tool_results": {**(state.get("tool_results") or {}), "booking_guard": booking["guard_result"]},
            },
            reply,
        )

    booking["guard_result"] = {"success": True, "reason": "ready_to_create"}
    return {
        "booking": booking,
        "tool_results": {**(state.get("tool_results") or {}), "booking_guard": booking["guard_result"]},
    }


async def booking_create_node(state: AgentState) -> AgentState:
    """Create the appointment. This is the only booking node that writes appointment data."""
    state = ensure_state_defaults(state)
    booking = state.get("booking") or default_booking_state()
    draft = booking.get("draft") or {}
    result = create_appointment.invoke(
        {
            "user_id": state.get("user_id") or "default_user",
            "session_id": state.get("session_id") or "default_session",
            "technician_id": _selected_technician_id(booking),
            "service_name": draft.get("service_type"),
            "start_time": draft.get("start_time"),
            "duration_minutes": draft.get("duration_minutes"),
            "gender_preference": draft.get("gender_preference"),
            "preference": draft.get("preference"),
            "idempotency_key": _booking_idempotency_key(state, booking),
        }
    )
    return {
        "tool_results": {
            **(state.get("tool_results") or {}),
            "create_appointment": result,
        }
    }


async def booking_complete_node(state: AgentState) -> AgentState:
    """Finalize a successful booking and clear active transaction state."""
    state = ensure_state_defaults(state)
    booking = dict(state.get("booking") or default_booking_state())
    create_result = (state.get("tool_results") or {}).get("create_appointment") or {}
    data = create_result.get("data") or {}
    draft = booking.get("draft") or {}
    end_time = data.get("end_time", "")
    end_time_text = end_time.split(" ", 1)[1] if " " in end_time else end_time
    technician_name = _selected_technician_name(booking)
    reply = composer.reply(
        "booking_success",
        {
            "technician_name": technician_name,
            "start_time": data.get("start_time"),
            "end_time_text": end_time_text,
            "service_type": draft.get("service_type"),
            "duration_minutes": draft.get("duration_minutes"),
        },
    )
    completed = {
        "draft": draft,
        "selected_option": booking.get("selected_option"),
        "create_result": data,
    }
    update = reset_active_booking_update()
    update.update(
        {
            "last_completed_booking": completed,
            "tool_results": state.get("tool_results", {}),
            "final_response": reply,
        }
    )
    return append_assistant_message(update, reply)


async def booking_failed_node(state: AgentState) -> AgentState:
    """Handle matching, guard, or write failures."""
    state = ensure_state_defaults(state)
    booking = dict(state.get("booking") or default_booking_state())
    create_result = (state.get("tool_results") or {}).get("create_appointment") or {}
    match_result = (state.get("tool_results") or {}).get("match_technician") or {}
    guard_result = (state.get("tool_results") or {}).get("booking_guard") or {}

    booking["status"] = "drafting"
    if guard_result.get("reason") == "technician_unavailable":
        booking["missing_fields"] = ["start_time"]
        body = "抱歉，该技师在当前时段不可约。请换一个时间或技师。"
    elif create_result and not create_result.get("success"):
        body = f"抱歉，预约保存失败：{create_result.get('error') or create_result.get('message')}"
    elif match_result and not match_result.get("success"):
        name = (booking.get("draft") or {}).get("technician_name")
        if name:
            body = f"抱歉，{name}技师在您选择的时间段不可约，也暂时没有找到合适的替代技师。请换一个时间或技师。"
        else:
            body = "抱歉，该时间段没有找到合适的可约技师。请换一个时间或调整偏好。"
    else:
        body = "抱歉，当前预约流程没有完成。请重新告诉我您想预约的时间、项目和技师偏好。"

    reply = await composer.areply(
        "booking_failed",
        {
            "body": body,
            "agent_label": "预约机器人",
            "draft": booking.get("draft") or {},
            "match_result": match_result,
            "guard_result": guard_result,
            "create_result": create_result,
        },
        {"user_input": last_user_text(state)},
    )

    return append_assistant_message(
        {
            "booking": booking,
            "final_response": reply,
        },
        reply,
    )
