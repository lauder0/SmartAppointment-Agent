"""Recommendation nodes that rank verified available technicians."""

from __future__ import annotations

from typing import Any, Dict

from langchain_core.messages import AIMessage

from agents.shared.node_utils import last_user_text
from agents.shared.response_composer import composer
from agents.specialists.common import agent_result
from agents.supervisor.state import SupervisorState, ensure_supervisor_defaults
from services.technician_recommendation_service import (
    TechnicianRecommendationService,
    parse_recommendation_preference,
)

from .memory import recall_preferences
from .state import normalize_recommendation_state


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
        reply = composer.reply(
            "technician_recommendation_failed",
            {
                "body": (
                    "我还没有可用于推荐的实时排班候选人。请先告诉我想预约的日期、时间和时长，"
                    "我查到可约技师后再为您比较推荐。"
                )
            },
        )
        recommendation.update(
            {
                "status": "needs_availability",
                "trigger_reason": "no_available_candidates",
            }
        )
        return _result_update(recommendation, reply, "recommendation_needs_availability")

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
    preference = parse_recommendation_preference(current_text, fallback=fallback_preference)
    recalled = recall_preferences(state)
    service_type = (
        focus.get("service_type")
        or (availability.get("criteria_snapshot") or {}).get("service_type")
    )

    ranked = TechnicianRecommendationService().rank(
        candidate_options=candidates,
        preference=preference,
        service_type=service_type,
        recalled_preferences=recalled,
        excluded_technician_ids=excluded_ids,
    )
    if not ranked:
        reply = composer.reply(
            "technician_recommendation_failed",
            {
                "body": (
                    "当前可约候选人已经比较完了，没有更多符合条件的技师。"
                    "您可以调整时间、性别或手法偏好，我再重新查询。"
                )
            },
        )
        recommendation.update(
            {
                "status": "exhausted",
                "excluded_technician_ids": excluded_ids,
                "trigger_reason": "candidate_pool_exhausted",
            }
        )
        return _result_update(recommendation, reply, "recommendation_exhausted")

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
    reply = await composer.areply(
        "technician_recommendation",
        {
            "body": body,
            "recommended_technician": selected,
            "alternative_technicians": alternatives,
            "criteria": availability.get("criteria_snapshot") or {},
            "preference": preference,
            "agent_label": "推荐机器人",
        },
        {"user_input": current_text},
    )
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
        "final_response": reply,
        "messages": [AIMessage(content=reply)],
        "tool_results": {
            **(state.get("tool_results") or {}),
            "technician_recommendation": {
                "success": True,
                "selected": selected,
                "alternatives": alternatives,
                "confidence": confidence,
            },
        },
        "last_agent_result": agent_result(
            "recommendation",
            "awaiting_selection",
            "technician_recommended",
            reply,
            {"recommendation": recommendation},
            {
                "target_agent": "booking",
                "reason": "recommendation_ready_for_selection",
                "payload": {"selected_recommendation": selected},
            },
        ),
    }


def _result_update(
    recommendation: Dict[str, Any],
    reply: str,
    result_type: str,
) -> SupervisorState:
    return {
        "recommendation": recommendation,
        "final_response": reply,
        "messages": [AIMessage(content=reply)],
        "last_agent_result": agent_result(
            "recommendation",
            recommendation.get("status", "unknown"),
            result_type,
            reply,
            {"recommendation": recommendation},
        ),
    }


def _recommendation_confidence(ranked: list[Dict[str, Any]]) -> float:
    top_score = float(ranked[0].get("score") or 0.0)
    margin = top_score - float(ranked[1].get("score") or 0.0) if len(ranked) > 1 else 0.15
    return round(min(1.0, max(0.0, top_score * 0.8 + max(0.0, margin) * 0.2)), 4)


def _recommendation_reason(
    selected: Dict[str, Any],
    preference: Dict[str, Any],
    service_type: str | None,
) -> str:
    features = selected.get("matched_features") or []
    if features:
        return "、".join(features[:3])
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
        alternative_names = "、".join(str(item.get("technician_name")) for item in alternatives)
        alternative_text = f"备选可以考虑：{alternative_names}。"
    service_text = f"服务项目按{service_type}考虑。" if service_type else ""
    return (
        f"{intro}{details}{schedule}{service_text}{alternative_text}"
        "如果您接受这位推荐，请回复“就她/他吧”或“确认选择”；不满意可以说“换一个”。"
    )
