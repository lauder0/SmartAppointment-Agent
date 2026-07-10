"""
实时可约时段查询服务

根据技师信息、营业时间和已预约忙碌时段，计算可预约时间段。
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from config.time_config import time_config
from services.appointment_service import AppointmentService


class AvailabilityIntent(str, Enum):
    """轻量规则对咨询问题的实时排班意图判断结果。"""

    AVAILABILITY = "availability"
    KNOWLEDGE = "knowledge"
    UNCERTAIN = "uncertain"


class AvailabilityService:
    """查询实时可约时段和技师空闲情况。"""

    strong_availability_keywords = [
        "可约", "可预约", "能约", "能预约", "还能约", "还能预约",
        "空位", "空闲", "有空", "有空位", "有档期",
        "档期", "排班", "可用时段", "可预约时间"
    ]
    weak_availability_keywords = [
        "时段", "时间段", "预约时间", "安排", "方便", "接待",
        "哪位技师", "哪个技师", "哪些技师", "技师可以"
    ]
    follow_up_keywords = [
        "男技师", "女技师", "男性技师", "女性技师", "男师傅", "女师傅",
        "男的", "女的", "男", "女", "一小时", "一个小时", "半小时",
        "分钟", "小时", "这个", "那个", "那", "换", "改成", "要",
        "全身按摩", "全身推拿", "肩颈推拿", "足底按摩", "背部推拿",
    ]
    knowledge_keywords = [
        "有哪些服务", "有什么服务", "服务项目", "项目介绍", "价格", "多少钱",
        "怎么预约", "如何预约", "预约流程", "营业时间", "地址", "电话",
        "交通", "环境", "注意事项", "禁忌", "功效", "区别"
    ]

    def __init__(self):
        self.appointment_service = AppointmentService()

    @staticmethod
    def parse_service_type(text: str) -> Optional[str]:
        """Extract a supported service item from user text."""
        lowered = text.lower()
        service_aliases = {
            "全身推拿": ["全身推拿", "全身按摩", "全身", "full body"],
            "肩颈推拿": ["肩颈推拿", "肩颈按摩", "肩颈", "neck", "shoulder"],
            "足底按摩": ["足底按摩", "足底推拿", "足疗", "足底", "foot"],
            "背部推拿": ["背部推拿", "背部按摩", "背部", "back"],
        }
        for canonical, aliases in service_aliases.items():
            if any(alias in lowered or alias in text for alias in aliases):
                return canonical
        if "按摩" in text or "推拿" in text or "massage" in lowered:
            return "按摩"
        return None

    @staticmethod
    def parse_preference(text: str) -> Optional[str]:
        """Extract technician style/preference from user text."""
        normalized = text.strip()
        preference_patterns = [
            (r"(力气|手劲|力度).{0,8}(大|重|强|足)", "力气大"),
            (r"(重手法|手法重|按重点|按重一点|用力一点)", "力气大"),
            (r"(深层|深度|酸痛|肩颈腰背)", "深层放松"),
            (r"(轻一点|轻柔|温柔|不要太重|力气小)", "手法轻柔"),
            (r"(放松|舒缓|助眠|压力大|睡眠差)", "舒缓放松"),
        ]
        for pattern, preference in preference_patterns:
            if re.search(pattern, normalized):
                return preference
        return None

    @staticmethod
    def is_formal_booking_request(text: str) -> bool:
        """Return True only when the user asks the agent to lock/create the booking."""
        normalized = text.strip()
        if not normalized:
            return False
        formal_keywords = [
            "帮我约", "帮我预约", "帮我订", "给我约", "给我预约", "给我安排",
            "就约", "就订", "就这个", "确认预约", "确认下单", "确定预约",
            "帮我锁定", "锁定这个", "安排这个", "预约这个", "订这个",
        ]
        return any(keyword in normalized for keyword in formal_keywords)

    @staticmethod
    def is_clear_appointment_start(text: str) -> bool:
        """Detect appointment intent without treating availability follow-ups as final booking."""
        normalized = text.strip()
        if not normalized:
            return False
        if AvailabilityService.is_formal_booking_request(normalized):
            return True
        starter_keywords = ["我要预约", "我想预约", "我要约", "我想约", "约个", "预约一个"]
        query_keywords = ["有哪些", "有没有", "有空", "空位", "空闲", "可约", "能约", "查", "看看", "看一下"]
        lowered = normalized.lower()
        if any(keyword in lowered for keyword in ("book", "booking", "reserve", "appointment")):
            return True
        return any(keyword in normalized for keyword in starter_keywords) and not any(
            keyword in normalized for keyword in query_keywords
        )

    def classify_availability_intent_by_rules(self, text: str) -> AvailabilityIntent:
        """用轻量规则判断实时排班意图；只处理明显情况，模糊情况交给LLM。"""
        normalized = text.strip()
        if not normalized:
            return AvailabilityIntent.KNOWLEDGE

        if any(keyword in normalized for keyword in self.strong_availability_keywords):
            return AvailabilityIntent.AVAILABILITY

        has_specific_time = self._has_specific_time_expression(normalized)
        has_realtime_subject = self._has_realtime_subject_expression(normalized)
        has_weak_signal = any(keyword in normalized for keyword in self.weak_availability_keywords)

        if has_specific_time and (has_realtime_subject or has_weak_signal):
            return AvailabilityIntent.AVAILABILITY

        if any(keyword in normalized for keyword in self.knowledge_keywords) and not has_specific_time:
            return AvailabilityIntent.KNOWLEDGE

        if has_specific_time or has_realtime_subject or has_weak_signal:
            return AvailabilityIntent.UNCERTAIN

        return AvailabilityIntent.KNOWLEDGE

    def is_availability_query(self, text: str) -> bool:
        """判断是否是实时排班/可约时段查询。"""
        return self.classify_availability_intent_by_rules(text) == AvailabilityIntent.AVAILABILITY

    def is_availability_follow_up(self, text: str) -> bool:
        """判断用户是否在补充上一轮实时排班查询条件。"""
        normalized = text.strip()
        if not normalized:
            return False
        if self._parse_gender(normalized) or self._parse_duration(normalized):
            return True
        if self.parse_preference(normalized):
            return True
        if self.parse_service_type(normalized):
            return True
        if self._has_specific_time_expression(normalized):
            return True
        return any(keyword == normalized or keyword in normalized for keyword in self.follow_up_keywords)

    def _has_specific_time_expression(self, text: str) -> bool:
        lowered = text.lower()
        if re.search(r"\d{1,2}[:：]\d{2}", text):
            return True
        if re.search(r"\b\d{1,2}\s*(?:am|pm)\b", lowered):
            return True
        if re.search(r"(今天|明天|后天|\d{1,2}月\d{1,2}[日号]?)", text):
            return True
        if re.search(r"\b(today|tomorrow)\b", lowered):
            return True
        if re.search(r"(上午|早上|中午|下午|晚上)?\s*[一二两三四五六七八九十\d]{1,3}\s*点", text):
            return True
        return False

    def _has_realtime_subject_expression(self, text: str) -> bool:
        return any(keyword in text for keyword in ("技师", "师傅", "时间", "时段", "档期", "排班"))

    def _availability_time_policy_error(self, criteria: Dict[str, Any]) -> Optional[str]:
        target_date = criteria.get("date")
        if target_date and not time_config.is_within_booking_date_window(target_date):
            return "outside_booking_window"

        start_time = criteria.get("start_time")
        if start_time:
            duration = criteria.get("duration_minutes") or 1
            end_time = start_time + timedelta(minutes=duration)
            valid_time, reason = time_config.validate_booking_time(start_time, end_time)
            if not valid_time:
                return reason
        return None

    def _booking_time_policy_reply(self, reason: str) -> str:
        start_hour, end_hour = time_config.get_business_hours()
        window_days = time_config.get_booking_window_days()
        return (
            "[REPLY][咨询机器人]"
            f"目前只能查询和预约未来 {window_days} 个自然日内的时间，"
            f"营业时间为 {start_hour}:00-{end_hour}:00。"
            "今天只能预约当前时间之后的剩余时段，请换一个时间。"
        )

    def answer_availability_query(self, text: str, base_criteria: Optional[Dict[str, Any]] = None) -> str:
        """返回实时可约时段查询的自然语言回答。"""
        criteria = self.parse_query_criteria(text)
        if base_criteria:
            criteria = self.merge_query_criteria(base_criteria, criteria)
        policy_error = self._availability_time_policy_error(criteria)
        if policy_error:
            return self._booking_time_policy_reply(policy_error)
        technicians = self._filter_technicians(criteria)

        if not technicians:
            return "[REPLY][咨询机器人]抱歉，没有找到符合条件的技师。您可以调整技师姓名或性别偏好后再查询。"

        if criteria.get("start_time"):
            return self._answer_specific_time_query(criteria, technicians)

        duration_minutes = criteria["duration_minutes"] or 60
        slots = self._find_available_slots(
            technicians=technicians,
            target_date=criteria["date"],
            duration_minutes=duration_minutes,
            max_slots=8
        )

        date_text = criteria["date"].strftime("%Y年%m月%d日")
        duration_text = f"{duration_minutes}分钟"
        filter_text = self._build_filter_text(criteria)

        if not slots:
            return (
                "[REPLY][咨询机器人]"
                f"我查询了{date_text}{filter_text}的实时排班，暂时没有找到适合{duration_text}服务的可约时段。"
                "您可以换一个日期、缩短服务时长，或放宽技师偏好后再试。"
            )

        lines = [
            f"我查询了{date_text}{filter_text}的实时排班，以下时段可支持{duration_text}服务："
        ]
        for slot in slots:
            names = "、".join(slot["technician_names"][:3])
            extra = "" if len(slot["technician_names"]) <= 3 else f"等{len(slot['technician_names'])}位技师"
            lines.append(f"- {slot['start']}-{slot['end']}：{names}{extra}可约")

        lines.append("您可以继续告诉我服务项目、时长或技师偏好，我会继续帮您筛选可约技师。如果要正式预约，请说“确认预约”或“帮我约某位技师”。")
        return "[REPLY][咨询机器人]" + "\n".join(lines)

    def extract_available_technician_names(self, response: str) -> List[str]:
        """从实时排班回复中提取展示过的技师姓名，用于短期上下文回指。"""
        technician_names = {
            technician.get("name")
            for technician in self.appointment_service.get_all_technicians()
            if technician.get("name")
        }
        return [name for name in technician_names if name in response]

    def parse_query_criteria(self, text: str) -> Dict[str, Any]:
        """解析实时排班查询条件，并标记哪些条件来自本轮用户明确输入。"""
        target_date = self._parse_date(text)
        duration_minutes = self._parse_duration(text)
        gender = self._parse_gender(text)
        technician_name = self._parse_technician_name(text)
        service_type = self.parse_service_type(text)
        preference = self.parse_preference(text)
        start_time = self._parse_specific_start_time(text, target_date)

        return {
            "date": target_date,
            "duration_minutes": duration_minutes,
            "gender": gender,
            "technician_name": technician_name,
            "service_type": service_type,
            "preference": preference,
            "start_time": start_time,
            "has_explicit_date": self._has_explicit_date_expression(text),
            "has_explicit_time": start_time is not None,
            "has_explicit_duration": duration_minutes is not None,
            "has_explicit_gender": gender is not None,
            "has_explicit_technician_name": technician_name is not None,
            "has_explicit_service_type": service_type is not None,
            "has_explicit_preference": preference is not None,
            "has_explicit_period": bool(re.search(r"(上午|早上|中午|下午|晚上)", text)),
        }

    def merge_query_criteria(
        self,
        base_criteria: Dict[str, Any],
        current_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """将本轮补充条件合并到上一轮实时排班查询条件中。"""
        merged = dict(base_criteria)

        if current_criteria.get("has_explicit_date"):
            merged["date"] = current_criteria["date"]
        elif not merged.get("date"):
            merged["date"] = current_criteria["date"]

        if current_criteria.get("has_explicit_time"):
            current_start = current_criteria["start_time"]
            if current_criteria.get("has_explicit_date"):
                merged["start_time"] = current_start
                merged["date"] = current_criteria["date"]
            else:
                base_date = merged.get("date") or current_criteria["date"]
                hour = current_start.hour
                base_start = merged.get("start_time")
                if (
                    base_start
                    and not current_criteria.get("has_explicit_period")
                    and hour < 12
                    and base_start.hour >= 12
                ):
                    hour += 12
                merged["start_time"] = base_date.replace(
                    hour=hour,
                    minute=current_start.minute,
                    second=0,
                    microsecond=0,
                )
        elif current_criteria.get("has_explicit_date") and merged.get("start_time"):
            base_start = merged["start_time"]
            merged["start_time"] = current_criteria["date"].replace(
                hour=base_start.hour,
                minute=base_start.minute,
                second=0,
                microsecond=0,
            )
        elif not merged.get("start_time"):
            merged["start_time"] = current_criteria.get("start_time")

        for field in ("duration_minutes", "gender", "technician_name", "service_type", "preference"):
            if current_criteria.get(field) is not None:
                merged[field] = current_criteria[field]

        merged["has_explicit_date"] = bool(
            base_criteria.get("has_explicit_date") or current_criteria.get("has_explicit_date")
        )
        merged["has_explicit_time"] = merged.get("start_time") is not None
        merged["has_explicit_duration"] = merged.get("duration_minutes") is not None
        merged["has_explicit_gender"] = merged.get("gender") is not None
        merged["has_explicit_technician_name"] = merged.get("technician_name") is not None
        merged["has_explicit_service_type"] = merged.get("service_type") is not None
        merged["has_explicit_preference"] = merged.get("preference") is not None
        return merged

    def _has_explicit_date_expression(self, text: str) -> bool:
        return bool(re.search(r"(今天|明天|后天|\d{1,2}月\d{1,2}[日号]?)", text) or re.search(r"\b(today|tomorrow)\b", text.lower()))

    def _parse_date(self, text: str) -> datetime:
        lowered = text.lower()
        now = time_config.now()
        if "后天" in text:
            return time_config.today() + timedelta(days=2)
        if "明天" in text or "tomorrow" in lowered:
            return time_config.today() + timedelta(days=1)
        if "today" in lowered:
            return time_config.today()
        match = re.search(r"(\d{1,2})月(\d{1,2})[日号]?", text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            return datetime(now.year, month, day, tzinfo=time_config.BEIJING_TZ)
        return time_config.today()

    def _parse_duration(self, text: str) -> Optional[int]:
        lowered = text.lower()
        english_hour_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:h|hr|hrs|hour|hours)\b", lowered)
        if english_hour_match:
            return int(float(english_hour_match.group(1)) * 60)

        english_minute_match = re.search(r"(\d{1,3})\s*(?:m|min|mins|minute|minutes)\b", lowered)
        if english_minute_match:
            return int(english_minute_match.group(1))

        if "half hour" in lowered:
            return 30

        hour_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:个)?小时", text)
        if hour_match:
            return int(float(hour_match.group(1)) * 60)

        chinese_hour_match = re.search(r"([一二两三四五六七八九十]+)\s*(?:个)?小时", text)
        if chinese_hour_match:
            hours = self._parse_chinese_number(chinese_hour_match.group(1))
            if hours is not None:
                return hours * 60

        minute_match = re.search(r"(\d{2,3})\s*分钟", text)
        if minute_match:
            return int(minute_match.group(1))

        chinese_minute_match = re.search(r"([一二两三四五六七八九十]{2,})\s*分钟", text)
        if chinese_minute_match:
            minutes = self._parse_chinese_number(chinese_minute_match.group(1))
            if minutes is not None:
                return minutes

        return None

    def _parse_specific_start_time(self, text: str, target_date: datetime) -> Optional[datetime]:
        lowered = text.lower()
        colon_match = re.search(r"(\d{1,2})[:：](\d{2})", text)
        if colon_match:
            hour = int(colon_match.group(1))
            minute = int(colon_match.group(2))
            return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        english_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lowered)
        if english_match:
            hour = int(english_match.group(1))
            minute = int(english_match.group(2) or 0)
            period = english_match.group(3)
            if period == "pm" and hour < 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if self._contains_preference_point_expression(text) and not re.search(
            r"(今天|明天|后天|上午|早上|中午|下午|晚上|\d{1,2}[:：]\d{2})",
            text,
        ):
            return None

        time_match = re.search(r"(上午|早上|中午|下午|晚上)?\s*([一二两三四五六七八九十\d]{1,3})\s*点(?:\s*([一二两三四五六七八九十\d]{1,3})\s*分?)?", text)
        if not time_match:
            return None

        period = time_match.group(1) or ""
        hour = self._parse_chinese_number(time_match.group(2))
        minute = self._parse_chinese_number(time_match.group(3) or "0")
        if hour is None or minute is None:
            return None

        if period in ("下午", "晚上") and hour < 12:
            hour += 12
        elif period == "中午" and hour < 11:
            hour += 12
        elif not period:
            start_hour, end_hour = time_config.get_business_hours()
            if hour < start_hour and hour + 12 < end_hour:
                hour += 12

        return target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    def _contains_preference_point_expression(self, text: str) -> bool:
        if "一点钟" in text or "1点钟" in text:
            return False
        return bool(
            re.search(r"(力气|手劲|力度|用力|按|轻|重|大|小|温柔|舒服).{0,6}一点", text)
            or re.search(r"一点的?(男|女)?技师", text)
        )

    def _parse_chinese_number(self, value: str) -> Optional[int]:
        if value.isdigit():
            return int(value)

        digit_map = {
            "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
            "五": 5, "六": 6, "七": 7, "八": 8, "九": 9
        }
        if value in digit_map:
            return digit_map[value]
        if value == "十":
            return 10
        if value.startswith("十"):
            tail = value[1:]
            return 10 + digit_map.get(tail, 0)
        if "十" in value:
            head, tail = value.split("十", 1)
            head_value = digit_map.get(head)
            if head_value is None:
                return None
            return head_value * 10 + digit_map.get(tail, 0)
        return None

    def _parse_gender(self, text: str) -> Optional[str]:
        lowered = text.lower()
        if "男技师" in text or "男性技师" in text or "男师傅" in text:
            return "男"
        if "女技师" in text or "女性技师" in text or "女师傅" in text:
            return "女"
        if re.search(r"\b(female|woman|women|girl)\b", lowered):
            return "女"
        if re.search(r"\b(male|man|men|boy)\b", lowered):
            return "男"
        return None

    def _parse_technician_name(self, text: str) -> Optional[str]:
        for technician in self.appointment_service.get_all_technicians():
            name = technician.get("name")
            if name and name in text:
                return name
        return None

    def _filter_technicians(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        if criteria.get("technician_name"):
            technician = self.appointment_service.get_technician_by_name(criteria["technician_name"])
            return [technician] if technician else []

        technicians = self.appointment_service.get_all_technicians()
        gender = criteria.get("gender")
        if gender:
            technicians = [tech for tech in technicians if tech.get("gender") == gender]
        preference = criteria.get("preference")
        if preference:
            technicians = self._filter_technicians_by_preference(technicians, preference)
        return technicians

    def _filter_technicians_by_preference(
        self,
        technicians: List[Dict[str, Any]],
        preference: str,
    ) -> List[Dict[str, Any]]:
        """Filter technicians by stable style keywords in their strength text."""
        if not preference:
            return technicians

        keyword_map = {
            "力气大": ["力气大", "重手法", "深层", "手法扎实", "肌肉放松"],
            "深层放松": ["深层", "肌肉放松", "肩颈", "腰背", "酸痛"],
            "手法轻柔": ["细腻", "舒缓", "轻柔", "芳香", "精油"],
            "舒缓放松": ["舒缓", "放松", "助眠", "压力", "睡眠"],
        }
        keywords = keyword_map.get(preference, [preference])
        matched = [
            tech
            for tech in technicians
            if any(keyword in (tech.get("strength") or "") for keyword in keywords)
        ]
        return matched or technicians

    def _find_available_slots(
        self,
        technicians: List[Dict[str, Any]],
        target_date: datetime,
        duration_minutes: int,
        max_slots: int
    ) -> List[Dict[str, Any]]:
        start_hour, end_hour = time_config.get_business_hours()
        day_start = target_date.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        day_end = target_date.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        now = time_config.now()

        slot_start = day_start
        if target_date.date() == now.date() and now > slot_start:
            minute = 30 if now.minute <= 30 else 60
            slot_start = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=minute)

        slots = []
        while slot_start + timedelta(minutes=duration_minutes) <= day_end:
            slot_end = slot_start + timedelta(minutes=duration_minutes)
            available_techs = []

            for tech in technicians:
                if self.appointment_service.is_technician_available(tech["id"], slot_start, slot_end):
                    available_techs.append(tech["name"])

            if available_techs:
                slots.append({
                    "start": time_config.format_datetime(slot_start, "%H:%M"),
                    "end": time_config.format_datetime(slot_end, "%H:%M"),
                    "technician_names": available_techs,
                })
                if len(slots) >= max_slots:
                    break

            slot_start += timedelta(minutes=30)

        return slots

    def _answer_specific_time_query(
        self,
        criteria: Dict[str, Any],
        technicians: List[Dict[str, Any]]
    ) -> str:
        start_time = criteria["start_time"]
        date_text = time_config.format_datetime(start_time, "%Y年%m月%d日")
        start_text = time_config.format_datetime(start_time, "%H:%M")
        filter_text = self._build_filter_text(criteria)

        if not criteria.get("duration_minutes"):
            return self._answer_point_in_time_query(criteria, technicians)

        end_time = start_time + timedelta(minutes=criteria["duration_minutes"])
        end_text = time_config.format_datetime(end_time, "%H:%M")
        duration_text = f"{criteria['duration_minutes']}分钟"

        start_hour, end_hour = time_config.get_business_hours()
        day_start = start_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        day_end = start_time.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        if start_time < day_start or end_time > day_end:
            return (
                "[REPLY][咨询机器人]"
                f"{date_text} {start_text}-{end_text} 不在当前营业时间内。"
                f"本店营业时间为 {start_hour}:00-{end_hour}:00，您可以换一个营业时间内的时段。"
            )

        available_techs = [
            tech["name"]
            for tech in technicians
            if self.appointment_service.is_technician_available(tech["id"], start_time, end_time)
        ]

        if available_techs:
            names = "、".join(available_techs[:5])
            extra = "" if len(available_techs) <= 5 else f"等{len(available_techs)}位技师"
            return (
                "[REPLY][咨询机器人]"
                f"我查询了实时排班，{date_text} {start_text}-{end_text}{filter_text}"
                f"可以预约{duration_text}服务。当前可约技师：{names}{extra}。"
                "您可以继续告诉我服务项目、时长或技师偏好，我会继续帮您筛选可约技师。如果要正式预约，请说“确认预约”或“帮我约某位技师”。"
            )

        nearby_slots = self._find_available_slots(
            technicians=technicians,
            target_date=criteria["date"],
            duration_minutes=criteria["duration_minutes"],
            max_slots=3
        )
        if nearby_slots:
            alternatives = "；".join(
                f"{slot['start']}-{slot['end']}（{'、'.join(slot['technician_names'][:2])}可约）"
                for slot in nearby_slots
            )
            return (
                "[REPLY][咨询机器人]"
                f"我查询了实时排班，{date_text} {start_text}-{end_text}{filter_text}"
                f"暂时没有适合{duration_text}服务的空闲技师。"
                f"您可以考虑这些可约时段：{alternatives}。"
            )

        return (
            "[REPLY][咨询机器人]"
            f"我查询了实时排班，{date_text} {start_text}-{end_text}{filter_text}"
            f"暂时没有适合{duration_text}服务的空闲技师。"
        )

    def _answer_point_in_time_query(
        self,
        criteria: Dict[str, Any],
        technicians: List[Dict[str, Any]]
    ) -> str:
        start_time = criteria["start_time"]
        check_end = start_time + timedelta(minutes=1)
        date_text = time_config.format_datetime(start_time, "%Y年%m月%d日")
        start_text = time_config.format_datetime(start_time, "%H:%M")
        filter_text = self._build_filter_text(criteria)

        start_hour, end_hour = time_config.get_business_hours()
        day_start = start_time.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        day_end = start_time.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        if start_time < day_start or start_time >= day_end:
            return (
                "[REPLY][咨询机器人]"
                f"{date_text} {start_text} 不在当前营业时间内。"
                f"本店营业时间为 {start_hour}:00-{end_hour}:00，您可以换一个营业时间内的时段。"
            )

        available_techs = [
            tech["name"]
            for tech in technicians
            if self.appointment_service.is_technician_available(tech["id"], start_time, check_end)
        ]

        if not available_techs:
            return (
                "[REPLY][咨询机器人]"
                f"我查询了实时排班，{date_text} {start_text}{filter_text}"
                "这个时间点暂时没有符合条件的空闲技师。"
            )

        names = "、".join(available_techs[:8])
        extra = "" if len(available_techs) <= 8 else f"等{len(available_techs)}位技师"
        return (
            "[REPLY][咨询机器人]"
            f"我查询了实时排班，{date_text} {start_text}{filter_text}"
            f"这个时间点空闲的技师有：{names}{extra}。"
            "您可以继续告诉我服务项目、时长或技师偏好，我会继续帮您筛选可约技师。如果要正式预约，请说“确认预约”或“帮我约某位技师”。"
        )

    def _build_filter_text(self, criteria: Dict[str, Any]) -> str:
        parts = []
        if criteria.get("technician_name"):
            parts.append(f"{criteria['technician_name']}技师")
        elif criteria.get("gender"):
            parts.append(f"{criteria['gender']}技师")
        if criteria.get("service_type") and criteria["service_type"] != "按摩":
            parts.append(criteria["service_type"])
        if criteria.get("preference"):
            parts.append(criteria["preference"])
        return f"（{'、'.join(parts)}）" if parts else ""
