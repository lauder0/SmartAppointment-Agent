"""Controlled plan review helpers.

This module is the Supervisor's explicit "think after child Agent result"
boundary. It is deterministic by default; an optional LLM reviewer can produce
the same decision shape for trace-only review when explicitly enabled.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Literal, TypedDict

from config.model_provider import create_chat_model
from .plan_schema import normalize_execution_plan
from .prompts import supervisor_reviewer_prompt
from agents.supervisor.orchestration.agent_registry import ACTION_TO_AGENT


ReviewDecision = Literal["continue", "wait", "complete", "blocked", "failed"]


class PlanReview(TypedDict, total=False):
    decision: ReviewDecision
    reason: str
    plan_id: str
    current_task_id: str | None
    next_task_id: str | None
    last_agent: str | None
    last_result_type: str | None
    source: str


def review_plan_after_result(plan: Dict[str, Any], last_agent_result: Dict[str, Any] | None) -> PlanReview:
    """Summarize Supervisor's post-result decision for traceability."""
    normalized = normalize_execution_plan(plan)
    result = last_agent_result or {}
    status = normalized.get("status")
    next_task_id = normalized.get("current_task_id")

    if status == "waiting_user":
        decision: ReviewDecision = "wait"
        reason = normalized.get("next_expected_user_action") or result.get("result_type") or "requires_user_input"
    elif status == "blocked":
        decision = "blocked"
        reason = normalized.get("blocked_reason") or result.get("error") or "blocked"
    elif status == "failed":
        decision = "failed"
        reason = normalized.get("blocked_reason") or result.get("error") or "failed"
    elif status == "completed":
        decision = "complete"
        reason = normalized.get("completion_reason") or "all_required_tasks_completed"
    else:
        decision = "continue" if next_task_id else "complete"
        reason = "next_plan_task_ready" if next_task_id else "no_next_task"

    return {
        "decision": decision,
        "reason": str(reason),
        "plan_id": normalized.get("plan_id"),
        "current_task_id": normalized.get("current_task_id"),
        "next_task_id": next_task_id,
        "last_agent": result.get("agent_name"),
        "last_result_type": result.get("result_type"),
        "source": "deterministic_reviewer",
    }


async def review_plan_after_result_with_optional_llm(
    plan: Dict[str, Any],
    last_agent_result: Dict[str, Any] | None,
) -> PlanReview:
    """Return deterministic review, optionally decorated by validated LLM review."""
    deterministic = review_plan_after_result(plan, last_agent_result)
    if not _should_call_llm_reviewer(plan, last_agent_result):
        return deterministic
    try:
        prompt = supervisor_reviewer_prompt(
            execution_plan=normalize_execution_plan(plan),
            last_agent_result=last_agent_result or {},
            allowed_actions=set(ACTION_TO_AGENT.keys()),
        )
        message = await create_chat_model(temperature=0).ainvoke(prompt)
        parsed = _extract_json_object(str(getattr(message, "content", "")))
        llm_review = _validate_llm_review(parsed, deterministic)
        return llm_review or deterministic
    except Exception:
        return deterministic


def _should_call_llm_reviewer(plan: Dict[str, Any], last_agent_result: Dict[str, Any] | None) -> bool:
    if os.getenv("ENABLE_SUPERVISOR_LLM_REVIEWER", "").strip().lower() not in {"1", "true", "yes"}:
        return False
    normalized = normalize_execution_plan(plan)
    result = last_agent_result or {}
    return (
        normalized.get("status") == "running"
        and len(normalized.get("tasks") or []) >= 3
        and result.get("status") == "completed"
    )


def _validate_llm_review(parsed: Dict[str, Any] | None, fallback: PlanReview) -> PlanReview | None:
    if not isinstance(parsed, dict):
        return None
    decision = str(parsed.get("decision") or "")
    if decision not in {"continue", "wait", "complete", "blocked", "failed"}:
        return None
    # The LLM reviewer is trace-only; it cannot contradict deterministic wait,
    # blocked, or failed decisions because those are safety/control states.
    if fallback.get("decision") in {"wait", "blocked", "failed"} and decision != fallback.get("decision"):
        return None
    return {
        **fallback,
        "decision": decision,  # type: ignore[typeddict-item]
        "reason": str(parsed.get("reason") or fallback.get("reason") or "llm_supervisor_reviewer"),
        "source": "llm_supervisor_reviewer",
    }


def _extract_json_object(text: str) -> Dict[str, Any] | None:
    content = (text or "").strip()
    if not content:
        return None
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", content, flags=re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None
