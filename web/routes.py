"""Web page routes."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from api.chat_handler import ProcessUserInput_stream, reset_session


logger = logging.getLogger(__name__)
templates = Jinja2Templates(directory="web/templates")
MAX_STREAM_CHUNKS = 4000

router = APIRouter(tags=["Web"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    state: str | None = None


class ResetChatRequest(BaseModel):
    session_id: str


@router.get("/", response_class=HTMLResponse, summary="Home")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


async def _stream_chat(message: str, session_id: str | None):
    chunk_count = 0
    async for token in ProcessUserInput_stream(message, session_id=session_id):
        yield token
        chunk_count += 1
        if chunk_count >= MAX_STREAM_CHUNKS:
            yield "\n[ERROR] Response was too long and has been stopped."
            break


@router.post("/chat/stream", summary="Streaming chat")
async def chat_stream_endpoint(chat: ChatRequest):
    return StreamingResponse(
        _stream_chat(chat.message, chat.session_id),
        media_type="text/plain",
    )


@router.post("/chat", summary="Compatibility chat endpoint")
async def chat_endpoint(chat: ChatRequest):
    return StreamingResponse(
        _stream_chat(chat.message, chat.session_id),
        media_type="text/plain",
    )


@router.post("/chat/reset", summary="Reset chat session")
async def chat_reset_endpoint(reset: ResetChatRequest):
    await reset_session(reset.session_id)
    return {"status": "success"}


@router.get("/user_behavior", response_class=HTMLResponse, summary="User behavior page")
async def user_behavior_page(request: Request):
    return templates.TemplateResponse("user_behavior_analysis.html", {"request": request})


@router.get("/knowledge", response_class=HTMLResponse, summary="Knowledge page")
async def knowledge_page(request: Request):
    try:
        from api.knowledge import get_all_knowledge

        knowledge_data = await get_all_knowledge()
        return templates.TemplateResponse(
            "knowledge_management.html",
            {
                "request": request,
                "documents": knowledge_data.get("documents", []),
                "categories": knowledge_data.get("categories", []),
            },
        )
    except Exception as exc:
        logger.error("Failed to load knowledge page: %s", exc)
        return templates.TemplateResponse(
            "knowledge_management.html",
            {"request": request, "documents": [], "categories": [], "error": str(exc)},
        )


@router.get("/technician", response_class=HTMLResponse, summary="Technician page")
async def technician_page(request: Request):
    try:
        from api.technician import get_all_technicians

        technicians = await get_all_technicians()
        return templates.TemplateResponse(
            "technician.html",
            {"request": request, "technicians": technicians},
        )
    except Exception as exc:
        logger.error("Failed to load technicians: %s", exc)
        return templates.TemplateResponse(
            "technician.html",
            {"request": request, "technicians": [], "error": str(exc)},
        )


@router.get(
    "/technician_schedule",
    response_class=HTMLResponse,
    summary="Technician schedule page",
)
async def technician_schedule_page(request: Request):
    try:
        from api.technician import get_all_technicians_schedule_window
        from config.time_config import time_config

        schedule_days = await get_all_technicians_schedule_window()
        return templates.TemplateResponse(
            "technician_schedule.html",
            {
                "request": request,
                "schedule_days": schedule_days,
                "current_date": time_config.current_date_str(),
                "business_hours": time_config.get_business_hours(),
            },
        )
    except Exception as exc:
        logger.error("Failed to load technician schedules: %s", exc)
        return templates.TemplateResponse(
            "technician_schedule.html",
            {
                "request": request,
                "schedule_days": [],
                "business_hours": (10, 22),
                "error": str(exc),
            },
        )


@router.get(
    "/user_behavior_analysis",
    response_class=HTMLResponse,
    summary="User behavior analysis page",
)
async def user_behavior_analysis_page(request: Request):
    return RedirectResponse(url="/user_behavior")
