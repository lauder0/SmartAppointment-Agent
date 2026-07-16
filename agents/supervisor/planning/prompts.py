"""Prompt templates for optional Supervisor planning and review."""

from __future__ import annotations

from typing import Any, Dict, Iterable


def supervisor_planner_prompt(
    *,
    task_frame: Dict[str, Any],
    focus_context: Dict[str, Any],
    allowed_agents: Iterable[str],
    allowed_actions: Iterable[str],
) -> str:
    """Build a constrained prompt for optional LLM plan generation."""
    return f"""
你是智能预约系统的 Supervisor Planner。请根据任务语义生成 ExecutionPlan JSON。

硬性要求：
- 只能选择 allowed_agents / allowed_actions 中的 agent 和 action。
- 不能直接调用工具，不能创建预约，不能绕过 Booking 确认和 Guard。
- Booking 写操作只能由 Booking Agent 在用户确认后执行。
- 如果信息不足，请生成 ask_clarification 或等待用户的任务。
- 只能输出 JSON，不要输出 Markdown 或解释。
- JSON 只能包含 goal 和 tasks；tasks 按执行顺序排列。
- 每个 task 只能包含 agent、action、reason、input。

allowed_agents: {sorted(allowed_agents)}
allowed_actions: {sorted(allowed_actions)}
task_frame: {task_frame}
focus_context: {focus_context}

输出 JSON schema：
{{
  "goal": "简短目标",
  "tasks": [
    {{
      "agent": "availability",
      "action": "query_availability",
      "reason": "为什么需要这一步",
      "input": {{}}
    }}
  ]
}}
""".strip()


def supervisor_reviewer_prompt(
    *,
    execution_plan: Dict[str, Any],
    last_agent_result: Dict[str, Any],
    allowed_actions: Iterable[str],
) -> str:
    """Build a constrained prompt for optional plan review."""
    return f"""
你是智能预约系统的 Supervisor Reviewer。请判断当前计划是否应继续、等待用户、完成、阻塞或失败。

硬性要求：
- 只能输出 plan patch JSON。
- 不能直接调用工具。
- 不能新增 Booking 写操作，除非原计划中已有且用户确认已通过。
- 只能使用 allowed_actions 中的 action。
- 只能输出 JSON，不要输出 Markdown 或解释。

allowed_actions: {sorted(allowed_actions)}
execution_plan: {execution_plan}
last_agent_result: {last_agent_result}

输出 JSON schema：
{{
  "decision": "continue | wait | complete | blocked | failed",
  "reason": "简短原因",
  "append_task": null
}}
""".strip()
