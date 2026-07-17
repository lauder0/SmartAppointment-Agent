"""Deterministic context rules used before the LLM router.

The understander owns lightweight text rules. When a rule needs business
parsing, it goes through the tools layer so the dependency direction remains:
Agent -> Tool -> Service.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from tools.availability_rule_tools import (
    AvailabilityIntent,
    classify_availability_intent_by_rules,
    is_availability_follow_up as _is_availability_follow_up,
    is_clear_appointment_start as _is_clear_appointment_start,
    is_formal_booking_request as _is_formal_booking_request,
    parse_query_criteria,
    parse_service_type,
)


@dataclass(frozen=True)
class RuleMatch:
    """Structured deterministic rule result before context/LLM enhancement."""

    signal_name: str
    intent_group: str
    subtype: str
    confidence: float = 0.9
    requires_context: bool = False
    attributes: dict[str, object] | None = None


GREETING_TERMS = {"你好", "您好", "嗨", "hi", "hello", "hey", "哈喽", "在吗", "您好呀", "你好呀"}
COURTESY_TERMS = {"谢谢", "感谢", "多谢", "好的谢谢", "谢谢你", "先这样", "我先看看", "好的我看看"}

SERVICE_CATALOG_QUESTION_KEYWORDS = [
    "有什么服务",
    "有哪些服务",
    "服务项目",
    "有什么项目",
    "有哪些项目",
    "都有什么项目",
    "服务清单",
    "项目清单",
    "价目表",
    "按摩项目",
    "推拿项目",
]

PRICE_QUESTION_KEYWORDS = [
    "价格",
    "价钱",
    "多少钱",
    "收费",
    "费用",
    "怎么收费",
    "如何收费",
    "贵不贵",
    "单价",
    "一次多少钱",
    "一小时多少钱",
]

HOURS_QUESTION_KEYWORDS = [
    "营业时间",
    "营业到几点",
    "几点开门",
    "几点关门",
    "几点下班",
    "开到几点",
    "什么时候开门",
    "什么时候关门",
    "上班时间",
    "今天营业吗",
    "周末营业吗",
]

LOCATION_QUESTION_KEYWORDS = [
    "地址",
    "位置",
    "在哪",
    "在哪儿",
    "在哪里",
    "哪儿",
    "哪里",
    "怎么走",
    "怎么去",
    "怎么过去",
    "导航",
    "交通",
    "地铁",
    "停车",
    "附近",
]

CONTACT_QUESTION_KEYWORDS = ["电话", "联系方式", "联系电话", "客服电话", "手机号", "微信", "联系你们"]
MEMBERSHIP_QUESTION_KEYWORDS = ["会员", "优惠", "活动", "折扣", "办卡", "储值", "充值", "次卡", "套餐", "团购", "券"]

APPOINTMENT_POLICY_QUESTION_KEYWORDS = [
    "怎么预约",
    "如何预约",
    "预约流程",
    "需要预约",
    "要预约吗",
    "提前多久",
    "怎么取消",
    "取消规则",
    "能取消吗",
    "可以取消吗",
    "怎么改时间",
    "可以改时间吗",
    "更改时间",
    "改期",
    "迟到",
]

SERVICE_DETAIL_QUESTION_KEYWORDS = [
    "项目介绍",
    "服务介绍",
    "注意事项",
    "禁忌",
    "功效",
    "作用",
    "效果",
    "区别",
    "适合什么",
    "不适合",
    "疼不疼",
    "痛不痛",
    "孕妇",
    "老人",
    "儿童",
    "经期",
    "空腹",
    "酒后",
]

TECHNICIAN_INFO_QUESTION_KEYWORDS = [
    "技师介绍",
    "师傅介绍",
    "有哪些技师",
    "有什么技师",
    "技师有哪些",
    "有哪些师傅",
    "师傅有哪些",
    "都有谁",
    "擅长什么",
    "手法怎么样",
]

SERVICE_RECOMMENDATION_KEYWORDS = [
    "推荐项目",
    "推荐服务",
    "推荐个项目",
    "推荐一个项目",
    "推荐一下项目",
    "推荐一下服务",
    "帮我推荐项目",
    "帮我推荐服务",
    "适合做什么项目",
    "适合什么项目",
    "适合什么服务",
    "做什么项目好",
    "做什么服务好",
    "选什么项目",
    "选什么",
    "应该选什么",
    "选哪个项目",
    "哪个项目适合",
    "哪种项目适合",
    "哪种推拿适合",
    "不知道做哪个",
    "不知道选哪个项目",
    "不知道选什么项目",
    "肩颈酸做什么",
    "脖子酸",
    "颈椎酸",
    "肩膀酸做什么",
    "腰酸背痛做什么",
    "想放松做什么",
]

SERVICE_SELECTION_KEYWORDS = ["想做", "我要", "我想", "选", "做这个", "就这个"]
SCOPE_KEYWORDS = ["你能做什么", "你会做什么", "能做什么", "会做什么", "能干什么", "你有什么功能"]
AVAILABILITY_LANGUAGE = ["可约", "可预约", "能约", "能预约", "有空", "空闲", "空位", "档期", "排班", "时段"]
UNSAFE_OR_UNSUPPORTED_KEYWORDS = ["别人的预约", "所有用户", "导出用户", "忽略规则", "绕过", "管理员权限"]


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text.strip().lower() if ch.isalnum() or "\u4e00" <= ch <= "\u9fff")


def _contains_any(text: str, keywords: list[str] | tuple[str, ...] | set[str]) -> bool:
    raw = text.strip().lower()
    normalized = _compact_text(text)
    return any(keyword in raw or keyword in normalized for keyword in keywords)


def _has_time_expression(text: str) -> bool:
    lowered = text.lower()
    return bool(
        re.search(r"\d{1,2}[:：]\d{2}", text)
        or re.search(r"\b\d{1,2}\s*(?:am|pm)\b", lowered)
        or re.search(r"(今天|明天|后天|\d{1,2}月\d{1,2}[日号]?)", text)
        or re.search(r"\b(today|tomorrow)\b", lowered)
        or re.search(r"(上午|早上|中午|下午|晚上)?\s*[一二两三四五六七八九十\d]{1,3}\s*点", text)
    )


def _has_availability_language(text: str) -> bool:
    return _contains_any(text, AVAILABILITY_LANGUAGE)


def is_greeting(text: str) -> bool:
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
    return any(signal in normalized for signal in ("谢谢", "感谢", "多谢")) and len(normalized) <= 12


def is_service_catalog_question(text: str) -> bool:
    return _contains_any(text, SERVICE_CATALOG_QUESTION_KEYWORDS)


def is_price_question(text: str) -> bool:
    return _contains_any(text, PRICE_QUESTION_KEYWORDS)


def is_business_hours_question(text: str) -> bool:
    return _contains_any(text, HOURS_QUESTION_KEYWORDS)


def is_location_question(text: str) -> bool:
    normalized = _compact_text(text)
    if not _contains_any(text, LOCATION_QUESTION_KEYWORDS):
        return False
    strong_travel_queries = ("怎么走", "怎么去", "怎么过去", "导航", "交通", "地铁", "停车")
    if any(query in normalized for query in strong_travel_queries):
        return True
    store_subjects = ("你们", "门店", "店", "店铺", "按摩店", "推拿店", "地址", "位置", "地方")
    location_queries = ("在哪", "在哪里", "在哪儿", "哪儿", "哪里", "位置", "地址")
    return any(subject in normalized for subject in store_subjects) and any(query in normalized for query in location_queries)


def is_contact_question(text: str) -> bool:
    return _contains_any(text, CONTACT_QUESTION_KEYWORDS)


def is_membership_question(text: str) -> bool:
    return _contains_any(text, MEMBERSHIP_QUESTION_KEYWORDS)


def is_appointment_policy_question(text: str) -> bool:
    return _contains_any(text, APPOINTMENT_POLICY_QUESTION_KEYWORDS)


def is_service_detail_question(text: str) -> bool:
    return _contains_any(text, SERVICE_DETAIL_QUESTION_KEYWORDS)


def is_technician_info_question(text: str) -> bool:
    if _has_time_expression(text) or _has_availability_language(text):
        return False
    return _contains_any(text, TECHNICIAN_INFO_QUESTION_KEYWORDS)


def is_knowledge_question(text: str) -> bool:
    return (
        is_service_catalog_question(text)
        or is_price_question(text)
        or is_business_hours_question(text)
        or is_location_question(text)
        or is_contact_question(text)
        or is_membership_question(text)
        or is_appointment_policy_question(text)
        or is_service_detail_question(text)
        or is_technician_info_question(text)
    )


def is_service_recommendation_request(text: str) -> bool:
    normalized = _compact_text(text)
    if not normalized:
        return False
    if _contains_any(text, SERVICE_RECOMMENDATION_KEYWORDS):
        return True
    has_service_subject = any(word in normalized for word in ("项目", "服务", "推拿", "按摩", "足疗"))
    has_choice_language = any(word in normalized for word in ("推荐", "适合", "选哪", "选什么", "做什么", "哪个好"))
    has_technician_subject = any(word in normalized for word in ("技师", "师傅"))
    return has_service_subject and has_choice_language and not has_technician_subject


def is_scope_question(text: str) -> bool:
    return _contains_any(text, SCOPE_KEYWORDS)


def is_unsafe_or_unsupported_request(text: str) -> bool:
    return _contains_any(text, UNSAFE_OR_UNSUPPORTED_KEYWORDS)


def is_formal_booking_request(text: str) -> bool:
    return _is_formal_booking_request(text)


def is_modification_request(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    if _contains_any(
        normalized,
        ("改成", "改到", "换成", "换到", "换一个", "换个", "换技师", "改一个", "换时间", "改时间", "重新选", "重新推荐"),
    ):
        return True
    service = parse_service_type(normalized)
    criteria = parse_query_criteria(normalized)
    return bool(
        service
        or criteria.get("duration_minutes")
        or criteria.get("gender")
        or criteria.get("technician_name")
        or criteria.get("preference")
        or criteria.get("start_time")
    )


def is_technician_replacement_request(text: str) -> bool:
    normalized = _compact_text(text)
    if not normalized:
        return False
    replacement_phrases = ("换一个技师", "换个技师", "换一位技师", "换位技师", "换技师", "更换技师", "重新推荐技师", "重新选技师")
    if any(phrase in normalized for phrase in replacement_phrases):
        return True
    return normalized.startswith("换") and ("技师" in normalized or "师傅" in normalized)


def is_clear_appointment_start(text: str) -> bool:
    return _is_clear_appointment_start(text)


def is_availability_refinement(text: str) -> bool:
    return _is_availability_follow_up(text)


def is_recommendation_request(text: str) -> bool:
    if is_service_recommendation_request(text):
        return False
    normalized = _compact_text(text)
    recommendation_phrases = (
        "有推荐",
        "有没有推荐",
        "推荐技师",
        "推荐的技师",
        "推荐师傅",
        "推荐一个",
        "推荐一位",
        "帮我推荐",
        "你帮我选",
        "帮我选一个",
        "帮我看看哪个",
        "帮我看看哪位",
        "哪个更合适",
        "哪位更合适",
        "哪个技师合适",
        "哪位技师合适",
        "哪个师傅合适",
        "哪位师傅合适",
        "合适的技师",
        "合适的师傅",
        "哪个好",
        "选哪个好",
        "你看着选",
        "随便推荐",
    )
    preference_signals = ("力气大", "手劲大", "重一点", "轻一点", "温柔一点", "舒缓一点", "按得深", "按透")
    return any(phrase in normalized for phrase in recommendation_phrases) or (
        any(signal in normalized for signal in preference_signals) and any(word in normalized for word in ("推荐", "选"))
    )


def is_recommendation_replacement_request(text: str) -> bool:
    normalized = _compact_text(text)
    return any(phrase in normalized for phrase in ("换一个", "换一位", "换个推荐", "再推荐一个", "还有别的吗", "下一个", "不要这个"))


def is_positive_confirmation(text: str) -> bool:
    normalized = _compact_text(text)
    return normalized in {
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


def is_negative_confirmation(text: str) -> bool:
    normalized = _compact_text(text)
    return normalized in {"不", "不要", "不行", "不同意", "取消", "先不约", "暂时不要", "换", "换一个", "no"} or normalized.startswith("换")


def is_recommendation_selection(text: str) -> bool:
    normalized = _compact_text(text)
    return is_positive_confirmation(text) or normalized in {
        "就他",
        "就他吧",
        "就她",
        "就她吧",
        "就这位",
        "就这位吧",
        "选他",
        "选他吧",
        "选她",
        "选她吧",
        "第一个",
        "第一位",
        "就第一个",
        "就第一位",
        "确认选择",
    }


def is_service_selection_after_catalog(text: str) -> bool:
    service_type = parse_service_type(text)
    return bool(service_type and _contains_any(text, SERVICE_SELECTION_KEYWORDS))


def classify_static_consultation_subtypes(text: str) -> list[str]:
    """Return stable knowledge subtypes matched by deterministic rules."""
    subtype_matchers = [
        ("service_catalog", is_service_catalog_question),
        ("pricing", is_price_question),
        ("business_hours", is_business_hours_question),
        ("location", is_location_question),
        ("contact", is_contact_question),
        ("appointment_policy", is_appointment_policy_question),
        ("service_detail", is_service_detail_question),
        ("technician_info", is_technician_info_question),
        ("membership_promotion", is_membership_question),
    ]
    return [subtype for subtype, matcher in subtype_matchers if matcher(text)]


def classify_rule_matches(text: str) -> list[RuleMatch]:
    """Classify clear deterministic business signals into groups and subtypes."""
    normalized = text.strip()
    if not normalized:
        return [RuleMatch("other", "basic_interaction", "empty", 0.98)]

    matches: list[RuleMatch] = []

    if is_unsafe_or_unsupported_request(normalized):
        return [RuleMatch("unsafe_or_unsupported", "safety", "permission_or_privacy_boundary", 0.99)]

    if is_greeting(normalized):
        matches.append(RuleMatch("greeting", "basic_interaction", "greeting", 0.98))
    if is_courtesy(normalized):
        matches.append(RuleMatch("courtesy", "basic_interaction", "courtesy", 0.98))
    if is_scope_question(normalized):
        matches.append(RuleMatch("other", "basic_interaction", "capability_scope", 0.9))

    for subtype in classify_static_consultation_subtypes(normalized):
        matches.append(
            RuleMatch(
                "knowledge_query",
                "static_consultation",
                subtype,
                0.95,
                attributes={"extension": subtype == "membership_promotion"},
            )
        )

    if is_service_recommendation_request(normalized):
        matches.append(RuleMatch("service_recommendation_request", "recommendation", "service_recommendation", 0.94))
    if is_recommendation_request(normalized):
        matches.append(RuleMatch("recommendation_request", "recommendation", "technician_recommendation", 0.95))
    if is_recommendation_replacement_request(normalized):
        matches.append(RuleMatch("recommendation_replacement", "context_operation", "recommendation_replacement", 0.95, True))
    if is_recommendation_selection(normalized):
        matches.append(RuleMatch("recommendation_selection", "context_operation", "recommendation_selection", 0.95, True))
    if is_positive_confirmation(normalized):
        matches.append(RuleMatch("positive_confirmation", "context_operation", "confirmation_positive", 0.96, True))
    if is_negative_confirmation(normalized):
        matches.append(RuleMatch("negative_confirmation", "context_operation", "confirmation_negative", 0.96, True))
    if is_modification_request(normalized):
        matches.append(RuleMatch("modification_request", "context_operation", "slot_or_task_modification", 0.86, True))
    if is_formal_booking_request(normalized):
        matches.append(RuleMatch("formal_booking_request", "booking", "formal_booking_commit", 0.96))
    if is_clear_appointment_start(normalized):
        matches.append(RuleMatch("appointment_request", "booking", "booking_start", 0.94))

    availability_intent = classify_availability_intent_by_rules(normalized)
    if availability_intent == AvailabilityIntent.AVAILABILITY:
        matches.append(RuleMatch("availability_query", "availability", "realtime_schedule_query", 0.94))
    if is_availability_refinement(normalized):
        matches.append(RuleMatch("availability_refinement", "context_operation", "availability_filter_refinement", 0.86, True))
    if is_service_selection_after_catalog(normalized):
        matches.append(RuleMatch("service_selection", "context_operation", "service_selection", 0.95, True))

    return matches


def classify_rule_intent(text: str) -> str | None:
    """Classify clear one-turn intent by deterministic rules."""
    matches = classify_rule_matches(text)
    names = {match.signal_name for match in matches}
    if "appointment_request" in names:
        return "appointment"
    if "availability_query" in names:
        return "availability_query"
    if "knowledge_query" in names or "service_recommendation_request" in names:
        return "knowledge_query"
    if "greeting" in names:
        return "greeting"
    if "courtesy" in names:
        return "courtesy"
    if "other" in names:
        return "other"
    return None
