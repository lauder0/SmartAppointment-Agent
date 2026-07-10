from __future__ import annotations

import pytest

from api import knowledge


class FakeKnowledgeService:
    calls: list[tuple] = []

    def __init__(self):
        self.initialized = False

    async def initialize(self):
        self.initialized = True

    async def add_document(self, content, category, keywords=None):
        self.calls.append(("add", content, category, keywords))
        return True

    async def update_document(self, doc_id, content=None, category=None, keywords=None):
        self.calls.append(("update", doc_id, content, category, keywords))
        return True

    async def search(self, query, top_k=3, category=None):
        self.calls.append(("search", query, top_k, category))
        return [
            {
                "id": 1,
                "content": "肩颈推拿 80 元。",
                "category": category or "服务项目",
                "rank": 1,
            }
        ][:top_k]


@pytest.fixture(autouse=True)
def fake_knowledge_service(monkeypatch):
    FakeKnowledgeService.calls = []
    monkeypatch.setattr("services.knowledge_service.KnowledgeService", FakeKnowledgeService)


@pytest.mark.asyncio
async def test_add_knowledge_accepts_page_payload():
    result = await knowledge.add_knowledge(
        knowledge.KnowledgeItem(
            content="营业时间是每天 9 点到 22 点。",
            category="营业时间",
            keywords=["营业时间", "开门"],
        )
    )

    assert result["status"] == "success"
    assert FakeKnowledgeService.calls == [
        ("add", "营业时间是每天 9 点到 22 点。", "营业时间", ["营业时间", "开门"])
    ]


@pytest.mark.asyncio
async def test_add_knowledge_keeps_question_answer_payload_compatible():
    result = await knowledge.add_knowledge(
        knowledge.KnowledgeItem(
            question="营业时间？",
            answer="每天 9 点到 22 点。",
            category="营业时间",
        )
    )

    assert result["status"] == "success"
    assert FakeKnowledgeService.calls == [
        ("add", "问题: 营业时间？\n答案: 每天 9 点到 22 点。", "营业时间", [])
    ]


@pytest.mark.asyncio
async def test_update_knowledge_accepts_page_payload():
    result = await knowledge.update_knowledge(
        7,
        knowledge.KnowledgeItem(
            content="肩颈推拿 80 元。",
            category="服务项目",
            keywords=["肩颈", "价格"],
        ),
    )

    assert result["status"] == "success"
    assert FakeKnowledgeService.calls == [
        ("update", 7, "肩颈推拿 80 元。", "服务项目", ["肩颈", "价格"])
    ]


@pytest.mark.asyncio
async def test_search_knowledge_returns_page_contract_fields():
    result = await knowledge.search_knowledge(
        knowledge.SearchRequest(query="肩颈价格", top_k=1, category="服务项目")
    )

    assert result["query"] == "肩颈价格"
    assert result["results"] == result["data"]
    assert result["total_found"] == 1
    assert result["count"] == 1
    assert FakeKnowledgeService.calls == [("search", "肩颈价格", 1, "服务项目")]
