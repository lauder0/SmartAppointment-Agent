"""Deterministic context rules used before the LLM router.

These helpers answer "what does this utterance mean in the current state?"
They intentionally handle stable business expressions and leave fuzzy cases to
the existing LLM classifier.
"""

from __future__ import annotations

import re

from services.availability_service import AvailabilityIntent, AvailabilityService


GREETING_TERMS = {"你好", "您好", "嗨", "hi", "hello", "hey", "哈喽", "在吗", "您好呀", "你好呀"}
COURTESY_TERMS = {"谢谢", "感谢", "多谢", "好的谢谢", "谢谢你", "先这样", "我先看看", "好的我看看"}

KNOWLEDGE_KEYWORDS = [
    "有哪些服务",
    "有什么服务",
    "服务项目",
    "项目介绍",
    "价格",
    "多少钱",
    "收费",
    "营业时间",
    "几点开门",
    "地址",
    "在哪里",
    "会员",
    "优惠",
    "怎么预约",
    "预约流程",
    "技师介绍",
]

SERVICE_SELECTION_KEYWORDS = ["想做", "我要", "我想", "选", "做这个", "就这个"]
SCOPE_KEYWORDS = ["你能做什么", "你会做什么", "能做什么", "会做什么", "能干什么", "你有什么功能"]


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text.strip().lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def is_greeting(text: str) -> bool:
    """Return True for pure greeting utterances, including greeting combinations."""
    normalized = _compact_text(text)
    if normalized in GREETING_TERMS:
        return True
    remaining = normalized
    for greeting in sorted(GREETING_TERMS, key=len, reverse=True):
        remaining = remaining.replace(greeting, "")
    return normalized != "" and remaining == ""


def is_courtesy(text: str) -> bool:
    normalized = _compact_text(text)
    if normalized in COURTESY_TERMS:
        return True
    courtesy_signals = ["谢谢", "感谢", "多谢"]
    closing_signals = ["先看看", "我看看", "先这样", "了解一下", "再说"]
    return any(signal in normalized for signal in courtesy_signals) and (
        len(normalized) <= 12 or any(signal in normalized for signal in closing_signals)
    )


def is_knowledge_question(text: str) -> bool:
    return any(keyword in text for keyword in KNOWLEDGE_KEYWORDS)


def is_scope_question(text: str) -> bool:
    normalized = text.strip()
    return any(keyword in normalized for keyword in SCOPE_KEYWORDS)


def is_formal_booking_request(text: str) -> bool:
    return AvailabilityService.is_formal_booking_request(text)


def is_modification_request(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    modification_keywords = [
        "改成",
        "改到",
        "换成",
        "换到",
        "换一个",
        "换个",
        "换技师",
        "改一下",
        "换时间",
        "改时间",
        "重新选",
        "重新推荐",
    ]
    if any(keyword in normalized for keyword in modification_keywords):
        return True
    service = AvailabilityService.parse_service_type(normalized)
    criteria = AvailabilityService().parse_query_criteria(normalized)
    return bool(
        service
        or criteria.get("duration_minutes")
        or criteria.get("gender")
        or criteria.get("technician_name")
        or criteria.get("preference")
        or criteria.get("start_time")
    )


def is_technician_replacement_request(text: str) -> bool:
    normalized = re.sub(r"[\s，。！？!,.、]+", "", text.strip().lower())
    if not normalized:
        return False
    replacement_phrases = [
        "换一个技师",
        "换个技师",
        "换一位技师",
        "换位技师",
        "换技师",
        "更换技师",
        "重新推荐技师",
        "重新选技师",
        "换一个师傅",
        "换个师傅",
        "换一位师傅",
    ]
    if any(phrase in normalized for phrase in replacement_phrases):
        return True
    return normalized.startswith("换") and ("技师" in normalized or "师傅" in normalized)


def is_clear_appointment_start(text: str) -> bool:
    return AvailabilityService.is_clear_appointment_start(text)


def is_availability_refinement(text: str) -> bool:
    return AvailabilityService().is_availability_follow_up(text)


def is_service_selection_after_catalog(text: str) -> bool:
    service_type = AvailabilityService.parse_service_type(text)
    return bool(service_type and any(keyword in text for keyword in SERVICE_SELECTION_KEYWORDS))


def is_positive_confirmation(text: str) -> bool:
    normalized = re.sub(r"[\s，。！？!,.、]+", "", text.strip().lower())
    positive_phrases = {
        "是",
        "好",
        "好的",
        "可以",
        "行",
        "没问题",
        "同意",
        "确定",
        "确认",
        "确认预约",
        "就这个",
        "帮我约吧",
        "帮我预约吧",
        "yes",
        "ok",
    }
    return normalized in positive_phrases


def is_negative_confirmation(text: str) -> bool:
    normalized = re.sub(r"[\s，。！？!,.、]+", "", text.strip().lower())
    negative_phrases = {
        "不",
        "不要",
        "不行",
        "不同意",
        "取消",
        "先不约",
        "暂时不要",
        "换",
        "换一个",
        "no",
    }
    return normalized in negative_phrases or normalized.startswith("换")


def classify_rule_intent(text: str) -> str | None:
    """Classify clear one-turn intent by deterministic rules."""
    normalized = text.strip()
    if not normalized:
        return "other"
    if is_greeting(normalized):
        return "greeting"
    if is_courtesy(normalized):
        return "courtesy"
    if is_scope_question(normalized):
        return "other"

    availability_service = AvailabilityService()
    if is_clear_appointment_start(normalized):
        return "appointment"

    availability_intent = availability_service.classify_availability_intent_by_rules(normalized)
    if availability_intent == AvailabilityIntent.AVAILABILITY:
        return "availability_query"

    if is_knowledge_question(normalized):
        return "knowledge_query"

    return None
