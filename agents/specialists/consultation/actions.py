"""Consultation and availability graph nodes."""

from __future__ import annotations

from config.model_provider import create_chat_model
from agents.understanding.rules import is_service_catalog_question, is_service_recommendation_request
from agents.specialists.consultation.response_generator import ResponseGenerator
from agents.shared.node_utils import (
    append_assistant_message,
    focus_updates_from_availability_criteria,
    last_user_text,
    merge_focus_context,
)
from agents.shared.response_composer import composer
from agents.shared.slot_utils import default_duration_for_service
from agents.shared.state import AgentState
from tools.availability_tools import query_availability
from tools.knowledge_tools import search_knowledge
from services.appointment_service import AppointmentService


async def knowledge_consult_node(state: AgentState) -> AgentState:
    """Handle static knowledge-base consultation."""
    user_input = last_user_text(state)
    if is_service_catalog_question(user_input):
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
    focus_updates = _service_recommendation_focus_updates(user_input, answer, state)
    update = {
        "final_response": reply,
        "tool_results": {"search_knowledge": result},
    }
    if focus_updates:
        update["focus_context"] = merge_focus_context(state.get("focus_context"), focus_updates)
    return append_assistant_message(
        update,
        reply,
    )


def _service_recommendation_focus_updates(
    user_input: str,
    answer: str,
    state: AgentState,
) -> dict:
    route_decision = state.get("route_decision") or {}
    if route_decision.get("task_type") != "service_recommendation" and not is_service_recommendation_request(user_input):
        return {}

    service_type = _infer_service_from_text(f"{answer}\n{user_input}")
    if not service_type:
        return {}

    duration = default_duration_for_service(service_type)
    updates = {
        "service_type": service_type,
        "last_offer": "service_recommendation",
        "service_source": "recommended",
    }
    if duration:
        updates["duration_minutes"] = duration
    return updates


def _infer_service_from_text(text: str) -> str | None:
    for service_type in ("背部推拿", "肩颈推拿", "足底按摩", "全身推拿"):
        if service_type in text:
            return service_type

    symptom_rules = (
        ("背部推拿", ("腰", "背", "腰酸", "腰痛", "背痛", "腰背", "脊柱")),
        ("肩颈推拿", ("肩", "颈", "脖子", "肩颈", "颈椎")),
        ("足底按摩", ("脚", "足", "足底", "睡眠", "助眠")),
        ("全身推拿", ("全身", "疲劳", "放松", "累", "乏")),
    )
    for service_type, keywords in symptom_rules:
        if any(keyword in text for keyword in keywords):
            return service_type
    return None

