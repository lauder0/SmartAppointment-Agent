from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.time_utils import business_now_naive, utc_now_naive
from db.db_router import DatabaseRouter
from services.appointment_preference_service import AppointmentPreferenceService
from services.appointment_service import AppointmentService

logger = logging.getLogger(__name__)

try:
    import schedule
except ModuleNotFoundError:  # pragma: no cover - depends on deployment extras
    schedule = None


class RecommendationService:
    """Generate return-visit recommendations from appointment history only."""

    def __init__(self, db_path: str = "sqlite:///data/smart_appointment.db"):
        self.db_path = db_path
        self._db_router: DatabaseRouter | None = None
        self._appointment_service: AppointmentService | None = None
        self._preference_service: AppointmentPreferenceService | None = None
        self.is_running = False
        self.scheduler_thread = None

    @property
    def db_router(self) -> DatabaseRouter:
        if self._db_router is None:
            self._db_router = DatabaseRouter(self.db_path)
        return self._db_router

    @property
    def recommendation_repo(self):
        return self.db_router.user_behavior

    @property
    def appointment_service(self) -> AppointmentService:
        if self._appointment_service is None:
            self._appointment_service = AppointmentService(self.db_path)
        return self._appointment_service

    @property
    def preference_service(self) -> AppointmentPreferenceService:
        if self._preference_service is None:
            self._preference_service = AppointmentPreferenceService(self.db_path)
        return self._preference_service

    def generate_recommendations_job(self) -> Optional[List[Dict[str, Any]]]:
        """Generate due recommendations and persist them without sending."""
        try:
            logger.info("Starting appointment-history recommendation generation")
            user_ids = self.appointment_service.get_known_user_ids(days_back=180)
            recommendations: List[Dict[str, Any]] = []
            for user_id in user_ids:
                recommendations.extend(self._generate_for_user(user_id))

            if recommendations:
                logger.info("Generated %s recommendations", len(recommendations))
                return recommendations

            logger.info("No recommendations generated")
            return None
        except Exception as e:
            logger.error("Recommendation job failed: %s", e)
            return None

    def _generate_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        profile = self.preference_service.recall(user_id)
        if not profile.get("appointment_count"):
            return []

        last_visit = profile.get("last_appointment_at")
        if not isinstance(last_visit, datetime):
            return []

        days_since_last = (business_now_naive() - last_visit.replace(tzinfo=None)).days
        interval = self._preferred_interval_days(profile)
        if days_since_last < interval:
            return []

        latest_appointments = self.appointment_service.get_user_appointments(user_id, limit=1)
        if not latest_appointments:
            return []

        latest_id = latest_appointments[0]["id"]
        dedupe_key = f"return_reminder:{user_id}:{latest_id}"
        if self._find_existing_recommendation(user_id, dedupe_key):
            return []

        available_times = self._preferred_technician_slots(profile)
        payload = {
            "days_since_last_appointment": days_since_last,
            "preferred_interval_days": interval,
            "preferred_service": profile.get("preferred_service"),
            "preferred_duration_minutes": profile.get("preferred_duration_minutes"),
            "preferred_technician_id": profile.get("preferred_technician_id"),
            "preferred_technician_name": profile.get("preferred_technician_name"),
            "preferred_time_period": profile.get("preferred_time_period"),
            "available_slots": [
                {
                    "start_time": slot["start_time"].isoformat(),
                    "end_time": slot["end_time"].isoformat(),
                    "formatted": slot["formatted"],
                }
                for slot in available_times
            ],
        }
        content = self._build_return_reminder(profile, days_since_last, available_times)
        recommendation_id = self.recommendation_repo.create_recommendation(
            user_id=user_id,
            recommendation_type="return_reminder",
            content=content,
            technician_id=profile.get("preferred_technician_id"),
            payload_json=payload,
            status="generated",
            dedupe_key=dedupe_key,
            trigger_reason="preferred_interval_reached",
            expires_at=utc_now_naive() + timedelta(days=7),
        )
        return [
            {
                "id": recommendation_id,
                "user_id": user_id,
                "recommendation_type": "return_reminder",
                "content": content,
                "technician_id": profile.get("preferred_technician_id"),
                "payload_json": payload,
                "status": "generated",
                "dedupe_key": dedupe_key,
                "is_sent": False,
            }
        ]

    def _find_existing_recommendation(self, user_id: str, dedupe_key: str) -> Optional[Dict[str, Any]]:
        for recommendation in self.recommendation_repo.get_pending_recommendations(user_id):
            if recommendation.get("dedupe_key") == dedupe_key and recommendation.get("status") in (
                "generated",
                "pending",
            ):
                return recommendation
        return None

    def _preferred_technician_slots(self, profile: Dict[str, Any], max_slots: int = 3) -> List[Dict[str, Any]]:
        technician_id = profile.get("preferred_technician_id")
        duration = profile.get("preferred_duration_minutes") or 60
        if not technician_id:
            return []

        slots: List[Dict[str, Any]] = []
        now = datetime.now()
        for day_offset in range(0, 3):
            date = now + timedelta(days=day_offset)
            start_hour = max(10, now.hour + 1) if day_offset == 0 else 10
            for hour in range(start_hour, 22):
                start = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                end = start + timedelta(minutes=int(duration))
                if self.appointment_service.is_technician_available(int(technician_id), start, end):
                    slots.append(
                        {
                            "start_time": start,
                            "end_time": end,
                            "formatted": start.strftime("%Y-%m-%d %H:%M"),
                        }
                    )
                    if len(slots) >= max_slots:
                        return slots
        return slots

    @staticmethod
    def _preferred_interval_days(profile: Dict[str, Any]) -> int:
        interval = profile.get("average_visit_interval_days")
        if interval:
            try:
                return max(7, min(45, int(round(float(interval) * 0.8))))
            except (TypeError, ValueError):
                pass
        return 30

    @staticmethod
    def _build_return_reminder(
        profile: Dict[str, Any],
        days_since_last: int,
        available_times: List[Dict[str, Any]],
    ) -> str:
        service = profile.get("preferred_service") or "massage service"
        duration = profile.get("preferred_duration_minutes") or 60
        technician = profile.get("preferred_technician_name")
        slot_text = ", ".join(slot["formatted"] for slot in available_times[:3])

        parts = [
            f"It has been {days_since_last} days since the user's last appointment.",
            f"The user's usual choice is {duration} minutes of {service}.",
        ]
        if technician and slot_text:
            parts.append(f"Preferred technician {technician} has available slots: {slot_text}.")
        elif technician:
            parts.append(f"The user's preferred technician is {technician}.")
        elif slot_text:
            parts.append(f"Available preferred-time slots: {slot_text}.")
        parts.append("Generated recommendation only; no message has been sent to the user.")
        return " ".join(parts)

    def start_scheduler(self) -> bool:
        """Start scheduled recommendation generation."""
        if self.is_running:
            logger.warning("Recommendation scheduler is already running")
            return False
        if schedule is None:
            logger.warning("Recommendation scheduler dependency is not installed")
            return False

        try:
            schedule.every().day.at("09:00").do(self.generate_recommendations_job)
            schedule.every().day.at("14:00").do(self.generate_recommendations_job)
            schedule.every().day.at("19:00").do(self.generate_recommendations_job)

            self.is_running = True

            def run_scheduler():
                logger.info("Recommendation scheduler started")
                while self.is_running:
                    schedule.run_pending()
                    time.sleep(60)
                logger.info("Recommendation scheduler stopped")

            self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
            self.scheduler_thread.start()
            return True
        except Exception as e:
            logger.error("Failed to start recommendation scheduler: %s", e)
            return False

    def stop_scheduler(self) -> bool:
        try:
            self.is_running = False
            if schedule is not None:
                schedule.clear()
            logger.info("Recommendation scheduler stopped")
            return True
        except Exception as e:
            logger.error("Failed to stop scheduler: %s", e)
            return False

    def run_immediate_check(self) -> Optional[List[Dict[str, Any]]]:
        logger.info("Running immediate recommendation generation")
        return self.generate_recommendations_job()

    def preview_return_reminder(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Build a recommendation preview without writing or sending."""
        try:
            profile = self.preference_service.recall(user_id)
        except Exception as exc:
            logger.warning("Preference recall unavailable for preview: %s", exc)
            profile = {
                "user_id": user_id or "default_user",
                "appointment_count": 0,
                "patterns": {"pattern": "no_data", "recommendation": "need_more_appointments"},
            }
        last_visit = profile.get("last_appointment_at")
        days_since_last = (
            (business_now_naive() - last_visit.replace(tzinfo=None)).days
            if isinstance(last_visit, datetime)
            else 0
        )
        available_times = self._preferred_technician_slots(profile)
        message = self._build_return_reminder(profile, days_since_last, available_times)
        return {
            "message": message,
            "technician_available_times": [
                {
                    "start_time": slot["start_time"].isoformat(),
                    "end_time": slot["end_time"].isoformat(),
                    "formatted": slot["formatted"],
                }
                for slot in available_times
            ],
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "thread_alive": self.scheduler_thread.is_alive() if self.scheduler_thread else False,
            "next_job": str(schedule.next_run()) if schedule is not None and schedule.jobs else None,
            "total_jobs": len(schedule.jobs) if schedule is not None else 0,
        }


if __name__ == "__main__":
    service = RecommendationService()
    service.start_scheduler()
    try:
        time.sleep(600)
    except KeyboardInterrupt:
        pass
    finally:
        service.stop_scheduler()
