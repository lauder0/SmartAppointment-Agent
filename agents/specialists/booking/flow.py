"""Booking agent internal workflow."""

from __future__ import annotations

from typing import Any, Dict

from .nodes import (
    accept_recommendation,
    ask_confirmation,
    ask_missing_slots,
    clarify_booking,
    complete_booking,
    create_transaction,
    fail_booking,
    guard_booking,
    interpret_confirmation,
    match_slot,
    parse_slots,
    record_behavior,
)


async def run_booking_flow(action: str | None, state: Dict[str, Any]) -> Dict[str, Any]:
    if action in {"start_or_continue_booking", "modify_booking"}:
        return await run_slot_filling_flow(state)
    if action in {"confirm_booking", "cancel_booking"}:
        return await run_confirmation_flow(state)
    if action == "select_recommended_technician":
        return await run_recommendation_selection_flow(state)
    return await clarify_booking(state)


async def run_slot_filling_flow(state: Dict[str, Any]) -> Dict[str, Any]:
    state = await parse_slots(state)
    booking = state.get("booking") or {}
    if booking.get("missing_fields"):
        return await ask_missing_slots(state)

    state = await match_slot(state)
    booking = state.get("booking") or {}
    if booking.get("selected_option"):
        return await ask_confirmation(state)
    return await fail_booking(state)


async def run_confirmation_flow(state: Dict[str, Any]) -> Dict[str, Any]:
    state = await interpret_confirmation(state)
    booking = state.get("booking") or {}
    if booking.get("status") != "confirmed":
        return state

    state = await guard_booking(state)
    guard = (state.get("tool_results") or {}).get("booking_guard") or {}
    if not guard.get("success"):
        return state

    state = await create_transaction(state)
    create_result = (state.get("tool_results") or {}).get("create_appointment") or {}
    if create_result.get("success"):
        state = await record_behavior(state)
        return await complete_booking(state)
    return await fail_booking(state)


async def run_recommendation_selection_flow(state: Dict[str, Any]) -> Dict[str, Any]:
    state = await accept_recommendation(state)
    booking = state.get("booking") or {}
    if booking.get("missing_fields"):
        return await ask_missing_slots(state)
    return await ask_confirmation(state)
