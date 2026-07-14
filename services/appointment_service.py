import logging
import threading
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from db.db_router import DatabaseRouter


logger = logging.getLogger(__name__)

_APPOINTMENT_LOCKS: Dict[int, threading.Lock] = {}
_APPOINTMENT_LOCKS_GUARD = threading.Lock()


def _get_technician_lock(technician_id: int) -> threading.Lock:
    with _APPOINTMENT_LOCKS_GUARD:
        lock = _APPOINTMENT_LOCKS.get(technician_id)
        if lock is None:
            lock = threading.Lock()
            _APPOINTMENT_LOCKS[technician_id] = lock
        return lock


class AppointmentService:
    """Service layer for appointment persistence and technician availability."""

    def __init__(self, db_path: str = "sqlite:///data/smart_appointment.db"):
        self.db_router = DatabaseRouter(db_path)
        self.technician_repo = self.db_router.technicians
        self.appointment_repo = self.db_router.appointments

    def save_appointment(
        self,
        technician_id: str,
        start_time: datetime,
        end_time: datetime,
        appointment_history: Dict[str, Any],
        session_id: str,
        user_id: str = "default_user",
        idempotency_key: Optional[str] = None,
    ) -> bool:
        return bool(
            self.save_appointment_result(
                technician_id=technician_id,
                start_time=start_time,
                end_time=end_time,
                appointment_history=appointment_history,
                session_id=session_id,
                user_id=user_id,
                idempotency_key=idempotency_key,
            ).get("success")
        )

    def save_appointment_result(
        self,
        technician_id: str,
        start_time: datetime,
        end_time: datetime,
        appointment_history: Dict[str, Any],
        session_id: str,
        user_id: str = "default_user",
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            technician_id_int = int(technician_id)
            appointment_no = f"APPT{int(time.time() * 1000)}{uuid.uuid4().hex[:6].upper()}"
            duration_minutes = int((end_time - start_time).total_seconds() / 60)
            service_name = appointment_history.get("project") or "massage service"
            gender_preference = appointment_history.get("gender")

            with _get_technician_lock(technician_id_int):
                result = self.appointment_repo.create_appointment_with_schedule_atomic(
                    appointment_no=appointment_no,
                    user_id=user_id or "default_user",
                    technician_id=technician_id_int,
                    service_name=service_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=duration_minutes,
                    gender_preference=gender_preference,
                    session_id=session_id,
                    source="chat",
                    status="confirmed",
                    idempotency_key=idempotency_key,
                )

            if not result.get("success"):
                logger.warning(
                    "Appointment save blocked: technician_id=%s, start=%s, end=%s, reason=%s",
                    technician_id,
                    start_time,
                    end_time,
                    result.get("reason"),
                )
                return result

            logger.info(
                "Appointment saved: technician_id=%s, start=%s, end=%s, appointment_id=%s, created=%s",
                technician_id,
                start_time,
                end_time,
                result.get("appointment_id"),
                result.get("created"),
            )
            return result
        except Exception as e:
            logger.error("Failed to save appointment: %s", e)
            return {"success": False, "created": False, "reason": "service_exception", "error": str(e)}

    def get_user_appointments(self, user_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            return self.appointment_repo.get_user_appointments(user_id, limit=limit)
        except Exception as e:
            logger.error("Failed to get user appointment history: %s", e)
            return []

    def get_known_user_ids(self, days_back: Optional[int] = None) -> List[str]:
        try:
            return self.appointment_repo.get_known_user_ids(days_back=days_back)
        except Exception as e:
            logger.error("Failed to get appointment user ids: %s", e)
            return []

    def get_technician_by_id(self, technician_id: int) -> Optional[Dict[str, Any]]:
        try:
            return self.technician_repo.get_technician_by_id(technician_id)
        except Exception as e:
            logger.error("Failed to get technician by id: %s", e)
            return None

    def get_technician_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        try:
            return self.technician_repo.get_technician_by_name(name)
        except Exception as e:
            logger.error("Failed to get technician by name: %s", e)
            return None

    def get_all_technicians(self) -> List[Dict[str, Any]]:
        try:
            return self.technician_repo.get_all_technicians()
        except Exception as e:
            logger.error("Failed to get technicians: %s", e)
            return []

    def get_technicians_by_gender(self, gender: str) -> List[Dict[str, Any]]:
        try:
            return self.technician_repo.get_technicians_by_gender(gender)
        except Exception as e:
            logger.error("Failed to get technicians by gender: %s", e)
            return []

    def get_technician_schedules(self, technician_id: int, date) -> List[Dict[str, Any]]:
        try:
            return self.technician_repo.get_technician_schedules(technician_id, date)
        except Exception as e:
            logger.error("Failed to get technician schedules: %s", e)
            return []

    def is_technician_available(self, technician_id: int, start_time: datetime, end_time: datetime) -> bool:
        try:
            return self.technician_repo.is_technician_available(technician_id, start_time, end_time)
        except Exception as e:
            logger.error("Failed to check technician availability: %s", e)
            return False

    def add_technician(self, name: str, gender: str = None, strength: str = None) -> Optional[int]:
        try:
            return self.technician_repo.add_technician(name, gender, strength)
        except Exception as e:
            logger.error("Failed to add technician: %s", e)
            return None

    def get_all_strengths(self) -> List[str]:
        try:
            return self.technician_repo.get_all_strengths()
        except Exception as e:
            logger.error("Failed to get technician strengths: %s", e)
            return []
