from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from config.time_utils import business_now_naive
from services.preference_recall_service import PreferenceRecallService
from services.recommendation_service import RecommendationService
from services.appointment_service import AppointmentService

router = APIRouter(prefix="/api/user-behavior", tags=["user behavior"])
router_underscore = APIRouter(prefix="/api/user_behavior", tags=["user behavior"])

logger = logging.getLogger(__name__)


class UserAnalysisResponse(BaseModel):
    favorite_technician_id: Optional[int] = None
    favorite_technician_name: Optional[str] = None
    favorite_service: Optional[str] = None
    favorite_duration: Optional[int] = None
    total_appointments: int = 0
    days_since_last_appointment: Optional[int] = None
    should_send_reminder: bool = False


class ReminderRequest(BaseModel):
    user_id: str = "default_user"


class ReminderResponse(BaseModel):
    message: str
    technician_available_times: Optional[list] = None


async def get_user_analysis(user_id: str = "default_user") -> UserAnalysisResponse:
    """Return dashboard-friendly behavior analysis from the service layer."""
    try:
        profile = PreferenceRecallService().recall(user_id)
        appointments = AppointmentService().get_user_appointments(user_id)

        last_visit = _latest_appointment_time(appointments)
        days_since_last = (
            (business_now_naive() - last_visit.replace(tzinfo=None)).days
            if last_visit
            else None
        )
        should_send = days_since_last is not None and days_since_last >= 30

        return UserAnalysisResponse(
            favorite_technician_id=profile.get("preferred_technician_id"),
            favorite_technician_name=profile.get("preferred_technician_name"),
            favorite_service=profile.get("preferred_service"),
            favorite_duration=profile.get("preferred_duration_minutes"),
            total_appointments=len(appointments),
            days_since_last_appointment=days_since_last,
            should_send_reminder=should_send,
        )
    except Exception as e:
        logger.error("Failed to get user behavior analysis: %s", e)
        return UserAnalysisResponse()


@router.get("/analysis", response_model=UserAnalysisResponse)
async def get_default_user_analysis():
    return await get_user_analysis("default_user")


@router.get("/dashboard_data", response_model=UserAnalysisResponse)
async def get_dashboard_data():
    return await get_user_analysis("default_user")


@router_underscore.get("/dashboard_data", response_model=UserAnalysisResponse)
async def get_dashboard_data_underscore():
    return await get_user_analysis("default_user")


@router.post("/send-reminder", response_model=ReminderResponse, summary="Generate return reminder")
async def send_reminder(request: ReminderRequest):
    try:
        result = RecommendationService().preview_return_reminder(request.user_id)
        return ReminderResponse(
            message=result["message"],
            technician_available_times=result["technician_available_times"],
        )
    except Exception as e:
        logger.error("Failed to generate return reminder: %s", e)
        return ReminderResponse(
            message=(
                "The system cannot generate a personalized reminder right now. "
                "Please try again later or contact the store directly."
            ),
            technician_available_times=[],
        )


def _latest_appointment_time(appointments: list[dict]) -> Optional[datetime]:
    dates = []
    for appointment in appointments:
        value = appointment.get("start_time")
        if isinstance(value, datetime):
            dates.append(value)
        elif value:
            try:
                dates.append(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
            except ValueError:
                continue
    return max(dates) if dates else None
