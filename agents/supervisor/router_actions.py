"""Main conversation router for state-aware flow dispatch."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

from config.model_provider import create_chat_model
from agents.shared.context.rules import (
    classify_rule_intent,
    is_availability_refinement,
    is_courtesy,
    is_formal_booking_request,
    is_greeting,
    is_knowledge_question,
    is_modification_request,
    is_negative_confirmation,
    is_positive_confirmation,
    is_service_selection_after_catalog,
)
from agents.shared.node_utils import last_user_text
from agents.shared.state import AgentState, ensure_state_defaults
from services.availability_service import AvailabilityService


ROUTER_ACTIONS = {
    "answer_knowledge",
    "query_availability",
    "start_or_continue_booking",
    "modify_booking",
    "confirm_booking",
    "cancel_booking",
    "ask_clarification",
    "unsupported",
}


def _has_availability_context(state: AgentState) -> bool:
    availability_result = state.get("availability_result") or {}
    return bool(
        availability_result.get("criteria_snapshot")
        or availability_result.get("options")
    )


def _booking_status(state: AgentState) -> str:
    booking = state.get("booking") or {}
    if booking.get("status") and booking.get("status") != "idle":
        return str(booking["status"])
    return "idle"


def _should_handoff_service_selection_to_booking(state: AgentState, user_text: str) -> bool:
    if not is_service_selection_after_catalog(user_text):
        return False
    focus = state.get("focus_context") or {}
    if focus.get("last_offer") == "service_catalog":
        return True
    criteria = AvailabilityService().parse_query_criteria(user_text)
    return criteria.get("duration_minutes") is None


def _recent_dialogue(state: AgentState, max_messages: int = 6) -> str:
    lines = []
    for message in (state.get("messages") or [])[-max_messages:]:
        role = "用户" if getattr(message, "type", None) == "human" else "助手"
        lines.append(f"{role}: {message.content}")
    return "\n".join(lines) if lines else "无"


def _compact_state_summary(state: AgentState) -> str:
    booking = state.get("booking") or {}
    focus = state.get("focus_context") or {}
    availability_result = state.get("availability_result") or {}
    availability_names = availability_result.get("available_technician_names") or []
    summary = {
        "booking_status": booking.get("status"),
        "booking_missing_fields": booking.get("missing_fields"),
        "booking_draft": booking.get("draft"),
        "booking_selected_option": booking.get("selected_option"),
        "focus_context": focus,
        "availability_criteria": availability_result.get("criteria_snapshot"),
        "available_technician_names": availability_names[:8],
    }
    return json.dumps(summary, ensure_ascii=False, default=str)


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


def _sanitize_llm_decision(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    action = str(raw.get("action") or "").strip()
    if action not in ROUTER_ACTIONS:
        return None
    confidence = raw.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    return {
        "action": action,
        "reason": str(raw.get("reason") or "llm_router"),
        "confidence": confidence,
        "slot_updates": raw.get("slot_updates") if isinstance(raw.get("slot_updates"), dict) else {},
        "source": "llm_router",
    }


async def _llm_route_decision(state: AgentState, user_text: str) -> Optional[Dict[str, Any]]:
    prompt = f"""
你是按摩门店智能预约系统的主路由器。请根据结构化状态、最近对话和当前用户输入，判断下一步 action。

只能选择一个 action：
- answer_knowledge：咨询服务项目、价格、营业时间、地址、会员、预约规则等静态知识。
- query_availability：查询或继续筛选技师实时排班、空闲时段、可约技师。
- start_or_continue_booking：开始预约、继续补充预约信息，或从排班结果转预约。
- modify_booking：用户正在修改一个待确认预约。
- confirm_booking：用户明确确认待确认预约。注意只有当前状态已经等待确认时才可选择。
- cancel_booking：用户明确取消待确认预约或预约草稿。
- ask_clarification：用户意图不明确，需要追问。
- unsupported：与门店咨询、排班、预约无关。

结构化状态：
{_compact_state_summary(state)}

最近对话：
{_recent_dialogue(state)}

当前用户输入：
{user_text}

请只输出 JSON，不要输出解释文字：
{{
  "action": "query_availability",
  "confidence": 0.0,
  "reason": "简短说明",
  "slot_updates": {{}}
}}
"""
    try:
        message = await create_chat_model(temperature=0).ainvoke(prompt)
    except Exception:
        return None
    parsed = _extract_json_object(str(getattr(message, "content", "")))
    if not parsed:
        return None
    return _sanitize_llm_decision(parsed)


async def main_router_node(state: AgentState) -> AgentState:
    """Choose the next graph action from state and the latest user input.

    The router is intentionally conservative: side-effecting booking confirmation
    remains guarded by deterministic confirmation rules, while fuzzy cases fall
    back to a structured LLM router.
    """
    state = ensure_state_defaults(state)
    user_text = last_user_text(state)
    status = _booking_status(state)

    decision = {
        "action": "unsupported",
        "reason": "default_unsupported",
    }

    if status == "awaiting_confirmation":
        if is_knowledge_question(user_text) or is_greeting(user_text) or is_courtesy(user_text):
            if is_knowledge_question(user_text):
                decision = {"action": "answer_knowledge", "reason": "knowledge_interrupt_pending_booking"}
            else:
                decision = {"action": "unsupported", "reason": "courtesy_or_greeting_pending_booking"}
        elif is_modification_request(user_text):
            decision = {"action": "start_or_continue_booking", "reason": "modify_pending_booking"}
        elif is_negative_confirmation(user_text):
            decision = {"action": "cancel_booking", "reason": "cancel_pending_booking"}
        elif is_positive_confirmation(user_text):
            decision = {"action": "confirm_booking", "reason": "booking_awaiting_confirmation"}
        else:
            decision = {"action": "ask_clarification", "reason": "unclear_confirmation_response"}
    elif status == "drafting":
        if is_knowledge_question(user_text):
            decision = {"action": "answer_knowledge", "reason": "knowledge_interrupt_during_booking"}
        else:
            decision = {"action": "start_or_continue_booking", "reason": "continue_booking_draft"}
    elif _has_availability_context(state):
        if is_formal_booking_request(user_text):
            decision = {"action": "start_or_continue_booking", "reason": "handoff_availability_to_booking"}
        elif _should_handoff_service_selection_to_booking(state, user_text):
            decision = {"action": "start_or_continue_booking", "reason": "service_selection_after_availability"}
        elif is_availability_refinement(user_text):
            decision = {"action": "query_availability", "reason": "refine_availability_context"}
    elif (state.get("focus_context") or {}).get("last_offer") == "service_catalog" and is_service_selection_after_catalog(user_text):
        decision = {"action": "start_or_continue_booking", "reason": "service_catalog_selection"}

    if decision["action"] == "unsupported":
        rule_intent = classify_rule_intent(user_text)
        if rule_intent == "knowledge_query":
            decision = {"action": "answer_knowledge", "reason": "rule_knowledge_query"}
        elif rule_intent == "availability_query":
            decision = {"action": "query_availability", "reason": "rule_availability_query"}
        elif rule_intent == "appointment":
            decision = {"action": "start_or_continue_booking", "reason": "rule_booking_request"}
        elif rule_intent in {"greeting", "courtesy", "other"}:
            decision = {"action": "unsupported", "reason": f"rule_{rule_intent}"}

    if decision["action"] == "unsupported" and classify_rule_intent(user_text) is None:
        llm_decision = await _llm_route_decision(state, user_text)
        if llm_decision:
            decision = llm_decision

    return {
        "route_decision": decision,
        "tool_results": {
            **(state.get("tool_results") or {}),
            "main_router": decision,
        },
    }
