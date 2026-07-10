"""Appointment API routed through the LangGraph workflow."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.graph_chat_handler import process_user_input_graph
from api.graph_state_view import state_view
from .core.response_models import AppointmentRequest, DataResponse

router = APIRouter(prefix="/api/appointment", tags=["appointment"])


def _build_appointment_message(request: AppointmentRequest) -> str:
    parts = [f"I want to book {request.service_type}."]
    if request.preferred_time:
        parts.append(f"The preferred time is {request.preferred_time}.")
    if request.duration_minutes:
        parts.append(f"The duration is {request.duration_minutes} minutes.")
    if request.gender_preference:
        parts.append(f"I prefer a {request.gender_preference} technician.")
    if request.technician_name:
        parts.append(f"I prefer technician {request.technician_name}.")
    if request.preference:
        parts.append(f"Technique preference: {request.preference}.")
    if request.notes:
        parts.append(f"Additional notes: {request.notes}.")
    return " ".join(parts)


@router.post("/create", response_model=DataResponse)
async def create_appointment(request: AppointmentRequest):
    """Process a structured appointment request through LangGraph."""
    try:
        session_id = f"appointment:{request.user_id}"
        result = await process_user_input_graph(
            _build_appointment_message(request),
            session_id=session_id,
            user_id=request.user_id,
        )
        view = state_view(result)
        return DataResponse(
            message="Appointment request processed",
            data={
                "session_id": result.get("session_id", session_id),
                "reply": result.get("final_response"),
                "intent": view["intent"],
                "agent": view["agent"],
                "booking": view["booking"],
                "last_completed_booking": view["last_completed_booking"],
                "route_decision": view["route_decision"],
                "tool_results": result.get("tool_results", {}),
                "request": request.model_dump(),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
