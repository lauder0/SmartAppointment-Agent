"""Input normalization and deterministic slot extraction."""

from __future__ import annotations

import re
from typing import Any, Dict

from config.time_config import time_config
from services.availability_service import AvailabilityService

from .schemas import NormalizedInput, compact_slots


def normalize_user_input(user_text: str) -> NormalizedInput:
    """Normalize text and extract directly observable candidate slots."""
    raw_text = user_text or ""
    normalized_text = _normalize_text(raw_text)
    availability_service = AvailabilityService()
    criteria = availability_service.parse_query_criteria(raw_text)
    candidate_slots: Dict[str, Any] = {
        "service_type": criteria.get("service_type"),
        "start_time": _serialize_datetime(criteria.get("start_time")),
        "duration_minutes": criteria.get("duration_minutes"),
        "gender_preference": criteria.get("gender"),
        "technician_name": criteria.get("technician_name"),
        "preference": criteria.get("preference"),
    }
    return {
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "candidate_slots": compact_slots(candidate_slots),
        "availability_criteria": criteria,
    }


def _normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[\s，。！？、,.!?；;：:]+", "", text)
    return text


def _serialize_datetime(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "year") and hasattr(value, "hour"):
        return time_config.format_datetime(value)
    return value
