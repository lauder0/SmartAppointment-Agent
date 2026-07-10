"""Consultation and availability graph nodes."""

from __future__ import annotations

from config.model_provider import create_chat_model
from agents.specialists.consultation.response_generator import ResponseGenerator
from agents.shared.node_utils import (
    append_assistant_message,
    focus_updates_from_availability_criteria,
    last_user_text,
    merge_focus_context,
)
from agents.shared.response_composer import composer
from agents.shared.state import AgentState
from tools.availability_tools import query_availability
from tools.knowledge_tools import search_knowledge
from services.appointment_service import AppointmentService


async def knowledge_consult_node(state: AgentState) -> AgentState:
    """Handle static knowledge-base consultation."""
    user_input = last_user_text(state)
    if _is_service_catalog_question(user_input):
        reply = composer.reply("service_catalog")
        focus_context = merge_focus_context(state.get("focus_context"), {"last_offer": "service_catalog"})
        return append_assistant_message(
            {
                "final_response": reply,
                "focus_context": focus_context,
            },
            reply,
        )

    result = await search_knowledge.ainvoke({"query": user_input, "top_k": 3})
    docs = []
    if result.get("success"):
        docs = result.get("data", {}).get("documents", [])

    generator = ResponseGenerator(create_chat_model(temperature=0.3))
    answer = await generator.generate_response(user_input, docs)
    reply = composer.reply("knowledge_answer", {"answer": answer})
    return append_assistant_message(
        {
            "final_response": reply,
            "tool_results": {"search_knowledge": result},
        },
        reply,
    )


def _is_service_catalog_question(text: str) -> bool:
    keywords = ["有哪些服务", "有什么服务", "服务项目", "都有什么项目", "有哪些项目", "有什么项目"]
    return any(keyword in text for keyword in keywords)
