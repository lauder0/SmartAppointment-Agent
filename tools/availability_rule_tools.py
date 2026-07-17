"""Rule/parser helpers exposed through the tools layer."""

from __future__ import annotations

from typing import Any, Dict

from services.availability_service import AvailabilityIntent, AvailabilityService


def is_formal_booking_request(text: str) -> bool:
    return AvailabilityService.is_formal_booking_request(text)


def parse_service_type(text: str) -> str | None:
    return AvailabilityService.parse_service_type(text)


def parse_query_criteria(text: str) -> Dict[str, Any]:
    return AvailabilityService().parse_query_criteria(text)


def parse_preference(text: str) -> str | None:
    return AvailabilityService().parse_preference(text)


def is_clear_appointment_start(text: str) -> bool:
    return AvailabilityService.is_clear_appointment_start(text)


def is_availability_follow_up(text: str) -> bool:
    return AvailabilityService().is_availability_follow_up(text)


def classify_availability_intent_by_rules(text: str) -> AvailabilityIntent:
    return AvailabilityService().classify_availability_intent_by_rules(text)
