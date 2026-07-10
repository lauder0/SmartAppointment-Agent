from __future__ import annotations

import pytest

from tools import knowledge_tools


class FakeKnowledgeService:
    def __init__(self):
        self.initialized = False

    async def initialize(self):
        self.initialized = True

    async def search(self, query, top_k=3, category=None):
        return [
            {
                "id": 1,
                "content": "肩颈推拿 80 元。",
                "category": category or "服务项目",
                "score": 1.0,
            }
        ][:top_k]


@pytest.mark.asyncio
async def test_search_knowledge_tool_returns_documents(monkeypatch):
    monkeypatch.setattr(knowledge_tools, "KnowledgeService", FakeKnowledgeService)

    result = await knowledge_tools.search_knowledge.ainvoke(
        {
            "query": "肩颈推拿多少钱",
            "top_k": 1,
            "category": "服务项目",
        }
    )

    assert result["success"] is True
    assert result["data"]["count"] == 1
    assert result["data"]["documents"][0]["category"] == "服务项目"
