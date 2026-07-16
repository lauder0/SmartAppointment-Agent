"""Rule-driven signal collection for clear business expressions."""

from __future__ import annotations

from typing import Any, Dict, List

from agents.understander.rules import RuleMatch, classify_rule_matches

from .schemas import IntentSignal


def collect_rule_signals(
    user_text: str,
    normalized: Dict[str, Any],
    state: Dict[str, Any],
) -> List[IntentSignal]:
    """Collect all clear signals instead of returning on first match."""
    signals: List[IntentSignal] = []
    slots = normalized.get("candidate_slots") or {}
    focus = state.get("focus_context") or {}
    booking = state.get("booking") or {}
    recommendation = state.get("recommendation") or {}

    def add(
        name: str,
        confidence: float = 0.9,
        matched_text: str = "",
        extra_slots: Dict[str, Any] | None = None,
        intent_group: str = "",
        subtype: str = "",
        requires_context: bool = False,
        attributes: Dict[str, Any] | None = None,
    ) -> None:
        merged_slots = dict(slots)
        if extra_slots:
            merged_slots.update(extra_slots)
        signals.append(
            {
                "name": name,
                "intent_group": intent_group,
                "subtype": subtype,
                "confidence": confidence,
                "source": "rule",
                "matched_text": matched_text or user_text,
                "requires_context": requires_context,
                "attributes": attributes or {},
                "slots": {k: v for k, v in merged_slots.items() if v not in (None, "", [], {})},
            }
        )

    def add_match(match: RuleMatch) -> None:
        add(
            match.signal_name,
            match.confidence,
            intent_group=match.intent_group,
            subtype=match.subtype,
            requires_context=match.requires_context,
            attributes=dict(match.attributes or {}),
        )

    for match in classify_rule_matches(user_text):
        add_match(match)

    if slots.get("service_type") and focus.get("last_offer") == "service_catalog":
        add(
            "service_selection_after_catalog",
            0.93,
            intent_group="context_operation",
            subtype="service_selection_after_catalog",
            requires_context=True,
        )
    if slots.get("service_type") and any(
        keyword in user_text for keyword in ("想做", "想要做", "我想做", "我要做", "选", "做这个", "就这个")
    ):
        add(
            "service_selection",
            0.9,
            intent_group="context_operation",
            subtype="service_selection",
            requires_context=True,
        )
    if slots:
        add(
            "slot_update",
            0.82,
            intent_group="context_operation",
            subtype="slot_update",
            requires_context=True,
        )
    if booking.get("status") == "awaiting_confirmation":
        add(
            "booking_confirmation_context",
            0.99,
            intent_group="context_operation",
            subtype="booking_awaiting_confirmation",
            requires_context=True,
        )
    if recommendation.get("status") == "awaiting_selection":
        add(
            "recommendation_selection_context",
            0.99,
            intent_group="context_operation",
            subtype="recommendation_awaiting_selection",
            requires_context=True,
        )

    return _dedupe_signals(signals)


def _dedupe_signals(signals: List[IntentSignal]) -> List[IntentSignal]:
    best: Dict[str, IntentSignal] = {}
    for signal in signals:
        name = signal.get("name")
        if not name:
            continue
        key = f"{name}:{signal.get('subtype') or ''}"
        current = best.get(key)
        if current is None or float(signal.get("confidence", 0.0)) > float(current.get("confidence", 0.0)):
            best[key] = signal
    return list(best.values())
