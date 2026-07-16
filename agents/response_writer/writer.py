"""Final response writer for Supervisor-driven multi-agent turns."""

from __future__ import annotations

import os
from typing import Any, Dict, List

from agents.response_writer.composer import composer
from config.model_provider import create_chat_model

from .prompts import final_response_prompt
from .schema import WriterInput, WriterOutput, summarize_writer_input


BOOKING_RESPONSE_TYPES = {
    "booking_missing_slots",
    "booking_confirmation",
    "booking_recommendation",
    "booking_cancelled",
    "booking_unclear_confirmation",
    "booking_guard_missing",
    "booking_guard_invalid",
    "booking_guard_time_invalid",
    "booking_guard_technician_unavailable",
    "booking_success",
    "booking_failed",
}


class ResponseWriter:
    """Compose one user-facing answer from a turn's structured AgentResults."""

    async def write(self, writer_input: WriterInput) -> WriterOutput:
        results = list(writer_input.get("turn_results") or [])
        parts: List[str] = []
        skipped = 0

        for result in results:
            body = await self._render_result_body(writer_input, result)
            if not body:
                skipped += 1
                continue
            if body not in parts:
                parts.append(body)

        final_response = "\n\n".join(parts) if parts else writer_input.get("final_response")
        label = self._select_label(results, final_response)
        strategy = self._strategy_for(writer_input, results)
        if final_response and self._should_polish_with_llm(strategy, results):
            polished = await self._polish_response(writer_input, final_response, results)
            if polished:
                final_response = polished
                strategy = f"{strategy}+llm_polish"
        if final_response:
            final_response = self._with_single_prefix(label, final_response)

        return {
            "final_response": final_response,
            "selected_label": label,
            "rendered_result_count": len(parts),
            "skipped_result_count": skipped,
            "writer_strategy": strategy,
            "input_summary": summarize_writer_input(writer_input),
        }

    async def _render_result_body(self, writer_input: WriterInput, result: Dict[str, Any]) -> str | None:
        if result.get("suppress_response") or (result.get("facts") or {}).get("suppress_response"):
            return None

        response_type = result.get("response_type")
        facts = dict(result.get("facts") or {})
        message = result.get("message")
        context = {
            "execution_plan": writer_input.get("execution_plan") or {},
            "focus_context": writer_input.get("shared_focus_context") or {},
            "agent_name": result.get("agent_name"),
        }

        if message and response_type not in BOOKING_RESPONSE_TYPES:
            return self._strip_reply_prefix(str(message))

        if response_type:
            if response_type in BOOKING_RESPONSE_TYPES:
                rendered = composer.reply(response_type, facts, context)
            else:
                rendered = await composer.areply(response_type, facts, context)
            body = self._strip_reply_prefix(rendered)
            if body:
                return body
            if message:
                return self._strip_reply_prefix(str(message))
            return None

        if message:
            return self._strip_reply_prefix(str(message))
        return None

    def _select_label(self, results: List[Dict[str, Any]], final_response: str | None) -> str:
        if any((result.get("response_type") or "") in BOOKING_RESPONSE_TYPES for result in results):
            return "预约机器人"
        if any(
            result.get("agent_name") == "fallback"
            and (
                "预约机器人" in str(result.get("message") or "")
                or "预约信息正在等待" in str(result.get("message") or "")
            )
            for result in results
        ):
            return "预约机器人"
        if any(result.get("agent_name") == "recommendation" for result in results):
            return "推荐机器人"
        if final_response and "预约" in final_response and "请问是否确认" in final_response:
            return "预约机器人"
        return "咨询机器人"
    def _strategy_for(self, writer_input: WriterInput, results: List[Dict[str, Any]]) -> str:
        plan = writer_input.get("execution_plan") or {}
        if plan.get("status") == "waiting_user":
            return "waiting_user"
        if any((result.get("response_type") or "") in BOOKING_RESPONSE_TYPES for result in results):
            return "booking_template_first"
        if len(results) > 1:
            return "multi_result_summary"
        return "single_result"

    def _with_single_prefix(self, label: str, body: str) -> str:
        cleaned = self._strip_reply_prefix(body)
        return f"[REPLY][{label}]{cleaned}"

    def _should_polish_with_llm(self, strategy: str, results: List[Dict[str, Any]]) -> bool:
        if os.getenv("ENABLE_RESPONSE_WRITER_LLM", "").strip().lower() not in {"1", "true", "yes"}:
            return False
        if strategy == "booking_template_first":
            return False
        return not any((result.get("response_type") or "") in BOOKING_RESPONSE_TYPES for result in results)

    async def _polish_response(
        self,
        writer_input: WriterInput,
        template_response: str,
        results: List[Dict[str, Any]],
    ) -> str | None:
        payload = {
            "template_response": self._strip_reply_prefix(template_response),
            "execution_plan": writer_input.get("execution_plan") or {},
            "shared_focus_context": writer_input.get("shared_focus_context") or {},
            "result_summaries": [
                {
                    "agent_name": result.get("agent_name"),
                    "result_type": result.get("result_type"),
                    "response_type": result.get("response_type"),
                    "facts": result.get("facts") or {},
                }
                for result in results
            ],
        }
        try:
            message = await create_chat_model(temperature=0.2).ainvoke(final_response_prompt(payload))
        except Exception:
            return None
        polished = self._strip_reply_prefix(str(getattr(message, "content", "")).strip())
        if not polished or len(polished) < 4:
            return None
        return polished

    def _strip_reply_prefix(self, text: str) -> str:
        cleaned = (text or "").strip()
        if cleaned.startswith("[REPLY]["):
            first_end = cleaned.find("]")
            second_end = cleaned.find("]", first_end + 1) if first_end != -1 else -1
            if second_end != -1:
                return cleaned[second_end + 1 :].strip()
        for prefix in ("[咨询机器人]", "[预约机器人]", "[推荐机器人]", "[智能预约助手]"):
            if cleaned.startswith(prefix):
                return cleaned[len(prefix) :].strip()
        return cleaned


writer = ResponseWriter()

