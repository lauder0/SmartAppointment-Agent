"""Availability specialist actions."""

from __future__ import annotations

from agents.shared.node_utils import (
    append_assistant_message,
    focus_updates_from_availability_criteria,
    last_user_text,
    merge_focus_context,
)
from agents.shared.response_composer import composer
from agents.shared.state import AgentState
from tools.availability_tools import query_availability
from services.appointment_service import AppointmentService


async def availability_query_node(state: AgentState) -> AgentState:
    """Handle realtime availability query."""
    user_input = last_user_text(state)
    base_criteria = None
    if state.get("availability_result"):
        base_criteria = state["availability_result"].get("criteria_snapshot")

    result = query_availability.invoke({"text": user_input, "base_criteria": base_criteria})
    if result.get("success"):
        data = result.get("data", {})
        reply = await composer.areply(
            "availability_result",
            {
                "body": data.get("answer") or "已完成实时排班查询。",
                "criteria": data.get("criteria") or {},
                "available_technician_names": data.get("available_technician_names", []),
            },
            {"user_input": user_input},
        )
        criteria = data.get("criteria")
        available_names = data.get("available_technician_names", [])
        focus_context = merge_focus_context(
            state.get("focus_context"),
            focus_updates_from_availability_criteria(criteria),
        )
        options = _availability_options(criteria, available_names)
        availability_result = {
            "criteria_snapshot": criteria,
            "options": options,
            "available_technician_names": available_names,
            "last_answer": reply,
        }
    else:
        reply = composer.reply(
            "availability_failed",
            {"body": f"抱歉，实时排班查询失败：{result.get('error') or result.get('message')}"},
        )
        focus_context = state.get("focus_context")
        availability_result = state.get("availability_result")

    update = {
        "final_response": reply,
        "focus_context": focus_context,
        "availability_result": availability_result,
        "tool_results": {"query_availability": result},
    }
    route_reason = (state.get("route_decision") or {}).get("reason")
    if route_reason == "prepare_candidates_for_recommendation" and result.get("success"):
        update["final_response"] = None
        return update
    return append_assistant_message(update, reply)


def _availability_options(criteria: dict | None, technician_names: list[str]) -> list[dict]:
    criteria = criteria or {}
    technicians_by_name = {
        tech.get("name"): tech
        for tech in AppointmentService().get_all_technicians()
        if tech.get("name")
    }
    options = []
    for index, name in enumerate(technician_names, start=1):
        tech = technicians_by_name.get(name) or {}
        options.append(
            {
                "option_id": f"opt_{index}",
                "technician_id": tech.get("id"),
                "technician_name": name,
                "start_time": criteria.get("start_time"),
                "duration_minutes": criteria.get("duration_minutes"),
                "service_type": criteria.get("service_type"),
                "gender_preference": criteria.get("gender"),
                "preference": criteria.get("preference"),
            }
        )
    return options
