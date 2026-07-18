"""Schemas for controlled LLM tool-calling results."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class ToolCallingResult(TypedDict, total=False):
    """Normalized result returned by the shared tool-calling runtime."""

    success: bool
    answer: str
    facts: Dict[str, Any]
    tool_calls: List[Dict[str, Any]]
    tool_results: Dict[str, Any]
    error: Optional[str]
    requires_user_input: bool
    next_expected_user_action: Optional[str]
