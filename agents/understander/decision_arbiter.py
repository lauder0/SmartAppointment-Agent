"""Decision arbiter that turns understanding results into graph route decisions."""

from __future__ import annotations

from typing import Any, Dict

from agents._shared.node_utils import last_user_text, merge_focus_context
from agents._shared.state import ensure_state_defaults

from .contextual_resolver import resolve_contextual_signals
from .llm_planner import llm_plan_decision, should_call_llm
from .normalizer import normalize_user_input
from .rule_signals import collect_rule_signals
from .decision_builder import build_understanding_result
from .schemas import RouteDecision, UnderstandingResult, compact_slots


async def understand_user_turn(state: Dict[str, Any]) -> Dict[str, Any]:
    """Run the full understanding stack and return state updates for Supervisor."""
    state = ensure_state_defaults(state)
    user_text = last_user_text(state)
    normalized = normalize_user_input(user_text)
    rule_signals = collect_rule_signals(user_text, normalized, state)
    context_signals = resolve_contextual_signals(rule_signals, state)
    llm_result = None
    if should_call_llm(context_signals, user_text):
        llm_result = await llm_plan_decision(state, user_text)

    understanding = build_understanding_result(
        raw_text=user_text,
        normalized_text=normalized.get("normalized_text", ""),
        signals=context_signals,
        state=state,
        llm_result=llm_result,
    )
    decision = build_route_decision(understanding)
    focus_context = _updated_focus_context(state, understanding)
    return {
        "route_decision": decision,
        "task_frame": understanding.get("task_frame"),
        "focus_context": focus_context,
        "tool_results": {
            **(state.get("tool_results") or {}),
            "intent_understanding": understanding,
            "main_router": decision,
        },
    }


def build_route_decision(understanding: UnderstandingResult) -> RouteDecision:
    action = understanding.get("next_action") or "unsupported"
    return {
        "action": action,
        "reason": understanding.get("route_reason") or "understanding_decision",
        "confidence": float(understanding.get("confidence", 0.0)),
        "source": "decision_arbiter",
        "task_type": understanding.get("task_type") or "",
        "primary_intent": understanding.get("primary_intent") or "",
        "secondary_intents": understanding.get("secondary_intents") or [],
        "slot_updates": understanding.get("slot_updates") or {},
        "missing_slots": understanding.get("missing_slots") or [],
        "conflicts": understanding.get("conflicts") or [],
        "invalidates": understanding.get("invalidates") or [],
        "safety_flags": understanding.get("safety_flags") or [],
        "risk_level": understanding.get("risk_level") or "low",
        "execution_policy": understanding.get("execution_policy") or "single_action",
        "clarification_question": understanding.get("clarification_question"),
        "trace": understanding.get("trace") or {},
    }


def _updated_focus_context(state: Dict[str, Any], understanding: UnderstandingResult) -> Dict[str, Any]:
    slot_updates = compact_slots(understanding.get("slot_updates") or {})
    focus_updates: Dict[str, Any] = {}
    for key in (
        "service_type",
        "start_time",
        "duration_minutes",
        "gender_preference",
        "technician_name",
        "technician_id",
        "preference",
    ):
        if key in slot_updates:
            focus_updates[key] = slot_updates[key]
    return merge_focus_context(state.get("focus_context"), focus_updates)
