"""Shared focus-context schema for cross-agent context sharing."""

from __future__ import annotations

from typing import Any, Dict


FOCUS_CONTEXT_KEYS = (
    "service_type",
    "start_time",
    "duration_minutes",
    "gender_preference",
    "technician_name",
    "technician_id",
    "preference",
    "symptom_or_need",
    "recommended_service",
    "selected_recommendation_ref",
    "last_offer",
    "context_source",
    "updated_by",
    "updated_at",
)


DEPENDENCY_FIELDS = {
    "service_type",
    "start_time",
    "duration_minutes",
    "gender_preference",
    "technician_name",
    "technician_id",
    "preference",
}


def default_focus_context() -> Dict[str, Any]:
    """Create a fresh cross-agent context describing the user's current focus."""
    return {
        "service_type": None,
        "start_time": None,
        "duration_minutes": None,
        "gender_preference": None,
        "technician_name": None,
        "technician_id": None,
        "preference": None,
        "symptom_or_need": None,
        "recommended_service": None,
        "selected_recommendation_ref": None,
        "last_offer": None,
        "context_source": {},
        "updated_by": None,
        "updated_at": None,
    }


def compact_focus_context(raw: Dict[str, Any] | None) -> Dict[str, Any]:
    """Normalize a potentially older focus-context payload to the current schema."""
    focus = default_focus_context()
    if raw:
        for key, value in raw.items():
            if key in FOCUS_CONTEXT_KEYS or key not in focus:
                focus[key] = value
    if not isinstance(focus.get("context_source"), dict):
        focus["context_source"] = {}
    return focus
