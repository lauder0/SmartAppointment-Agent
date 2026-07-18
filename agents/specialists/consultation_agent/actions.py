"""Consultation and availability graph nodes."""

from __future__ import annotations

from config.model_provider import create_chat_model
from agents._shared.tool_calling import get_allowed_tools, run_tool_calling_agent
from agents.understander.rules import (
    is_appointment_policy_question,
    is_business_hours_question,
    is_contact_question,
    is_location_question,
    is_membership_question,
    is_price_question,
    is_service_catalog_question,
    is_service_detail_question,
    is_service_recommendation_request,
    is_technician_info_question,
)
from agents.specialists.consultation_agent.response_generator import ResponseGenerator
from agents._shared.node_utils import (
    last_user_text,
    merge_focus_context,
)
from agents._shared.slot_utils import default_duration_for_service
from agents._shared.state import AgentState
from tools.knowledge_tools import search_knowledge


async def knowledge_consult_node(state: AgentState) -> AgentState:
    """Handle static knowledge-base consultation."""
    user_input = last_user_text(state)
    if is_service_catalog_question(user_input):
        focus_context = merge_focus_context(state.get("focus_context"), {"last_offer": "service_catalog"})
        return {
            "response_type": "service_catalog",
            "response_facts": {},
            "focus_context": focus_context,
        }

    static_answer = _static_template_answer(user_input)
    if static_answer:
        focus_updates = _static_focus_updates(user_input)
        update = {
            "response_type": "knowledge_answer",
            "response_facts": {"answer": static_answer},
            "tool_results": {"static_knowledge_template": {"success": True, "reason": "deterministic_static_answer"}},
        }
        if focus_updates:
            update["focus_context"] = merge_focus_context(state.get("focus_context"), focus_updates)
        return update

    tool_calling_update = await _try_consultation_tool_calling(state, user_input)
    if tool_calling_update:
        return tool_calling_update

    result = await search_knowledge.ainvoke({"query": user_input, "top_k": 3})
    docs = []
    if result.get("success"):
        docs = result.get("data", {}).get("documents", [])

    generator = ResponseGenerator(create_chat_model(temperature=0.3))
    answer = await generator.generate_response(user_input, docs)
    focus_updates = _service_recommendation_focus_updates(user_input, answer, state)
    update = {
        "response_type": "knowledge_answer",
        "response_facts": {"answer": answer},
        "tool_results": {"search_knowledge": result},
    }
    if focus_updates:
        update["focus_context"] = merge_focus_context(state.get("focus_context"), focus_updates)
    return update


async def _try_consultation_tool_calling(state: AgentState, user_input: str) -> AgentState | None:
    """Let the consultation agent choose among read-only tools for open questions."""
    prompt = _consultation_tool_prompt(user_input, state)
    result = await run_tool_calling_agent(
        agent_name="consultation",
        action="answer_knowledge",
        state=state,
        prompt=prompt,
        allowed_tools=get_allowed_tools("consultation", "answer_knowledge"),
        system_prompt=(
            "You are the consultation specialist in a massage-shop appointment system. "
            "Use only the provided tools when facts are needed. Do not claim a booking "
            "has been created. Do not call or request write-side tools. Answer in concise Chinese."
        ),
    )
    answer = (result.get("answer") or "").strip()
    if not result.get("success") or not answer:
        return None

    focus_updates = _service_recommendation_focus_updates(user_input, answer, state)
    update: AgentState = {
        "response_type": "knowledge_answer",
        "response_facts": {
            "answer": answer,
            "tool_calling": True,
        },
        "tool_results": {
            **(state.get("tool_results") or {}),
            "consultation_tool_calling": result,
            **(result.get("tool_results") or {}),
        },
    }
    if focus_updates:
        update["focus_context"] = merge_focus_context(state.get("focus_context"), focus_updates)
    return update


def _consultation_tool_prompt(user_input: str, state: AgentState) -> str:
    focus = state.get("focus_context") or {}
    return (
        "User question:\n"
        f"{user_input}\n\n"
        "Shared focus context:\n"
        f"{focus}\n\n"
        "Task:\n"
        "- Answer the user's consultation question for the massage shop.\n"
        "- If the question asks for services, prices, policies, address, hours, or project details, search knowledge.\n"
        "- If the question asks for technicians, use technician read tools.\n"
        "- If the user describes symptoms or a need and asks what to choose, use service recommendation.\n"
        "- Return only the final user-facing Chinese answer, without JSON and without [REPLY] prefix."
    )


def _static_focus_updates(user_input: str) -> dict:
    service_type = _infer_service_from_text(user_input)
    if not service_type:
        return {}
    updates = {
        "service_type": service_type,
        "last_offer": "service_detail",
    }
    duration = default_duration_for_service(service_type)
    if duration:
        updates["duration_minutes"] = duration
    return updates


def _static_template_answer(user_input: str) -> str | None:
    """Return deterministic answers for stable store FAQ topics."""
    if is_appointment_policy_question(user_input):
        return (
            "可以的。若临时有事，建议您尽量提前联系门店取消或更改预约时间，"
            "这样方便我们重新安排技师和时段。若已临近预约时间，也可以直接告诉我"
            "要取消、改时间或换技师，我会根据当前预约状态继续处理。"
        )
    if is_business_hours_question(user_input):
        return "我们门店营业时间为每天 10:00-22:00。您可以预约未来 7 个自然日内的可用时段。"
    if is_location_question(user_input):
        return (
            "我们门店位于北京海淀区中关村大街27号。您可以乘地铁至中关村站，"
            "从 A 口出站后向北步行约 300 米；自驾可使用附近商场地下停车场。"
        )
    if is_contact_question(user_input):
        return "您可以通过门店前台电话或到店咨询联系我们。若要预约，也可以直接告诉我时间、项目和技师偏好。"
    if is_membership_question(user_input):
        return "目前会员可关注充值、次卡和阶段活动优惠，具体折扣以门店当期公示为准。您也可以告诉我想做的项目，我帮您继续查询或预约。"
    if is_price_question(user_input):
        return (
            "当前主要项目价格为：全身推拿120元/60分钟，肩颈推拿80元/30分钟，"
            "足底按摩100元/45分钟，背部推拿90元/40分钟。"
        )
    if is_service_detail_question(user_input):
        return (
            "全身推拿适合整体放松和缓解疲劳；肩颈推拿适合久坐、伏案后的肩颈僵硬；"
            "足底按摩偏助眠减压；背部推拿适合腰背酸痛和背部紧张。"
        )
    if is_technician_info_question(user_input):
        return "我们有多位技师可提供服务。若您告诉我预约时间、项目、时长或性别/手法偏好，我可以实时查询可约技师并继续推荐。"
    return None

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
        ("全身推拿", ("全身", "疲劳", "放松", "累")),
    )
    for service_type, keywords in symptom_rules:
        if any(keyword in text for keyword in keywords):
            return service_type
    return None
