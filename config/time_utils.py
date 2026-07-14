"""Small time helpers with explicit timezone policy."""

from __future__ import annotations

from datetime import UTC, datetime

from config.time_config import time_config


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for system events."""
    return datetime.now(UTC)


def utc_now_naive() -> datetime:
    """Return UTC without tzinfo for existing SQLAlchemy DateTime columns."""
    return utc_now().replace(tzinfo=None)


def utc_now_iso() -> str:
    """Return a compact UTC ISO timestamp for trace/state strings."""
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def business_now_naive() -> datetime:
    """Return local business time without tzinfo for appointment-time comparisons."""
    return time_config.now().replace(tzinfo=None)
