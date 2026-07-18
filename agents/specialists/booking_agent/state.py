"""Booking agent private state helpers."""

from __future__ import annotations

from typing import Any, Dict

from agents.supervisor.state import default_booking_state


def normalize_booking_state(raw: Dict[str, Any] | None) -> Dict[str, Any]:
    booking = dict(raw or default_booking_state())
    booking.setdefault("status", "idle")
    booking.setdefault("draft", {})
    booking.setdefault("missing_fields", [])
    booking.setdefault("confirmation_summary", None)
    booking.setdefault("selected_option", None)
    booking.setdefault("excluded_technician_ids", [])
    booking.setdefault("guard_result", None)
    booking.setdefault("time_clarification", None)
    return booking


def booking_result_type(booking: Dict[str, Any], state: Dict[str, Any]) -> str:
    if booking.get("status") == "awaiting_confirmation":
        return "booking_confirmation"
    if booking.get("status") == "created" or state.get("last_completed_booking"):
        return "booking_created"
    if booking.get("missing_fields"):
        return "booking_missing"
    return "booking"
