from __future__ import annotations

from datetime import datetime
from statistics import mean
from typing import Any, Dict, Iterable, Optional

from services.appointment_service import AppointmentService


class AppointmentPreferenceService:
    """Build user preference profiles from durable appointment history."""

    def __init__(self, db_path: str = "sqlite:///data/smart_appointment.db"):
        self.appointment_service = AppointmentService(db_path)

    def recall(self, user_id: str = "default_user", limit: int = 10) -> Dict[str, Any]:
        appointments = self.appointment_service.get_user_appointments(user_id or "default_user", limit=limit)
        profile: Dict[str, Any] = {
            "user_id": user_id or "default_user",
            "appointment_count": len(appointments),
            "raw_preferences": [],
            "confidence": {},
            "patterns": {"pattern": "no_data", "recommendation": "need_more_appointments"},
        }
        if not appointments:
            return profile

        service = self._weighted_top((item.get("service_name") for item in appointments), len(appointments))
        duration = self._weighted_top((item.get("duration_minutes") for item in appointments), len(appointments))
        gender = self._weighted_top(
            (
                item.get("gender_preference") or item.get("technician_gender")
                for item in appointments
            ),
            len(appointments),
        )
        technician = self._weighted_top((item.get("technician_id") for item in appointments), len(appointments))
        time_period = self._weighted_top(
            (self._time_period(item.get("start_time")) for item in appointments),
            len(appointments),
        )
        hour = self._weighted_top((self._hour(item.get("start_time")) for item in appointments), len(appointments))

        self._apply_top(profile, "service", "preferred_service", service)
        self._apply_top(profile, "duration", "preferred_duration_minutes", duration)
        self._apply_top(profile, "gender", "preferred_gender", gender)
        self._apply_top(profile, "time_period", "preferred_time_period", time_period)
        self._apply_top(profile, "hour", "preferred_hour", hour)

        if technician.get("value"):
            technician_id = int(technician["value"])
            profile["preferred_technician_id"] = technician_id
            profile["confidence"]["technician"] = technician["confidence"]
            for item in appointments:
                if item.get("technician_id") == technician_id:
                    profile["preferred_technician_name"] = item.get("technician_name")
                    profile["preferred_technician"] = {
                        "id": technician_id,
                        "name": item.get("technician_name"),
                        "gender": item.get("technician_gender"),
                        "strength": item.get("technician_strength"),
                    }
                    break

        latest = max((self._parse_datetime(item.get("start_time")) for item in appointments), default=None)
        if latest:
            profile["last_appointment_at"] = latest

        interval = self._average_interval_days(appointments)
        if interval is not None:
            profile["average_visit_interval_days"] = interval

        profile["patterns"] = {
            "pattern": "active_user" if len(appointments) > 2 else "occasional_user",
            "frequency_analysis": {
                "days_between": interval or 0,
                "frequency": self._frequency_label(interval, len(appointments)),
            },
            "preferred_technician": str(profile.get("preferred_technician_id"))
            if profile.get("preferred_technician_id")
            else None,
            "time_preference": {
                "preferred_hour": profile.get("preferred_hour"),
                "preferred_time_period": profile.get("preferred_time_period"),
            },
            "total_appointments": len(appointments),
        }
        return profile

    @staticmethod
    def _weighted_top(values: Iterable[Any], count: int) -> Dict[str, Any]:
        scores: Dict[Any, float] = {}
        supports: Dict[Any, int] = {}
        for index, value in enumerate(values):
            if value in (None, "", "None"):
                continue
            weight = max(0.2, 1.0 - (index * 0.08))
            scores[value] = scores.get(value, 0.0) + weight
            supports[value] = supports.get(value, 0) + 1
        if not scores:
            return {}
        total = sum(scores.values())
        value, score = max(scores.items(), key=lambda item: item[1])
        return {
            "value": value,
            "score": score,
            "confidence": round(score / total, 2) if total else 0,
            "sample_size": count,
            "support_count": supports.get(value, 0),
        }

    @staticmethod
    def _apply_top(profile: Dict[str, Any], preference_type: str, field: str, item: Dict[str, Any]) -> None:
        if not item.get("value"):
            return
        profile[field] = item["value"]
        profile["confidence"][preference_type] = item["confidence"]
        profile["raw_preferences"].append(
            {
                "preference_type": preference_type,
                "preference_value": str(item["value"]),
                "confidence_score": item["confidence"],
                "support_count": item.get("support_count", 0),
            }
        )

    @classmethod
    def _average_interval_days(cls, appointments: list[Dict[str, Any]]) -> Optional[float]:
        dates = sorted(
            parsed
            for parsed in (cls._parse_datetime(item.get("start_time")) for item in appointments)
            if parsed
        )
        if len(dates) < 2:
            return None
        intervals = [(dates[index + 1] - dates[index]).days for index in range(len(dates) - 1)]
        return round(mean(intervals), 1)

    @staticmethod
    def _frequency_label(interval: Optional[float], count: int) -> str:
        if count < 2 or interval is None:
            return "single_appointment"
        if interval < 7:
            return "very_frequent"
        if interval < 14:
            return "frequent"
        if interval < 30:
            return "regular"
        return "occasional"

    @classmethod
    def _time_period(cls, value: Any) -> Optional[str]:
        parsed = cls._parse_datetime(value)
        if not parsed:
            return None
        if 6 <= parsed.hour < 12:
            return "morning"
        if 12 <= parsed.hour < 18:
            return "afternoon"
        return "evening"

    @classmethod
    def _hour(cls, value: Any) -> Optional[int]:
        parsed = cls._parse_datetime(value)
        return parsed.hour if parsed else None

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
