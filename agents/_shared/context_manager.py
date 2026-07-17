"""Context merge and invalidation helpers shared by agents and Supervisor."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from config.time_utils import utc_now_iso

from .context_schema import DEPENDENCY_FIELDS, compact_focus_context, default_focus_context


EMPTY_VALUES = (None, "", "未知", [], {})


def merge_focus_context(
    current: Dict[str, Any] | None,
    updates: Dict[str, Any] | None,
    *,
    updated_by: str | None = None,
) -> Dict[str, Any]:
    """Merge non-empty updates into the cross-agent focus context.

    `context_source` tracks which layer/agent most recently supplied each
    field. This lets Supervisor and tests explain why a slot exists.
    """
    focus = compact_focus_context(current or default_focus_context())
    if not updates:
        return focus

    source = dict(focus.get("context_source") or {})
    for key, value in updates.items():
        if value in EMPTY_VALUES:
            continue
        focus[key] = value
        if updated_by:
            source[key] = updated_by
    focus["context_source"] = source
    focus["updated_by"] = updated_by or focus.get("updated_by")
    focus["updated_at"] = utc_now_iso()
    return focus


def changed_dependency_fields(
    current: Dict[str, Any] | None,
    updates: Dict[str, Any] | None,
) -> List[str]:
    """Return dependency fields whose value changed in the current turn."""
    focus = compact_focus_context(current or default_focus_context())
    changed: List[str] = []
    for field in DEPENDENCY_FIELDS:
        if field not in (updates or {}):
            continue
        value = (updates or {}).get(field)
        if value in EMPTY_VALUES:
            continue
        old = focus.get(field)
        if old not in EMPTY_VALUES and str(old) != str(value):
            changed.append(field)
    return sorted(changed)


def invalidations_for_focus_changes(changed_fields: Iterable[str]) -> List[str]:
    """Map changed focus fields to downstream state paths that must be rebuilt."""
    changed = set(changed_fields)
    invalidates: set[str] = set()
    if changed & {"service_type", "start_time", "duration_minutes", "gender_preference", "preference"}:
        invalidates.update(
            {
                "availability.criteria_snapshot",
                "availability.options",
                "availability.available_technician_names",
                "recommendation.selected_recommendation",
                "recommendation.candidate_recommendations",
                "recommendation.alternative_recommendations",
                "booking.selected_option",
                "booking.confirmation_summary",
            }
        )
    if changed & {"technician_name", "technician_id"}:
        invalidates.update(
            {
                "recommendation.selected_recommendation",
                "booking.selected_option",
                "booking.confirmation_summary",
            }
        )
    return sorted(invalidates)


def apply_state_invalidations(state: Dict[str, Any], invalidates: Iterable[str]) -> Dict[str, Any]:
    """Return a shallow state patch that clears invalidated downstream fields."""
    invalidation_set = set(invalidates or [])
    update: Dict[str, Any] = {}
    if any(path.startswith("availability.") for path in invalidation_set):
        availability = dict(state.get("availability") or {})
        if "availability.criteria_snapshot" in invalidation_set:
            availability["criteria_snapshot"] = None
        if "availability.options" in invalidation_set:
            availability["options"] = []
        if "availability.available_technician_names" in invalidation_set:
            availability["available_technician_names"] = []
        if availability:
            availability["status"] = "idle"
            update["availability"] = availability

    if any(path.startswith("recommendation.") for path in invalidation_set):
        recommendation = dict(state.get("recommendation") or {})
        if "recommendation.selected_recommendation" in invalidation_set:
            recommendation["selected_recommendation"] = None
        if "recommendation.candidate_recommendations" in invalidation_set:
            recommendation["candidate_recommendations"] = []
        if "recommendation.alternative_recommendations" in invalidation_set:
            recommendation["alternative_recommendations"] = []
        if recommendation:
            recommendation["status"] = "idle"
            update["recommendation"] = recommendation

    if any(path.startswith("booking.") for path in invalidation_set):
        booking = dict(state.get("booking") or {})
        if "booking.selected_option" in invalidation_set:
            booking["selected_option"] = None
        if "booking.confirmation_summary" in invalidation_set:
            booking["confirmation_summary"] = None
        if booking:
            if booking.get("status") == "awaiting_confirmation":
                booking["status"] = "drafting"
            booking["guard_result"] = None
            update["booking"] = booking

    return update
