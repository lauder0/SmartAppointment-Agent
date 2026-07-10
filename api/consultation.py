"""Consultation API routed through the LangGraph workflow."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.graph_chat_handler import process_user_input_graph
from api.graph_state_view import state_view
from .core.response_models import ConsultationRequest, DataResponse

router = APIRouter(prefix="/api/consultation", tags=["consultation"])


@router.post("/ask", response_model=DataResponse)
async def ask_consultation(request: ConsultationRequest):
    """Process a consultation question through LangGraph."""
    try:
        session_id = f"consultation:{request.user_id}"
        result = await process_user_input_graph(
            request.question,
            session_id=session_id,
            user_id=request.user_id,
        )
        view = state_view(result)
        return DataResponse(
            message="Consultation processed",
            data={
                "session_id": result.get("session_id", session_id),
                "answer": result.get("final_response"),
                "question": request.question,
                "intent": view["intent"],
                "agent": view["agent"],
                "route_decision": view["route_decision"],
                "tool_results": result.get("tool_results", {}),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
