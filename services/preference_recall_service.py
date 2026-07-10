from __future__ import annotations

from typing import Any, Dict

from services.appointment_preference_service import AppointmentPreferenceService


class PreferenceRecallService:
    """Compatibility facade for appointment-history-based preference recall."""

    def __init__(self, db_path: str = "sqlite:///data/smart_appointment.db"):
        self.appointment_preference_service = AppointmentPreferenceService(db_path)

    def recall(self, user_id: str = "default_user") -> Dict[str, Any]:
        return self.appointment_preference_service.recall(user_id or "default_user")
