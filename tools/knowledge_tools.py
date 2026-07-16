"""Knowledge retrieval tools."""

from __future__ import annotations

from langchain_core.tools import tool

from services.knowledge_service import KnowledgeService
from .schemas import SearchKnowledgeInput, tool_result


def _tool_result(*args, **kwargs) -> dict:
    return tool_result(*args, tool_name="search_knowledge", **kwargs)


@tool(args_schema=SearchKnowledgeInput)
async def search_knowledge(query: str, top_k: int = 3, category: str | None = None) -> dict:
    """Search static massage-shop knowledge such as services, prices, address, policies, and hours."""
    try:
        service = KnowledgeService()
        if not service.initialized:
            await service.initialize()
        docs = await service.search(query, top_k=top_k, category=category)
        return _tool_result(
            True,
            data={"query": query, "documents": docs, "count": len(docs)},
            message="知识库检索成功",
        )
    except Exception as e:
        return _tool_result(False, data={"query": query}, message="知识库检索失败", error=str(e))
