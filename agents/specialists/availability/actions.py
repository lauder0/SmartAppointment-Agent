"""Availability specialist actions."""

from __future__ import annotations

from agents.shared.node_utils import (
    focus_updates_from_availability_criteria,
    last_user_text,
    merge_focus_context,
)
from agents.shared.state import AgentState
from tools.availability_tools import query_availability
from services.appointment_service import AppointmentService


async def availability_query_node(state: AgentState) -> AgentState:
    """Handle realtime availability query."""
    user_input = last_user_text(state)
    base_criteria = None
    if state.get("availability_result"):
        base_criteria = state["availability_result"].get("criteria_snapshot")
    if not base_criteria:
        base_criteria = _base_criteria_from_focus_context(state.get("focus_context"))

    result = query_availability.invoke({"text": user_input, "base_criteria": base_criteria})
    if result.get("success"):
        data = result.get("data", {})
        response_type = "availability_result"
        response_facts = {
            "body": data.get("answer") or "已完成实时排班查询。",
            "criteria": data.get("criteria") or {},
            "available_technician_names": data.get("available_technician_names", []),
        }
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
            "last_answer": response_facts["body"],
        }
    else:
        response_type = "availability_failed"
        response_facts = {"body": f"抱歉，实时排班查询失败：{result.get('error') or result.get('message')}"}
        focus_context = state.get("focus_context")
        availability_result = state.get("availability_result")

    update = {
        "response_type": response_type,
        "response_facts": response_facts,
        "focus_context": focus_context,
        "availability_result": availability_result,
        "tool_results": {"query_availability": result},
    }
    return update


def _base_criteria_from_focus_context(focus_context: dict | None) -> dict | None:
    focus_context = focus_context or {}
    base = {
        "service_type": focus_context.get("service_type"),
        "start_time": focus_context.get("start_time"),
        "duration_minutes": focus_context.get("duration_minutes"),
        "gender": focus_context.get("gender_preference"),
        "technician_name": focus_context.get("technician_name"),
        "preference": focus_context.get("preference"),
    }
    base = {key: value for key, value in base.items() if value not in (None, "", [], {})}
    return base or None


def _availability_options(criteria: dict | None, technician_names: list[str]) -> list[dict]:
    criteria = criteria or {}
    try:
        technicians = AppointmentService().get_all_technicians()
    except Exception:
        technicians = []
    technicians_by_name = {tech.get("name"): tech for tech in technicians if tech.get("name")}
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
