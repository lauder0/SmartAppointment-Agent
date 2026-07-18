"""Recommendation nodes that rank verified available technicians."""

from __future__ import annotations

from typing import Any, Dict

from agents._shared.node_utils import last_user_text, merge_focus_context
from agents._shared.slot_utils import default_duration_for_service
from agents._shared.tool_calling import get_allowed_tools, run_tool_calling_agent
from agents.specialists.result_contract import agent_result
from agents.supervisor.state import SupervisorState, ensure_supervisor_defaults
from tools.recommendation_tools import parse_preference, rank_technicians, recommend_service_item
from tools.technician_read_tools import get_all_technicians

from .memory import recall_preferences
from .state import normalize_recommendation_state


async def recommend_service_node(state: SupervisorState) -> SupervisorState:
    """Recommend a service item from symptoms, need, or preference."""
    state = ensure_supervisor_defaults(state)
    recommendation = normalize_recommendation_state(state.get("recommendation"))
    focus = state.get("shared_focus_context") or {}
    user_text = last_user_text(state)
    tool_result = recommend_service_item.invoke({"user_text": user_text, "focus_context": focus})
    result = tool_result.get("data") or {}
    selected = result.get("selected") or {}
    alternatives = list(result.get("alternatives") or [])

    if not selected:
        body = "我暂时没能判断最适合的服务项目。您可以告诉我主要想缓解哪里不舒服，或想放松、助眠、缓解肩颈/背部。"
        recommendation.update({"status": "waiting_user", "trigger_reason": "service_recommendation_unclear"})
        return {
            "recommendation": recommendation,
            "last_agent_result": agent_result(
                "recommendation",
                "waiting_user",
                "service_recommendation_unclear",
                None,
                {"recommendation": recommendation},
                response_type="service_recommendation",
                facts={"body": body},
                requires_user_input=True,
                next_expected_user_action="provide_symptom_or_need",
            ),
        }

    service_name = selected.get("name")
    duration = selected.get("default_duration_minutes") or default_duration_for_service(service_name)
    recommended_service = {
        "name": service_name,
        "service_type": service_name,
        "description": selected.get("description"),
        "duration_minutes": duration,
        "price_yuan": selected.get("price_yuan"),
        "matched_keywords": selected.get("matched_keywords") or [],
    }
    recommendation.update(
        {
            "status": "completed",
            "selected_service_recommendation": recommended_service,
            "alternative_service_recommendations": alternatives,
            "recommendation_reason": _service_recommendation_reason(recommended_service),
            "trigger_reason": "service_recommendation_requested",
        }
    )
    focus_updates = {
        "service_type": service_name,
        "duration_minutes": duration,
        "recommended_service": recommended_service,
        "symptom_or_need": user_text,
        "last_offer": "service_recommendation",
    }
    focus_context = merge_focus_context(focus, focus_updates, updated_by="recommendation")
    body = _service_recommendation_body(recommended_service, alternatives)
    return {
        "shared_focus_context": focus_context,
        "recommendation": recommendation,
        "tool_results": {
            **(state.get("tool_results") or {}),
            "recommend_service_item": tool_result,
        },
        "last_agent_result": agent_result(
            "recommendation",
            "completed",
            "service_recommended",
            None,
            {"recommendation": recommendation},
            response_type="service_recommendation",
            facts={
                "body": body,
                "recommended_service": recommended_service,
                "alternative_services": alternatives,
                "agent_label": "推荐机器人",
            },
            tool_results={"recommend_service_item": tool_result},
            requires_user_input=True,
            next_expected_user_action="provide_time_or_request_technician_recommendation",
        ),
    }


async def recommend_technician_node(
    state: SupervisorState,
    replace_current: bool = False,
) -> SupervisorState:
    state = ensure_supervisor_defaults(state)
    recommendation = normalize_recommendation_state(state.get("recommendation"))
    availability = state.get("availability") or {}
    focus = state.get("shared_focus_context") or {}
    candidates = list(availability.get("options") or [])

    if not candidates:
        tool_calling_update = await _try_tool_calling_technician_recommendation(
            state=state,
            recommendation=recommendation,
            replace_current=replace_current,
        )
        if tool_calling_update:
            return tool_calling_update

        body = (
            "我还没有可用于推荐的实时排班候选人。请先告诉我想预约的日期、时间和时长，"
            "我查到可约技师后再为您比较推荐。"
        )
        recommendation.update({"status": "needs_availability", "trigger_reason": "no_available_candidates"})
        return _result_update(recommendation, body, "recommendation_needs_availability")

    excluded_ids = list(recommendation.get("excluded_technician_ids") or [])
    current = recommendation.get("selected_recommendation") or {}
    if replace_current and current.get("technician_id") not in (None, ""):
        current_id = int(current["technician_id"])
        if current_id not in excluded_ids:
            excluded_ids.append(current_id)

    current_text = last_user_text(state)
    previous_preference = recommendation.get("preference") or {}
    fallback_preference = (
        str(focus.get("preference") or "")
        or str((availability.get("criteria_snapshot") or {}).get("preference") or "")
        or str(previous_preference.get("raw_text") or "")
    )
    preference = parse_preference(current_text, fallback=fallback_preference)
    recalled = recall_preferences(state)
    service_type = focus.get("service_type") or (availability.get("criteria_snapshot") or {}).get("service_type")

    rank_result = rank_technicians.invoke(
        {
            "candidate_options": candidates,
            "preference": preference,
            "service_type": service_type,
            "recalled_preferences": recalled,
            "excluded_technician_ids": excluded_ids,
        }
    )
    ranked = (rank_result.get("data") or {}).get("ranked") or []
    if not ranked:
        body = "当前可约候选人已经比较完了，没有更多符合条件的技师。您可以调整时间、性别或手法偏好，我再重新查询。"
        recommendation.update(
            {
                "status": "exhausted",
                "excluded_technician_ids": excluded_ids,
                "trigger_reason": "candidate_pool_exhausted",
            }
        )
        return _result_update(recommendation, body, "recommendation_exhausted")

    selected = ranked[0]
    alternatives = ranked[1:3]
    confidence = _recommendation_confidence(ranked)
    reason = _recommendation_reason(selected, preference, service_type)
    body = _recommendation_body(
        selected=selected,
        alternatives=alternatives,
        preference=preference,
        service_type=service_type,
        criteria=availability.get("criteria_snapshot") or {},
        reason=reason,
    )
    response_facts = {
        "body": body,
        "recommended_technician": selected,
        "alternative_technicians": alternatives,
        "criteria": availability.get("criteria_snapshot") or {},
        "preference": preference,
        "agent_label": "推荐机器人",
    }
    recommendation.update(
        {
            "status": "awaiting_selection",
            "recalled_preferences": recalled,
            "candidate_recommendations": ranked,
            "selected_recommendation": selected,
            "alternative_recommendations": alternatives,
            "preference": preference,
            "recommendation_reason": reason,
            "confidence": confidence,
            "excluded_technician_ids": excluded_ids,
            "trigger_reason": "replacement_requested" if replace_current else "user_requested",
        }
    )
    return {
        "recommendation": recommendation,
        "tool_results": {
            **(state.get("tool_results") or {}),
            "rank_technicians": rank_result,
        },
        "last_agent_result": agent_result(
            "recommendation",
            "awaiting_selection",
            "technician_recommended",
            None,
            {"recommendation": recommendation},
            response_type="technician_recommendation",
            facts=response_facts,
            suggested_next_tasks=[
                {
                    "agent": "booking",
                    "action": "select_recommended_technician",
                    "reason": "recommendation_ready_for_selection",
                    "input": {"selected_recommendation": selected},
                    "auto_continue": False,
                    "task_type": "booking_confirmation",
                    "primary_intent": "select_recommended_technician",
                }
            ],
            requires_user_input=True,
            next_expected_user_action="accept_recommendation | choose_alternative | change_preference",
        ),
    }


async def _try_tool_calling_technician_recommendation(
    *,
    state: SupervisorState,
    recommendation: Dict[str, Any],
    replace_current: bool,
) -> SupervisorState | None:
    """Use read-only tools to query availability and rank candidates when possible."""
    action = "replace_recommendation" if replace_current else "generate_recommendation"
    user_text = last_user_text(state)
    focus = state.get("shared_focus_context") or {}
    result = await run_tool_calling_agent(
        agent_name="recommendation",
        action=action,
        state=state,
        prompt=_recommendation_tool_prompt(user_text, focus, state.get("availability") or {}),
        allowed_tools=get_allowed_tools("recommendation", action),
        system_prompt=(
            "You are the technician recommendation specialist. Use only read-only tools. "
            "If availability candidates are missing, query availability first, then rank technicians. "
            "Never create appointments."
        ),
    )
    ranked = _ranked_from_tool_calling(result)
    if not ranked:
        ranked = _rank_from_availability_tool_results(result, state, focus)
    if not result.get("success") or not ranked:
        return None

    preference = parse_preference(user_text, fallback=str(focus.get("preference") or ""))
    service_type = focus.get("service_type")
    criteria = _availability_criteria_from_tool_calling(result)
    selected = ranked[0]
    alternatives = ranked[1:3]
    reason = _recommendation_reason(selected, preference, service_type)
    body = _recommendation_body(
        selected=selected,
        alternatives=alternatives,
        preference=preference,
        service_type=service_type,
        criteria=criteria,
        reason=reason,
    )
    recommendation.update(
        {
            "status": "awaiting_selection",
            "candidate_recommendations": ranked,
            "selected_recommendation": selected,
            "alternative_recommendations": alternatives,
            "preference": preference,
            "recommendation_reason": reason,
            "confidence": _recommendation_confidence(ranked),
            "trigger_reason": "tool_calling_recommendation",
        }
    )
    response_facts = {
        "body": body,
        "recommended_technician": selected,
        "alternative_technicians": alternatives,
        "criteria": criteria,
        "preference": preference,
    }
    return {
        "recommendation": recommendation,
        "tool_results": {
            **(state.get("tool_results") or {}),
            "recommendation_tool_calling": result,
            **(result.get("tool_results") or {}),
        },
        "last_agent_result": agent_result(
            "recommendation",
            "awaiting_selection",
            "technician_recommended",
            None,
            {"recommendation": recommendation},
            response_type="technician_recommendation",
            facts=response_facts,
            suggested_next_tasks=[
                {
                    "agent": "booking",
                    "action": "select_recommended_technician",
                    "reason": "recommendation_ready_for_selection",
                    "input": {"selected_recommendation": selected},
                    "auto_continue": False,
                    "task_type": "booking_confirmation",
                    "primary_intent": "select_recommended_technician",
                }
            ],
            requires_user_input=True,
            next_expected_user_action="accept_recommendation | choose_alternative | change_preference",
        ),
    }


def _recommendation_tool_prompt(user_text: str, focus: Dict[str, Any], availability: Dict[str, Any]) -> str:
    return (
        "User request:\n"
        f"{user_text}\n\n"
        "Shared focus context:\n"
        f"{focus}\n\n"
        "Current availability state:\n"
        f"{availability}\n\n"
        "Task:\n"
        "- Recommend a technician only from verified availability candidates.\n"
        "- If current availability has no options but the user/context includes enough time information, call query_availability first.\n"
        "- Call recall_preferences and rank_technicians when candidates are available.\n"
        "- Return a concise Chinese recommendation. Do not create appointments."
    )


def _ranked_from_tool_calling(result: Dict[str, Any]) -> list[Dict[str, Any]]:
    tool_results = result.get("tool_results") or {}
    rank_result = tool_results.get("rank_technicians") or {}
    ranked = (rank_result.get("data") or {}).get("ranked") or []
    return list(ranked) if isinstance(ranked, list) else []


def _rank_from_availability_tool_results(
    result: Dict[str, Any],
    state: SupervisorState,
    focus: Dict[str, Any],
) -> list[Dict[str, Any]]:
    """Deterministically bridge availability tool output into ranking input."""
    tool_results = result.setdefault("tool_results", {})
    availability_result = tool_results.get("query_availability") or {}
    availability_data = availability_result.get("data") or {}
    names = availability_data.get("available_technician_names") or []
    if not names:
        return []

    all_technicians_result = tool_results.get("get_all_technicians")
    if not all_technicians_result:
        all_technicians_result = get_all_technicians.invoke({})
        tool_results["get_all_technicians"] = all_technicians_result
    technicians = (all_technicians_result.get("data") or {}).get("technicians") or []
    technicians_by_name = {technician.get("name"): technician for technician in technicians if technician.get("name")}
    criteria = availability_data.get("criteria") or {}
    candidates = []
    for index, name in enumerate(names, start=1):
        technician = technicians_by_name.get(name) or {}
        candidates.append(
            {
                "option_id": f"tool_opt_{index}",
                "technician_id": technician.get("id"),
                "technician_name": name,
                "gender": technician.get("gender"),
                "strength": technician.get("strength"),
                "start_time": criteria.get("start_time"),
                "duration_minutes": criteria.get("duration_minutes"),
                "service_type": criteria.get("service_type"),
                "gender_preference": criteria.get("gender"),
                "preference": criteria.get("preference"),
            }
        )

    preference = parse_preference(last_user_text(state), fallback=str(focus.get("preference") or ""))
    rank_result = rank_technicians.invoke(
        {
            "candidate_options": candidates,
            "preference": preference,
            "service_type": focus.get("service_type") or criteria.get("service_type"),
            "recalled_preferences": recall_preferences(state),
            "excluded_technician_ids": (state.get("recommendation") or {}).get("excluded_technician_ids") or [],
        }
    )
    tool_results["rank_technicians"] = rank_result
    ranked = (rank_result.get("data") or {}).get("ranked") or []
    return list(ranked) if isinstance(ranked, list) else []


def _availability_criteria_from_tool_calling(result: Dict[str, Any]) -> Dict[str, Any]:
    tool_results = result.get("tool_results") or {}
    availability_result = tool_results.get("query_availability") or {}
    return (availability_result.get("data") or {}).get("criteria") or {}


def _result_update(recommendation: Dict[str, Any], body: str, result_type: str) -> SupervisorState:
    response_facts = {"body": body}
    return {
        "recommendation": recommendation,
        "last_agent_result": agent_result(
            "recommendation",
            recommendation.get("status", "unknown"),
            result_type,
            None,
            {"recommendation": recommendation},
            response_type="technician_recommendation_failed",
            facts=response_facts,
        ),
    }


def _service_recommendation_reason(service: Dict[str, Any]) -> str:
    matched = service.get("matched_keywords") or []
    if matched:
        return "、".join(str(item) for item in matched[:3])
    description = service.get("description")
    if description:
        return str(description)
    return "更贴合您当前描述的需求"


def _service_recommendation_body(selected: Dict[str, Any], alternatives: list[Dict[str, Any]]) -> str:
    name = selected.get("name") or selected.get("service_type")
    duration = selected.get("duration_minutes")
    price = selected.get("price_yuan")
    reason = _service_recommendation_reason(selected)
    parts = [f"针对您的需求，我更推荐{name}。"]
    if duration:
        parts.append(f"时长约 {duration} 分钟。")
    if price:
        parts.append(f"价格 {price} 元。")
    parts.append(f"推荐理由：{reason}。")
    if alternatives:
        names = "、".join(str(item.get("name")) for item in alternatives if item.get("name"))
        if names:
            parts.append(f"备选项目可以考虑：{names}。")
    parts.append("如果您想预约这个项目，可以继续告诉我时间；如果还想推荐技师，也可以直接说“帮我推荐技师”。")
    return "".join(parts)


def _recommendation_confidence(ranked: list[Dict[str, Any]]) -> float:
    top_score = float(ranked[0].get("score") or 0.0)
    margin = top_score - float(ranked[1].get("score") or 0.0) if len(ranked) > 1 else 0.15
    return round(min(1.0, max(0.0, top_score * 0.8 + max(0.0, margin) * 0.2)), 4)


def _recommendation_reason(selected: Dict[str, Any], preference: Dict[str, Any], service_type: str | None) -> str:
    features = selected.get("matched_features") or []
    if features:
        return "、".join(str(item) for item in features[:3])
    profile_label = preference.get("profile_label")
    if profile_label:
        return f"在当前可约候选中与“{profile_label}”偏好相对更接近"
    if service_type:
        return f"在当前可约候选中更适合{service_type}"
    return "综合当前可约情况和技师专长排序更靠前"


def _recommendation_body(
    selected: Dict[str, Any],
    alternatives: list[Dict[str, Any]],
    preference: Dict[str, Any],
    service_type: str | None,
    criteria: Dict[str, Any],
    reason: str,
) -> str:
    name = selected.get("technician_name")
    time_text = criteria.get("start_time")
    duration = criteria.get("duration_minutes")
    preference_text = preference.get("profile_label") or preference.get("raw_text")
    intro = f"结合您希望{preference_text}的偏好，" if preference_text else "结合您的需求，"
    details = f"我更推荐{name}技师，主要匹配点是：{reason}。"
    schedule = ""
    if time_text:
        schedule = f"该技师在 {time_text}"
        if duration:
            schedule += f" 起可预约 {duration} 分钟"
        schedule += "。"
    alternative_text = ""
    if alternatives:
        alternative_names = "、".join(str(item.get("technician_name")) for item in alternatives if item.get("technician_name"))
        if alternative_names:
            alternative_text = f"备选可以考虑：{alternative_names}。"
    service_text = f"服务项目按{service_type}考虑。" if service_type else ""
    return (
        f"{intro}{details}{schedule}{service_text}{alternative_text}"
        "如果您接受这位推荐，请回复“就好/他吧”或“确认选择”；不满意可以说“换一个”。"
    )
