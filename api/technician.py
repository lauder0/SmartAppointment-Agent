"""Technician API endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config.time_config import time_config


router = APIRouter(prefix="/api/technicians", tags=["technicians"])


class TechnicianResponse(BaseModel):
    id: int
    name: str
    gender: str
    strength: str


class ScheduleResponse(BaseModel):
    id: int
    technician_id: int
    start_time: str
    end_time: str
    status: str
    appointment_id: int | None = None


def _technician_service():
    from services.technician_service import TechnicianService

    service = TechnicianService()
    service.initialize_default_technicians()
    return service


def _parse_date(value: str | None):
    if not value:
        return time_config.today()
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD") from exc
    return parsed.replace(tzinfo=time_config.BEIJING_TZ)


def _format_busy_periods(schedules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    busy_periods = []
    for sched in schedules:
        if sched.get("status") != "busy":
            continue
        start_time = sched["start_time"]
        end_time = sched["end_time"]
        busy_periods.append(
            {
                "start": start_time.strftime("%H:%M") if hasattr(start_time, "strftime") else str(start_time),
                "end": end_time.strftime("%H:%M") if hasattr(end_time, "strftime") else str(end_time),
                "appointment_id": sched.get("appointment_id"),
            }
        )
    return busy_periods


def _schedule_day_payload(service, technicians: List[Dict[str, Any]], target_day) -> Dict[str, Any]:
    start_hour, end_hour = time_config.get_business_hours()
    return {
        "date": target_day.strftime("%Y-%m-%d"),
        "is_today": target_day.date() == time_config.today().date(),
        "business_hours": {
            "start": f"{start_hour:02d}:00",
            "end": f"{end_hour:02d}:00",
        },
        "technicians": [
            {
                "technician_id": tech["id"],
                "technician_name": tech["name"],
                "busy_periods": _format_busy_periods(service.get_technician_schedules(tech["id"], target_day)),
            }
            for tech in technicians
        ],
    }


@router.get("/", response_model=List[TechnicianResponse], summary="Get all technicians")
async def get_all_technicians():
    try:
        service = _technician_service()
        technicians = service.get_all_technicians()
        return [
            TechnicianResponse(
                id=tech["id"],
                name=tech["name"],
                gender=tech.get("gender", ""),
                strength=tech.get("strength", ""),
            )
            for tech in technicians
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get technicians: {exc}") from exc


@router.get("/schedules/window", summary="Get technician schedules in the bookable window")
async def get_all_technicians_schedule_window(days: int | None = None):
    """Return all technician schedules for today, tomorrow, and the day after tomorrow."""
    try:
        service = _technician_service()
        technicians = service.get_all_technicians()
        max_days = time_config.get_booking_window_days()
        requested_days = max(1, min(days or max_days, max_days))
        today = time_config.today()
        return [
            _schedule_day_payload(service, technicians, today + timedelta(days=offset))
            for offset in range(requested_days)
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get schedule window: {exc}") from exc


@router.get("/schedules/today", summary="Get all technician schedules today")
async def get_all_technicians_schedule_today():
    """Compatibility endpoint returning only the first day of the schedule window."""
    window = await get_all_technicians_schedule_window(days=1)
    today = window[0] if window else {"technicians": []}
    return [
        {
            "technician_id": item["technician_id"],
            "technician_name": item["technician_name"],
            "busy_periods": item["busy_periods"],
        }
        for item in today.get("technicians", [])
    ]


@router.get("/{technician_id}/schedule", response_model=List[ScheduleResponse], summary="Get technician schedule")
async def get_technician_schedule(technician_id: int, date: str | None = None):
    """Return one technician's schedule for a requested date. Defaults to today."""
    try:
        service = _technician_service()
        tech = service.get_technician_by_id(technician_id)
        if not tech:
            raise HTTPException(status_code=404, detail="Technician not found")

        target_day = _parse_date(date)
        schedules = service.get_technician_schedules(technician_id, target_day)
        return [
            ScheduleResponse(
                id=sched["id"],
                technician_id=sched["technician_id"],
                start_time=sched["start_time"].strftime("%H:%M"),
                end_time=sched["end_time"].strftime("%H:%M"),
                status=sched["status"],
                appointment_id=sched.get("appointment_id"),
            )
            for sched in schedules
        ]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get technician schedule: {exc}") from exc


@router.get("/{technician_id}", response_model=TechnicianResponse, summary="Get single technician")
async def get_technician(technician_id: int):
    try:
        service = _technician_service()
        tech = service.get_technician_by_id(technician_id)
        if not tech:
            raise HTTPException(status_code=404, detail="Technician not found")
        return TechnicianResponse(
            id=tech["id"],
            name=tech["name"],
            gender=tech.get("gender", ""),
            strength=tech.get("strength", ""),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get technician: {exc}") from exc
