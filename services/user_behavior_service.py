from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from db.db_router import DatabaseRouter

logger = logging.getLogger(__name__)


class UserBehaviorService:
    """Service for durable behavior records and preference updates."""

    def __init__(self, db_path: str = "sqlite:///data/smart_appointment.db"):
        self.db_router = DatabaseRouter(db_path)
        self.user_behavior_repo = self.db_router.user_behavior

    def record_behavior(
        self,
        user_id: str,
        action_type: str,
        action_data: Dict[str, Any] | None = None,
        technician_id: str | int | None = None,
        session_id: str = "default_session",
    ) -> bool:
        """Record one behavior and update preferences when the behavior is an appointment."""
        try:
            action_data = action_data or {}
            normalized_technician_id = self._normalize_technician_id(
                technician_id or action_data.get("technician_id")
            )
            behavior_id = self.user_behavior_repo.record_behavior(
                user_id=user_id,
                action_type=action_type,
                action_data=action_data,
                technician_id=normalized_technician_id,
                session_id=session_id,
            )

            if behavior_id:
                self._update_preferences_from_behavior(
                    user_id=user_id,
                    action_type=action_type,
                    action_data=action_data,
                    technician_id=normalized_technician_id,
                )
                logger.info(
                    "User behavior recorded: user=%s, action=%s, id=%s",
                    user_id,
                    action_type,
                    behavior_id,
                )
                return True
            return False
        except Exception as e:
            logger.error("Failed to record user behavior: %s", e)
            return False

    def get_user_behaviors(
        self,
        user_id: str,
        action_type: str | None = None,
        days_back: int | None = None,
    ) -> List[Dict[str, Any]]:
        try:
            return self.user_behavior_repo.get_user_behaviors(user_id, action_type, days_back)
        except Exception as e:
            logger.error("Failed to get user behaviors: %s", e)
            return []

    def get_user_preferences(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            return self.user_behavior_repo.get_user_preferences(user_id)
        except Exception as e:
            logger.error("Failed to get user preferences: %s", e)
            return []

    def update_user_preference(
        self,
        user_id: str,
        preference_type: str,
        preference_value: str,
        confidence_score: int = 1,
    ) -> bool:
        try:
            return self.user_behavior_repo.update_user_preference(
                user_id,
                preference_type,
                preference_value,
                confidence_score,
            )
        except Exception as e:
            logger.error("Failed to update user preference: %s", e)
            return False

    def get_known_user_ids(self, days_back: int | None = None) -> List[str]:
        try:
            return self.user_behavior_repo.get_known_user_ids(days_back)
        except Exception as e:
            logger.error("Failed to get known user ids: %s", e)
            return []

    def analyze_user_patterns(self, user_id: str) -> Dict[str, Any]:
        try:
            behaviors = self.get_user_behaviors(user_id, days_back=30)
            if not behaviors:
                return {"pattern": "no_data", "recommendation": "need_more_data"}

            appointment_behaviors = [
                behavior for behavior in behaviors if behavior.get("action_type") == "appointment"
            ]
            freq_analysis = self._analyze_frequency(appointment_behaviors)
            preferred_technician = self._analyze_preferred_technician(appointment_behaviors)
            time_preference = self._analyze_time_preference(appointment_behaviors)

            return {
                "pattern": "active_user" if len(appointment_behaviors) > 2 else "occasional_user",
                "frequency_analysis": freq_analysis,
                "preferred_technician": preferred_technician,
                "time_preference": time_preference,
                "total_appointments": len(appointment_behaviors),
                "analysis_period_days": 30,
            }
        except Exception as e:
            logger.error("Failed to analyze user patterns: %s", e)
            return {"pattern": "analysis_error", "error": str(e)}

    def _update_preferences_from_behavior(
        self,
        user_id: str,
        action_type: str,
        action_data: Dict[str, Any],
        technician_id: Optional[int],
    ) -> None:
        if action_type != "appointment":
            return

        updates: list[tuple[str, str, int]] = []
        if technician_id:
            updates.append(("technician", str(technician_id), 2))

        service_name = (
            action_data.get("service_name")
            or action_data.get("project")
            or action_data.get("service_type")
        )
        if service_name:
            updates.append(("service", str(service_name), 1))

        duration = self._normalize_duration(
            action_data.get("duration_minutes") or action_data.get("duration")
        )
        if duration:
            updates.append(("duration", str(duration), 1))

        gender = action_data.get("gender_preference") or action_data.get("gender")
        if gender:
            updates.append(("gender", str(gender), 1))

        style = (
            action_data.get("preference")
            or action_data.get("style_preference")
            or action_data.get("technician_type")
        )
        if style:
            updates.append(("style", str(style), 1))

        time_period = self._time_period_from_start_time(action_data.get("start_time"))
        if time_period:
            updates.append(("time_period", time_period, 1))

        for preference_type, preference_value, score in updates:
            self.update_user_preference(user_id, preference_type, preference_value, score)

    def _analyze_frequency(self, appointment_behaviors: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not appointment_behaviors:
            return {"frequency": "no_appointments", "days_between": 0}
        if len(appointment_behaviors) < 2:
            return {"frequency": "single_appointment", "days_between": 0}

        dates = []
        for behavior in appointment_behaviors:
            parsed = self._parse_datetime(behavior.get("created_at"))
            if parsed:
                dates.append(parsed)

        if len(dates) < 2:
            return {"frequency": "insufficient_data", "days_between": 0}

        dates.sort()
        intervals = [(dates[i + 1] - dates[i]).days for i in range(len(dates) - 1)]
        avg_interval = sum(intervals) / len(intervals)

        if avg_interval < 7:
            frequency = "very_frequent"
        elif avg_interval < 14:
            frequency = "frequent"
        elif avg_interval < 30:
            frequency = "regular"
        else:
            frequency = "occasional"

        return {"frequency": frequency, "days_between": avg_interval}

    def _analyze_preferred_technician(
        self,
        appointment_behaviors: List[Dict[str, Any]],
    ) -> Optional[str]:
        technician_counts = Counter(
            str(behavior.get("technician_id"))
            for behavior in appointment_behaviors
            if behavior.get("technician_id")
        )
        if not technician_counts:
            return None
        technician_id, count = technician_counts.most_common(1)[0]
        return technician_id if count > 1 else None

    def _analyze_time_preference(self, appointment_behaviors: List[Dict[str, Any]]) -> Dict[str, Any]:
        hours = []
        weekdays = []
        for behavior in appointment_behaviors:
            action_data = behavior.get("action_data") or {}
            parsed = self._parse_datetime(action_data.get("start_time"))
            if parsed:
                hours.append(parsed.hour)
                weekdays.append(parsed.weekday())

        if not hours:
            return {"preferred_hour": None, "preferred_weekday": None}

        hour_counter = Counter(hours)
        weekday_counter = Counter(weekdays)
        preferred_hour = hour_counter.most_common(1)[0][0]
        preferred_weekday = weekday_counter.most_common(1)[0][0]
        weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        return {
            "preferred_hour": preferred_hour,
            "preferred_weekday": weekday_names[preferred_weekday],
            "hour_distribution": dict(hour_counter),
            "weekday_distribution": dict(weekday_counter),
        }

    @staticmethod
    def _normalize_technician_id(technician_id: Any) -> Optional[int]:
        if technician_id in (None, "", "None"):
            return None
        try:
            return int(technician_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_duration(duration: Any) -> Optional[int]:
        if duration in (None, "", "None"):
            return None
        if isinstance(duration, int):
            return duration
        digits = re.findall(r"\d+", str(duration))
        return int(digits[0]) if digits else None

    @classmethod
    def _time_period_from_start_time(cls, start_time: Any) -> Optional[str]:
        parsed = cls._parse_datetime(start_time)
        if not parsed:
            return None
        if 6 <= parsed.hour < 12:
            return "morning"
        if 12 <= parsed.hour < 18:
            return "afternoon"
        return "evening"

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            try:
                from config.time_config import time_config

                return time_config.parse_datetime(str(value))
            except Exception:
                return None
