from __future__ import annotations

import pytest

from services.knowledge_service import KnowledgeService


def make_service() -> KnowledgeService:
    service = KnowledgeService.__new__(KnowledgeService)
    service.RRF_K = KnowledgeService.RRF_K
    return service


def test_reciprocal_rank_fusion_promotes_cross_channel_matches():
    service = make_service()

    fused_scores = service._reciprocal_rank_fusion(
        [
            ({1: 1, 2: 2}, service.VECTOR_WEIGHT),
            ({2: 1}, service.KEYWORD_WEIGHT),
        ]
    )

    assert fused_scores[2] > fused_scores[1]


@pytest.mark.asyncio
async def test_search_uses_rrf_ranking_for_hybrid_candidates(monkeypatch):
    service = make_service()
    service.initialized = True
    service.index = object()

    documents = [
        {"id": 1, "content": "vector only", "category": "service", "keywords": []},
        {"id": 2, "content": "hybrid", "category": "service", "keywords": []},
    ]

    class FakeKnowledgeRepo:
        def get_all_documents(self):
            return documents

    service.db = FakeKnowledgeRepo()
    monkeypatch.setattr(service, "_search_vector", lambda query, allowed_ids: {1: 0.99, 2: 0.98})
    monkeypatch.setattr(service, "_calculate_keyword_scores", lambda query, docs: {2: 10.0})

    results = await service.search("hybrid query", top_k=2)

    assert [doc["id"] for doc in results] == [2, 1]
    assert results[0]["retrieval_method"] == "hybrid"
    assert results[0]["vector_rank"] == 2
    assert results[0]["keyword_rank"] == 1
    assert results[0]["score"] == results[0]["rrf_score"]
