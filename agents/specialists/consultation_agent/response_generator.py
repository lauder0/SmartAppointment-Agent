"""Consultation response generation for the LangGraph workflow."""

from __future__ import annotations

from typing import AsyncGenerator

from langchain_core.language_models.chat_models import BaseChatModel


class ResponseGenerator:
    """Generate customer-facing consultation answers from retrieved documents."""

    def __init__(self, llm: BaseChatModel):
        self.llm = llm

    async def generate_response(self, user_input: str, knowledge_docs: list[dict]) -> str:
        try:
            prompt = self._build_consultation_prompt(user_input, knowledge_docs)
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            return str(response.content)
        except Exception as exc:
            return f"抱歉，处理您的问题时出现错误：{exc}"

    async def generate_response_stream(
        self,
        user_input: str,
        knowledge_docs: list[dict],
    ) -> AsyncGenerator[str, None]:
        answer = await self.generate_response(user_input, knowledge_docs)
        yield "[REPLY][咨询机器人]"
        for char in answer:
            yield char

    def create_unrelated_message(self) -> str:
        return "[THOUGHT][咨询机器人] 这个问题不是咨询类问题，我将交回给意图识别节点处理。"

    def _build_consultation_prompt(self, user_input: str, knowledge_docs: list[dict]) -> str:
        knowledge_context = self._format_knowledge_docs(knowledge_docs)
        return (
            "你是按摩预约门店的咨询助手。请基于给定知识库内容回答用户问题。"
            "回答要简洁、友好、直接；如果知识库没有明确依据，请说明暂时无法确认，"
            "并引导用户提供服务项目、时间或技师偏好以继续预约。\n\n"
            f"用户问题：{user_input}\n\n"
            f"知识库内容：\n{knowledge_context}"
        )

    def _format_knowledge_docs(self, knowledge_docs: list[dict]) -> str:
        if not knowledge_docs:
            return "未检索到相关知识。"

        lines = []
        for index, doc in enumerate(knowledge_docs, start=1):
            category = doc.get("category") or "未分类"
            content = doc.get("content") or ""
            lines.append(f"{index}. [{category}] {content}")
        return "\n".join(lines)
