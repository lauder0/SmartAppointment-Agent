"""Service catalog helpers exposed through the tools layer."""

from __future__ import annotations

from typing import Any

from services.service_catalog_service import ServiceCatalogService


def default_duration_for_service(service_type: str | None) -> int | None:
    """Return the catalog default duration for a concrete service name."""
    if not service_type:
        return None

    normalized = str(service_type).strip()
    if not normalized or normalized == "???":
        return None
    if normalized in {"???", "???", "???", "???"}:
        return None

    catalog = ServiceCatalogService()
    try:
        services: list[dict[str, Any]] = catalog.get_all_services()
    except Exception:
        services = []
    if not services:
        services = catalog.default_services

    for service in services:
        name = str(service.get("name") or "").strip()
        if not name:
            continue
        if normalized == name or name in normalized:
            try:
                duration = int(service.get("default_duration_minutes") or 0)
            except (TypeError, ValueError):
                return None
            return duration or None
    return None
