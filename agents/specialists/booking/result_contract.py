"""Structured Booking result contract.

Booking owns side-effecting appointment creation, so its graph output needs a
stable contract before Supervisor publishes any user-facing response.
"""

from __future__ import annotations

from typing import Any, Dict, Literal, TypedDict

from agents.specialists.result_contract import SpecialistResult, agent_result

from .state import booking_result_type


BOOKING_RESULT_CONTRACT_VERSION = "booking_result.v1"


BookingResultType = Literal[
    "booking_confirmation",
    "booking_recommendation",
    "booking_created",
    "booking_missing",
    "booking_cancelled",
    "booking_unclear_confirmation",
    "booking_guard_missing",
    "booking_guard_invalid",
    "booking_guard_time_invalid",
    "booking_guard_technician_unavailable",
    "booking_failed",
    "booking",
]


class BookingResultContract(TypedDict, total=False):
    """Booking result contract consumed by Supervisor."""

    version: str
    agent_name: str
    status: str
    result_type: BookingResultType
    response_type: str
    facts: Dict[str, Any]
    state_updates: Dict[str, Any]
    tool_results: Dict[str, Any]
    requires_user_input: bool
    next_expected_user_action: str | None
    write_performed: bool
    safety: Dict[str, Any]
    draft_snapshot: Dict[str, Any]
    selected_option: Dict[str, Any] | None
    completed_booking: Dict[str, Any] | None
    error: str | None


_RESPONSE_TYPE_BY_RESULT_TYPE = {
    "booking_confirmation": "booking_confirmation",
    "booking_recommendation": "booking_recommendation",
    "booking_created": "booking_success",
    "booking_missing": "booking_missing_slots",
    "booking_cancelled": "booking_cancelled",
    "booking_unclear_confirmation": "booking_unclear_confirmation",
    "booking_guard_missing": "booking_guard_missing",
    "booking_guard_invalid": "booking_guard_invalid",
    "booking_guard_time_invalid": "booking_guard_time_invalid",
    "booking_guard_technician_unavailable": "booking_guard_technician_unavailable",
    "booking_failed": "booking_failed",
    "booking": "clarification",
}

_USER_INPUT_ACTION_BY_RESULT_TYPE = {
    "booking_confirmation": "confirm_or_cancel_booking",
    "booking_recommendation": "accept_or_reject_booking_recommendation",
    "booking_missing": "provide_missing_booking_slots",
    "booking_unclear_confirmation": "reply_confirm_or_cancel",
    "booking_guard_missing": "provide_required_booking_fields",
    "booking_guard_invalid": "revise_invalid_booking_fields",
    "booking_guard_time_invalid": "choose_another_time",
    "booking_guard_technician_unavailable": "choose_another_time_or_technician",
    "booking_failed": "revise_booking_request",
    "booking": "clarify_booking_request",
}


def build_booking_result_contract(
    *,
    action: str | None,
    booking: Dict[str, Any],
    aggregate: Dict[str, Any],
    merged_state: Dict[str, Any],
) -> BookingResultContract:
    """Normalize a Booking flow aggregate into one stable result contract."""
    result_type = _resolve_result_type(booking, aggregate, merged_state)
    response_type = aggregate.get("response_type") or _RESPONSE_TYPE_BY_RESULT_TYPE.get(result_type, result_type)
    facts = dict(aggregate.get("response_facts") or {})
    tool_results = dict(merged_state.get("tool_results") or {})
    completed_booking = merged_state.get("last_completed_booking")
    create_result = tool_results.get("create_appointment") or {}
    guard_result = tool_results.get("booking_guard") or {}
    write_performed = bool(result_type == "booking_created" and create_result.get("success"))
    next_action = _USER_INPUT_ACTION_BY_RESULT_TYPE.get(result_type)
    status = _contract_status(result_type, booking)
    error = _contract_error(result_type, tool_results)
    state_updates = {"booking": booking}
    if completed_booking:
        state_updates["last_completed_booking"] = completed_booking

    contract: BookingResultContract = {
        "version": BOOKING_RESULT_CONTRACT_VERSION,
        "agent_name": "booking",
        "status": status,
        "result_type": result_type,
        "response_type": response_type,
        "facts": facts,
        "state_updates": state_updates,
        "tool_results": tool_results,
        "requires_user_input": next_action is not None,
        "next_expected_user_action": next_action,
        "write_performed": write_performed,
        "safety": {
            "action": action,
            "confirmation_required": result_type in {"booking_confirmation", "booking_created"},
            "confirmed": result_type == "booking_created" or booking.get("status") == "confirmed",
            "guard_success": guard_result.get("success"),
            "guard_reason": guard_result.get("reason"),
            "create_success": create_result.get("success"),
            "idempotency_key": (create_result.get("data") or {}).get("idempotency_key"),
        },
        "draft_snapshot": dict(booking.get("draft") or {}),
        "selected_option": booking.get("selected_option"),
        "completed_booking": completed_booking,
        "error": error,
    }
    return contract


def booking_contract_to_specialist_result(contract: BookingResultContract) -> SpecialistResult:
    """Adapt a BookingResultContract to the generic SpecialistResult envelope."""
    facts = dict(contract.get("facts") or {})
    facts["booking_result"] = _public_contract(contract)
    return agent_result(
        "booking",
        contract.get("status") or "unknown",
        contract.get("result_type") or "booking",
        None,
        contract.get("state_updates") or {},
        response_type=contract.get("response_type"),
        facts=facts,
        tool_results=contract.get("tool_results") or {},
        requires_user_input=bool(contract.get("requires_user_input")),
        next_expected_user_action=contract.get("next_expected_user_action"),
        error=contract.get("error"),
    )


def _resolve_result_type(
    booking: Dict[str, Any],
    aggregate: Dict[str, Any],
    merged_state: Dict[str, Any],
) -> BookingResultType:
    raw = aggregate.get("result_type") or booking_result_type(booking, merged_state)
    return raw if raw in _RESPONSE_TYPE_BY_RESULT_TYPE else "booking"


def _contract_status(result_type: str, booking: Dict[str, Any]) -> str:
    if result_type == "booking_created":
        return "completed"
    if result_type == "booking_cancelled":
        return "cancelled"
    if result_type.startswith("booking_guard") or result_type == "booking_failed":
        return "blocked"
    return str(booking.get("status") or "unknown")


def _contract_error(result_type: str, tool_results: Dict[str, Any]) -> str | None:
    if result_type in {"booking_created", "booking_confirmation", "booking_missing", "booking_cancelled"}:
        return None
    for key in ("create_appointment", "booking_guard", "match_technician"):
        result = tool_results.get(key) or {}
        error = result.get("error") or result.get("reason")
        if error:
            return str(error)
    return None


def _public_contract(contract: BookingResultContract) -> Dict[str, Any]:
    """Return contract fields useful to Supervisor, API views, and evals."""
    return {
        "version": contract.get("version"),
        "status": contract.get("status"),
        "result_type": contract.get("result_type"),
        "response_type": contract.get("response_type"),
        "requires_user_input": contract.get("requires_user_input"),
        "next_expected_user_action": contract.get("next_expected_user_action"),
        "write_performed": contract.get("write_performed"),
        "safety": contract.get("safety"),
        "draft_snapshot": contract.get("draft_snapshot"),
        "selected_option": contract.get("selected_option"),
        "completed_booking": contract.get("completed_booking"),
        "error": contract.get("error"),
    }
