"""Central response composition for graph nodes.

Workflow nodes produce facts; this module turns those facts into user-facing
messages. High-risk booking messages stay template-first so key fields remain
stable, while low-risk explanatory responses can later opt into LLM wording.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

from config.model_provider import create_chat_model


ResponseFacts = Dict[str, Any]


RESPONSE_POLICY: Dict[str, str] = {
    "knowledge_answer": "llm",
    "service_catalog": "template_required",
    "availability_result": "llm_optional",
    "availability_failed": "template_required",
    "booking_missing_slots": "template_required",
    "booking_confirmation": "template_required",
    "booking_recommendation": "llm_optional",
    "booking_cancelled": "template_required",
    "booking_unclear_confirmation": "template_required",
    "booking_guard_missing": "template_required",
    "booking_guard_invalid": "template_required",
    "booking_guard_time_invalid": "template_required",
    "booking_guard_technician_unavailable": "template_required",
    "booking_success": "template_required",
    "booking_failed": "llm_optional",
    "technician_recommendation": "llm_optional",
    "technician_recommendation_failed": "template_required",
    "greeting": "template_required",
    "courtesy": "template_required",
    "unsupported": "template_required",
    "clarification": "template_required",
}


@dataclass(frozen=True)
class ComposedResponse:
    """A rendered reply plus metadata for auditing or future evals."""

    response_type: str
    policy: str
    agent_label: str
    body: str
    reply: str


class ResponseComposer:
    """Render user-facing replies from structured facts."""

    def __init__(self, enable_llm: bool = False):
        self.enable_llm = enable_llm

    def compose(
        self,
        response_type: str,
        facts: ResponseFacts | None = None,
        context: ResponseFacts | None = None,
    ) -> ComposedResponse:
        facts = facts or {}
        context = context or {}
        policy = RESPONSE_POLICY.get(response_type, "template_required")
        agent_label = facts.get("agent_label") or self._default_agent(response_type)

        body = self._template_body(response_type, facts, context)
        body = self._validate_required_text(response_type, body, facts)
        reply = self._with_prefix(agent_label, body)
        return ComposedResponse(
            response_type=response_type,
            policy=policy,
            agent_label=agent_label,
            body=body,
            reply=reply,
        )

    def reply(
        self,
        response_type: str,
        facts: ResponseFacts | None = None,
        context: ResponseFacts | None = None,
    ) -> str:
        return self.compose(response_type, facts, context).reply

    async def acompose(
        self,
        response_type: str,
        facts: ResponseFacts | None = None,
        context: ResponseFacts | None = None,
    ) -> ComposedResponse:
        facts = facts or {}
        context = context or {}
        policy = RESPONSE_POLICY.get(response_type, "template_required")
        agent_label = facts.get("agent_label") or self._default_agent(response_type)
        template_body = self._template_body(response_type, facts, context)

        body = template_body
        if self.enable_llm and policy in {"llm", "llm_optional"}:
            llm_body = await self._try_llm_body(response_type, template_body, facts, context)
            if llm_body and self._llm_body_is_valid(response_type, llm_body, facts):
                body = llm_body

        body = self._validate_required_text(response_type, body, {**facts, "fallback_body": template_body})
        reply = self._with_prefix(agent_label, body)
        return ComposedResponse(
            response_type=response_type,
            policy=policy,
            agent_label=agent_label,
            body=body,
            reply=reply,
        )

    async def areply(
        self,
        response_type: str,
        facts: ResponseFacts | None = None,
        context: ResponseFacts | None = None,
    ) -> str:
        return (await self.acompose(response_type, facts, context)).reply

    def _template_body(
        self,
        response_type: str,
        facts: ResponseFacts,
        context: ResponseFacts,
    ) -> str:
        template = _TEMPLATES.get(response_type)
        if template:
            return template(facts, context)
        return str(facts.get("body") or facts.get("message") or "")

    def _default_agent(self, response_type: str) -> str:
        if response_type.startswith("booking_"):
            return "预约机器人"
        if response_type.startswith("technician_recommendation"):
            return "推荐机器人"
        if response_type in {"greeting", "courtesy", "unsupported", "clarification"}:
            return "咨询机器人"
        return "咨询机器人"

    def _with_prefix(self, agent_label: str, body: str) -> str:
        body = body or ""
        if body.startswith("[REPLY]"):
            return body
        return f"[REPLY][{agent_label}]{body}"

    async def _try_llm_body(
        self,
        response_type: str,
        template_body: str,
        facts: ResponseFacts,
        context: ResponseFacts,
    ) -> str | None:
        prompt = self._llm_prompt(response_type, template_body, facts, context)
        try:
            message = await create_chat_model(temperature=0.2).ainvoke(prompt)
        except Exception:
            return None
        return self._clean_llm_body(str(getattr(message, "content", "") or ""))

    def _llm_prompt(
        self,
        response_type: str,
        template_body: str,
        facts: ResponseFacts,
        context: ResponseFacts,
    ) -> str:
        return f"""
你是按摩门店智能预约系统的表达层。请把结构化事实改写成自然、简洁、专业的中文回复。

要求：
- 只能使用 facts/template 中已有事实，不要编造技师、时间、价格、项目或预约结果。
- 不要输出 [REPLY] 或机器人标签，系统会自动添加。
- 不要说已经预约成功，除非 template 明确包含预约成功。
- 如果是排班结果，保留时间、时长、性别偏好和至少一位可约技师名称。
- 如果是技师推荐，保留推荐技师名称，并说明仍需用户确认。
- 如果是失败解释，给出可执行下一步，例如换时间、换技师或调整偏好。

response_type: {response_type}
facts: {facts}
context: {context}
template:
{template_body}
""".strip()

    def _clean_llm_body(self, body: str) -> str:
        cleaned = body.strip()
        for prefix in ("[REPLY][咨询机器人]", "[REPLY][预约机器人]", "[咨询机器人]", "[预约机器人]"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        return cleaned

    def _llm_body_is_valid(
        self,
        response_type: str,
        body: str,
        facts: ResponseFacts,
    ) -> bool:
        if not body:
            return False
        if "预约成功" in body and response_type != "booking_success":
            return False

        required = []
        if response_type == "availability_result":
            criteria = facts.get("criteria") or {}
            start_time = criteria.get("start_time")
            if start_time:
                required.append(str(start_time)[-5:])
            names = facts.get("available_technician_names") or []
            if names and not any(str(name) in body for name in names[:5]):
                return False
        elif response_type == "booking_recommendation":
            recommended = facts.get("recommended_technician") or {}
            name = recommended.get("name") or recommended.get("technician_name")
            if name:
                required.append(str(name))
        elif response_type == "technician_recommendation":
            recommended = facts.get("recommended_technician") or {}
            name = recommended.get("name") or recommended.get("technician_name")
            if name:
                required.append(str(name))

        return all(item in body for item in required)

    def _validate_required_text(
        self,
        response_type: str,
        body: str,
        facts: ResponseFacts,
    ) -> str:
        required = []
        if response_type == "booking_confirmation":
            required = ["时间：", "项目：", "时长：", "技师：", "请问是否确认预约"]
        elif response_type == "booking_success":
            required = ["预约成功", "时间：", "项目：", "时长："]

        if required and not all(item in body for item in required):
            fallback = facts.get("fallback_body")
            if fallback:
                return str(fallback)
        return body


def service_catalog_body(_: ResponseFacts, __: ResponseFacts) -> str:
    return (
        "您好！我们目前提供以下几项专业推拿服务：\n"
        "✅ 全身推拿（120元/60分钟）——舒缓全身疲劳，调理气血循环；\n"
        "✅ 肩颈推拿（80元/30分钟）——专注缓解久坐、伏案引起的僵硬与酸痛；\n"
        "✅ 足底按摩（100元/45分钟）——刺激足部反射区，助眠减压、改善代谢；\n"
        "✅ 背部推拿（90元/40分钟）——放松脊柱两侧肌肉，缓解背部紧张与不适。\n\n"
        "您可以继续告诉我想做的项目、时间、时长或技师偏好，我会继续帮您筛选可约技师。"
    )


def raw_body(facts: ResponseFacts, _: ResponseFacts) -> str:
    return str(facts.get("body") or facts.get("answer") or facts.get("message") or "")


def booking_confirmation_body(facts: ResponseFacts, _: ResponseFacts) -> str:
    return (
        "\n我帮您整理一下预约信息：\n"
        f"时间：{facts.get('time_line')}\n"
        f"项目：{facts.get('service_type')}\n"
        f"时长：{facts.get('duration_minutes')}分钟\n"
        f"技师：{facts.get('technician_name')}\n"
        "请问是否确认预约？\n"
    )


def booking_cancelled_body(_: ResponseFacts, __: ResponseFacts) -> str:
    return "好的，已取消这次待确认的预约。您可以继续咨询服务，或重新指定想预约的时间、项目和技师偏好。"


def booking_unclear_confirmation_body(_: ResponseFacts, __: ResponseFacts) -> str:
    return "请您明确回复“确认”或“取消”。如果需要调整，也可以直接告诉我新的时间、项目或技师。"


def booking_guard_missing_body(_: ResponseFacts, __: ResponseFacts) -> str:
    return "为了保证预约准确，我还不能直接创建这条预约。请补充或重新确认预约时间、项目、时长和技师。"


def booking_guard_invalid_body(_: ResponseFacts, __: ResponseFacts) -> str:
    return "预约时间、时长或技师信息不够明确，请重新告诉我。"


def booking_guard_time_invalid_body(facts: ResponseFacts, _: ResponseFacts) -> str:
    return (
        f"目前只能预约未来 {facts.get('booking_window_days')} 个自然日内的时间，"
        f"营业时间为 {facts.get('business_start')}:00-{facts.get('business_end')}:00，"
        "且今天只能预约当前时间之后的剩余时段。请换一个时间。"
    )


def booking_guard_technician_unavailable_body(_: ResponseFacts, __: ResponseFacts) -> str:
    return "抱歉，这个技师在刚才确认的时间段已经不可约了。请换一个时间或技师，我会重新为您匹配。"


def booking_success_body(facts: ResponseFacts, _: ResponseFacts) -> str:
    return (
        f"\n机器人：已为您预约技师：{facts.get('technician_name')}。预约成功！"
        f"预约信息：时间：{facts.get('start_time')}-{facts.get('end_time_text')}，"
        f"项目：{facts.get('service_type')}，时长：{facts.get('duration_minutes')}分钟。\n"
    )


def greeting_body(facts: ResponseFacts, _: ResponseFacts) -> str:
    if facts.get("booking_pending"):
        return (
            "您好，当前有一条预约信息正在等待您确认。"
            "如果要继续预约，请回复“确认”；如果需要调整，请告诉我想修改的时间、项目或技师。"
        )
    return "您好，我是智能预约助手。您可以咨询服务项目、价格、营业时间，或告诉我想查询/预约的时间。"


def courtesy_body(facts: ResponseFacts, _: ResponseFacts) -> str:
    if facts.get("booking_pending"):
        return "不客气。当前还有一条预约信息等待确认；如果要继续预约，请回复“确认”，需要调整也可以直接告诉我。"
    return "不客气，您可以继续咨询服务项目、价格、排班，或告诉我想预约的时间。"


def unsupported_body(_: ResponseFacts, __: ResponseFacts) -> str:
    return (
        "这个问题我不太适合深入处理。我主要可以帮您查询门店服务项目、价格、营业时间、实时排班，"
        "也可以帮您整理预约信息。您想了解哪一项？"
    )


def clarification_body(facts: ResponseFacts, _: ResponseFacts) -> str:
    if facts.get("booking_active"):
        return "我需要再确认一下您的预约需求。请告诉我想调整或补充的是时间、项目、时长还是技师偏好。"
    return "我可以帮您查询服务项目、价格、营业时间、实时排班，也可以帮您预约。请告诉我您想咨询什么，或希望预约的时间、项目和技师偏好。"


_TEMPLATES: Dict[str, Callable[[ResponseFacts, ResponseFacts], str]] = {
    "knowledge_answer": raw_body,
    "service_catalog": service_catalog_body,
    "availability_result": raw_body,
    "availability_failed": raw_body,
    "booking_missing_slots": raw_body,
    "booking_confirmation": booking_confirmation_body,
    "booking_recommendation": raw_body,
    "booking_cancelled": booking_cancelled_body,
    "booking_unclear_confirmation": booking_unclear_confirmation_body,
    "booking_guard_missing": booking_guard_missing_body,
    "booking_guard_invalid": booking_guard_invalid_body,
    "booking_guard_time_invalid": booking_guard_time_invalid_body,
    "booking_guard_technician_unavailable": booking_guard_technician_unavailable_body,
    "booking_success": booking_success_body,
    "booking_failed": raw_body,
    "technician_recommendation": raw_body,
    "technician_recommendation_failed": raw_body,
    "greeting": greeting_body,
    "courtesy": courtesy_body,
    "unsupported": unsupported_body,
    "clarification": clarification_body,
}


composer = ResponseComposer(enable_llm=True)
