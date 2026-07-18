"""Bounded LLM tool-calling runtime for low-risk specialist work."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Iterable, List

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from config.model_provider import create_chat_model

from .policy import filter_allowed_tools, is_tool_allowed, tool_policy_summary
from .schemas import ToolCallingResult


logger = logging.getLogger(__name__)


async def run_tool_calling_agent(
    *,
    agent_name: str,
    action: str,
    state: Dict[str, Any],
    prompt: str,
    allowed_tools: Iterable[BaseTool],
    system_prompt: str | None = None,
    max_iterations: int = 5,
) -> ToolCallingResult:
    """Run a short, policy-constrained tool-calling loop.

    The runtime only receives policy-approved tools, rejects high-risk or write
    tools again at execution time, and returns trace data without mutating
    graph state directly.
    """
    _ = state  # reserved for future trace/context hooks
    tools = filter_allowed_tools(allowed_tools, agent_name=agent_name, action=action)
    if not tools:
        return {
            "success": False,
            "answer": "",
            "facts": {},
            "tool_calls": [],
            "tool_results": {},
            "error": "no_allowed_tools",
        }

    messages: List[Any] = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    tool_by_name = {tool.name: tool for tool in tools}
    trace_calls: List[Dict[str, Any]] = []
    tool_results: Dict[str, Any] = {}

    try:
        llm = create_chat_model(temperature=0)
        if not hasattr(llm, "bind_tools"):
            return {
                "success": False,
                "answer": "",
                "facts": {},
                "tool_calls": [],
                "tool_results": {},
                "error": "model_does_not_support_bind_tools",
            }
        model = llm.bind_tools(tools)

        for _iteration in range(max_iterations):
            message = await model.ainvoke(messages)
            messages.append(message)
            tool_calls = list(getattr(message, "tool_calls", None) or [])
            if not tool_calls:
                answer = _message_content(message)
                return {
                    "success": True,
                    "answer": answer,
                    "facts": _extract_json_facts(answer),
                    "tool_calls": trace_calls,
                    "tool_results": tool_results,
                    "requires_user_input": False,
                    "next_expected_user_action": None,
                }

            for call in tool_calls:
                name = str(call.get("name") or "")
                args = call.get("args") or {}
                call_id = str(call.get("id") or name)
                trace_calls.append({"name": name, "args": args, "id": call_id})
                if not is_tool_allowed(name, agent_name, action) or name not in tool_by_name:
                    result = {
                        "success": False,
                        "error": "tool_not_allowed",
                        "policy": tool_policy_summary(agent_name, action),
                    }
                else:
                    result = await _invoke_tool(tool_by_name[name], args)
                tool_results[name] = result
                messages.append(
                    ToolMessage(
                        content=json.dumps(result, ensure_ascii=False, default=str),
                        tool_call_id=call_id,
                    )
                )

        return {
            "success": False,
            "answer": "",
            "facts": {},
            "tool_calls": trace_calls,
            "tool_results": tool_results,
            "error": "max_iterations_exceeded",
        }
    except Exception as exc:
        logger.exception("Tool-calling runtime failed for %s/%s", agent_name, action)
        return {
            "success": False,
            "answer": "",
            "facts": {},
            "tool_calls": trace_calls,
            "tool_results": tool_results,
            "error": str(exc),
        }


async def _invoke_tool(tool: BaseTool, args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = await tool.ainvoke(args)
        return result if isinstance(result, dict) else {"success": True, "data": result}
    except Exception as exc:
        return {"success": False, "error": str(exc), "message": f"{tool.name} failed"}


def _message_content(message: Any) -> str:
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    return json.dumps(content, ensure_ascii=False, default=str)


def _extract_json_facts(text: str) -> Dict[str, Any]:
    stripped = (text or "").strip()
    if not stripped:
        return {}
    try:
        parsed = json.loads(stripped)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}
