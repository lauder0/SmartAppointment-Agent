"""Pydantic schemas shared by agent tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def tool_result(
    success: bool,
    data: Any = None,
    message: str = "",
    error: str | None = None,
) -> Dict[str, Any]:
    """Return a consistent result envelope for tools."""
    return {
        "success": success,
        "data": data,
        "message": message,
        "error": error,
    }


class SearchKnowledgeInput(BaseModel):
    query: str = Field(description="user knowledge query")
    top_k: int = Field(default=3, ge=1, le=5, description="number of documents")
    category: Optional[str] = Field(default=None, description="optional knowledge category")


class QueryAvailabilityInput(BaseModel):
    text: str = Field(description="raw availability query")
    base_criteria: Optional[Dict[str, Any]] = Field(default=None, description="previous criteria")


class MatchTechnicianInput(BaseModel):
    start_time: str = Field(description="appointment start time, YYYY-MM-DD HH:MM")
    duration_minutes: int = Field(gt=0, description="duration in minutes")
    gender_preference: Optional[str] = Field(default=None, description="technician gender preference")
    preference: Optional[str] = Field(default=None, description="style or strength preference")
    technician_name: Optional[str] = Field(default=None, description="specified technician name")
    excluded_technician_ids: List[int] = Field(
        default_factory=list,
        description="technician ids that should not be selected",
    )
    user_id: Optional[str] = Field(default="default_user", description="user id for preference recall")


class CreateAppointmentInput(BaseModel):
    user_id: str = Field(default="default_user", description="user id")
    session_id: str = Field(description="current session id")
    technician_id: int = Field(description="technician id")
    service_name: str = Field(description="service item name")
    start_time: str = Field(description="appointment start time, YYYY-MM-DD HH:MM")
    duration_minutes: int = Field(gt=0, description="duration in minutes")
    gender_preference: Optional[str] = Field(default=None, description="technician gender preference")
    preference: Optional[str] = Field(default=None, description="style or strength preference")
    idempotency_key: Optional[str] = Field(default=None, description="dedupe key for retry-safe creation")


class RecordUserBehaviorInput(BaseModel):
    user_id: str = Field(default="default_user", description="user id")
    action_type: str = Field(description="behavior type, such as appointment/consultation")
    action_data: Dict[str, Any] = Field(default_factory=dict, description="behavior details")
    technician_id: Optional[str] = Field(default=None, description="related technician id")
    session_id: str = Field(default="default_session", description="session id")


class GetWeatherInput(BaseModel):
    city: str = Field(default="Beijing", description="city name")
