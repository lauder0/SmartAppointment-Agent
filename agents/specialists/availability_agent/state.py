"""Availability agent private state helpers."""

from __future__ import annotations

from typing import Any, Dict

from agents.supervisor.state import default_availability_state


def normalize_availability_state(raw: Dict[str, Any] | None) -> Dict[str, Any]:
    availability = dict(raw or default_availability_state())
    availability.setdefault("status", "idle")
    availability.setdefault("criteria_snapshot", None)
    availability.setdefault("options", [])
    availability.setdefault("available_technician_names", [])
    availability.setdefault("last_answer", None)
    return availability


def status_from_result(availability: Dict[str, Any]) -> str:
    return "completed" if availability.get("criteria_snapshot") else "failed"
