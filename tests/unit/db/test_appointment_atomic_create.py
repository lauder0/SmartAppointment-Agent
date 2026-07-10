from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

from db.db_router import DatabaseRouter
from services.appointment_service import AppointmentService


class AppointmentAtomicCreateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_url = f"sqlite:///{Path(self.tmp.name) / 'appointments.db'}"
        self.router = DatabaseRouter(self.db_url)
        self.technician_id = self.router.technicians.add_technician(
            name="测试技师",
            gender="女",
            strength="肩颈放松",
        )
        self.router.appointments.add_service(
            name="肩颈推拿",
            default_duration_minutes=60,
            price_cents=8000,
            description="测试服务",
        )
        self.service = AppointmentService(self.db_url)
        self.start = datetime(2026, 6, 11, 15, 0)
        self.end = self.start + timedelta(minutes=60)

    def tearDown(self):
        self.router.close()
        self.service.db_router.close()
        self.tmp.cleanup()

    def _save(self, key: str, start: datetime | None = None, duration_minutes: int = 60) -> bool:
        start = start or self.start
        end = start + timedelta(minutes=duration_minutes)
        return self.service.save_appointment(
            technician_id=str(self.technician_id),
            start_time=start,
            end_time=end,
            appointment_history={
                "project": "肩颈推拿",
                "duration": f"{duration_minutes}分钟",
                "gender": "女",
            },
            session_id="s1",
            user_id="u1",
            idempotency_key=key,
        )

    def test_atomic_create_writes_appointment_and_busy_schedule(self):
        self.assertTrue(self._save("atomic-key-1"))

        appointments = self.router.appointments.get_user_appointments("u1")
        schedules = self.router.technicians.get_technician_schedules(self.technician_id, self.start)

        self.assertEqual(len(appointments), 1)
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0]["status"], "busy")
        self.assertEqual(schedules[0]["appointment_id"], appointments[0]["id"])

    def test_idempotent_replay_does_not_create_duplicate_rows(self):
        self.assertTrue(self._save("same-key"))
        self.assertTrue(self._save("same-key"))

        appointments = self.router.appointments.get_user_appointments("u1")
        schedules = self.router.technicians.get_technician_schedules(self.technician_id, self.start)

        self.assertEqual(len(appointments), 1)
        self.assertEqual(len(schedules), 1)

    def test_overlapping_appointment_is_blocked(self):
        self.assertTrue(self._save("first-key"))
        self.assertFalse(self._save("overlap-key", start=self.start + timedelta(minutes=30)))

        appointments = self.router.appointments.get_user_appointments("u1")
        schedules = self.router.technicians.get_technician_schedules(self.technician_id, self.start)

        self.assertEqual(len(appointments), 1)
        self.assertEqual(len(schedules), 1)

    def test_concurrent_overlap_allows_only_one_create(self):
        keys = ["concurrent-key-1", "concurrent-key-2"]
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(self._save, keys))

        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 1)
        appointments = self.router.appointments.get_user_appointments("u1")
        schedules = self.router.technicians.get_technician_schedules(self.technician_id, self.start)
        self.assertEqual(len(appointments), 1)
        self.assertEqual(len(schedules), 1)


if __name__ == "__main__":
    unittest.main()
