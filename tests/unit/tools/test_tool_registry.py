from __future__ import annotations

from tools.registry import TOOL_REGISTRY, get_tool_metadata
from tools.schemas import tool_result


def test_create_appointment_tool_metadata_marks_write_risk_and_idempotency():
    metadata = get_tool_metadata("create_appointment")

    assert metadata is not None
    assert metadata["permission"] == "write"
    assert metadata["risk_level"] == "high"
    assert metadata["requires_confirmation"] is True
    assert metadata["idempotent"] is True
    assert "idempotency_key_fields" in metadata


def test_all_registered_tools_have_stability_contract_fields():
    required = {"description", "permission", "timeout_ms", "retryable", "idempotent", "risk_level", "error_codes"}

    for name, metadata in TOOL_REGISTRY.items():
        missing = required - metadata.keys()
        assert not missing, f"{name} missing metadata fields: {sorted(missing)}"


def test_tool_result_includes_registry_metadata_without_breaking_legacy_fields():
    result = tool_result(True, data={"ok": True}, message="done", tool_name="query_availability")

    assert result["success"] is True
    assert result["data"] == {"ok": True}
    assert result["message"] == "done"
    assert result["error"] is None
    assert result["metadata"]["tool_name"] == "query_availability"
    assert result["metadata"]["permission"] == "read"
    assert result["metadata"]["risk_level"] == "low"
    assert result["metadata"]["idempotent"] is True
