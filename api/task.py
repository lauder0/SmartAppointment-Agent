"""Task API routed through the LangGraph workflow."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.graph_chat_handler import process_user_input_graph
from api.graph_state_view import state_view
from .core.response_models import DataResponse, TaskClassificationRequest

router = APIRouter(prefix="/api/task", tags=["task"])


@router.post("/classify", response_model=DataResponse)
async def classify_task(request: TaskClassificationRequest):
    """Classify and process a task through LangGraph."""
    try:
        user_input = request.text or request.message
        if not user_input:
            raise HTTPException(status_code=400, detail="Missing task content; provide text or message.")

        context = request.context or {}
        session_id = context.get("session_id")
        user_id = context.get("user_id", "default_user")
        result = await process_user_input_graph(
            user_input,
            session_id=session_id,
            user_id=user_id,
        )
        view = state_view(result)

        return DataResponse(
            message="Task processed",
            data={
                "session_id": result.get("session_id", session_id),
                "reply": result.get("final_response"),
                "intent": view["intent"],
                "agent": view["agent"],
                "route_decision": view["route_decision"],
                "tool_results": result.get("tool_results", {}),
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
