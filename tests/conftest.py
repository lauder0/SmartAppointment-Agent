from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from db.db_router import DatabaseRouter
from services.appointment_service import AppointmentService
from services.session_state_store import MemorySessionStateStore


@pytest.fixture
def tmp_db_url(tmp_path: Path) -> str:
    return "sqlite:///" + str(tmp_path / "test.db").replace("\\", "/")


@pytest.fixture
def db_router(tmp_db_url: str):
    router = DatabaseRouter(tmp_db_url)
    try:
        yield router
    finally:
        router.close()


@pytest.fixture
def appointment_service(tmp_db_url: str):
    service = AppointmentService(tmp_db_url)
    try:
        yield service
    finally:
        service.db_router.close()


@pytest.fixture
def seeded_technician(db_router: DatabaseRouter) -> int:
    return db_router.technicians.add_technician(
        name="测试技师",
        gender="女",
        strength="肩颈放松",
    )


@pytest.fixture
def seeded_service(db_router: DatabaseRouter) -> int:
    return db_router.appointments.add_service(
        name="肩颈推拿",
        default_duration_minutes=60,
        price_cents=8000,
        description="测试服务",
    )


@pytest.fixture
def fixed_future_time() -> datetime:
    return datetime(2026, 6, 11, 15, 0)


@pytest.fixture
def one_hour() -> timedelta:
    return timedelta(minutes=60)


@pytest.fixture
def memory_session_store() -> MemorySessionStateStore:
    return MemorySessionStateStore(ttl_seconds=60)
