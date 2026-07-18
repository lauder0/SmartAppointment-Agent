"""Tool access policy for local LLM tool-calling."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from langchain_core.tools import BaseTool

from tools.availability_tools import query_availability
from tools.knowledge_tools import search_knowledge
from tools.preference_tools import recall_preferences
from tools.recommendation_tools import rank_technicians, recommend_service_item
from tools.registry import get_tool_metadata
from tools.technician_read_tools import (
    check_technician_available,
    get_all_technicians,
    get_technician_by_name,
)
from tools.weather_tools import get_weather


TOOL_BY_NAME: Dict[str, BaseTool] = {
    tool.name: tool
    for tool in (
        search_knowledge,
        query_availability,
        get_all_technicians,
        get_technician_by_name,
        check_technician_available,
        recall_preferences,
        recommend_service_item,
        rank_technicians,
        get_weather,
    )
}


AGENT_ALLOWED_TOOL_NAMES: Dict[str, Dict[str, List[str]]] = {
    "consultation": {
        "answer_knowledge": [
            "search_knowledge",
            "get_all_technicians",
            "get_technician_by_name",
            "recommend_service_item",
            "get_weather",
        ],
    },
    "availability": {
        "query_availability": [
            "query_availability",
            "get_all_technicians",
            "get_technician_by_name",
        ],
    },
    "recommendation": {
        "recommend_service": [
            "recommend_service_item",
            "search_knowledge",
        ],
        "generate_recommendation": [
            "query_availability",
            "get_all_technicians",
            "recall_preferences",
            "rank_technicians",
        ],
        "replace_recommendation": [
            "recall_preferences",
            "rank_technicians",
        ],
    },
}


def get_allowed_tool_names(agent_name: str, action: str) -> List[str]:
    """Return policy-approved tool names for an agent/action pair."""
    return list((AGENT_ALLOWED_TOOL_NAMES.get(agent_name) or {}).get(action) or [])


def get_allowed_tools(agent_name: str, action: str) -> List[BaseTool]:
    """Return policy-approved LangChain tool instances."""
    return [TOOL_BY_NAME[name] for name in get_allowed_tool_names(agent_name, action) if name in TOOL_BY_NAME]


def is_tool_allowed(tool_name: str, agent_name: str, action: str) -> bool:
    """Validate that a tool can be selected by the LLM in this context."""
    if tool_name not in get_allowed_tool_names(agent_name, action):
        return False
    metadata = get_tool_metadata(tool_name) or {}
    if metadata.get("requires_confirmation"):
        return False
    if metadata.get("permission") == "write":
        return False
    if metadata.get("risk_level") == "high":
        return False
    if metadata.get("llm_callable") is False:
        return False
    return True


def filter_allowed_tools(
    tools: Iterable[BaseTool],
    *,
    agent_name: str,
    action: str,
) -> List[BaseTool]:
    """Filter arbitrary tool instances through the shared policy."""
    return [tool for tool in tools if is_tool_allowed(tool.name, agent_name, action)]


def tool_policy_summary(agent_name: str, action: str) -> Dict[str, Any]:
    """Return a compact policy view for traces and tests."""
    return {
        "agent_name": agent_name,
        "action": action,
        "allowed_tools": get_allowed_tool_names(agent_name, action),
    }
