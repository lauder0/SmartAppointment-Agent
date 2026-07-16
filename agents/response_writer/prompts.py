"""Prompt templates for optional final response rewriting.

The production path is template/fact first. These prompts are intentionally
small and constrained so an LLM can only polish wording, not invent business
facts or bypass booking guards.
"""

from __future__ import annotations

from typing import Any, Dict


def final_response_prompt(payload: Dict[str, Any]) -> str:
    """Build a constrained prompt for optional final response polishing."""
    return f"""
你是按摩门店智能预约系统的最终回复表达层。请基于结构化事实生成一段自然、简洁的中文回复。

硬性要求：
- 只能使用 payload 中已有事实，不要编造项目、价格、技师、时间、排班或预约结果。
- 不要输出机器人标签，不要输出 [REPLY]。
- Booking confirmation / booking_created 的关键字段必须原样保留。
- 如果系统正在等待用户，必须明确下一步需要用户补充或确认什么。
- 如果 payload 中已经有 template_response，优先保持其事实和顺序，只做轻微润色。

payload:
{payload}
""".strip()
