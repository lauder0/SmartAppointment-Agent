# services/knowledge_service.py

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Dict, List

import faiss
import numpy as np

from db.db_router import DatabaseRouter
from .text_embedding import embed_input

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Knowledge base service backed by database storage and hybrid retrieval."""

    VECTOR_WEIGHT = 0.65
    KEYWORD_WEIGHT = 0.35
    RRF_K = 60

    def __init__(self, db_path: str = "sqlite:///data/smart_appointment.db"):
        self.db_router = DatabaseRouter(db_path)
        self.db = self.db_router.knowledge
        self.index = None
        self.document_ids: List[int] = []
        self.initialized = False

        self.default_knowledge = [
            {
                "content": "我们推拿房的营业时间是每天上午9点到晚上10点，全年无休。",
                "category": "营业时间",
                "keywords": ["营业时间", "开门", "关门", "几点", "时间"],
            },
            {
                "content": "我们提供多种推拿服务：全身推拿（120元/60分钟）、肩颈推拿（80元/30分钟）、足底按摩（100元/45分钟）、背部推拿（90元/40分钟）。",
                "category": "服务项目",
                "keywords": ["服务", "推拿", "按摩", "价格", "收费", "多少钱"],
            },
            {
                "content": "我们有专业的男、女技师为您服务。所有技师都经过专业培训，持有相关资格证书，您可以根据个人偏好选择男技师或女技师。",
                "category": "技师信息",
                "keywords": ["技师", "师傅", "男", "女", "专业", "资格"],
            },
            {
                "content": "我们店的位置位于北京市海淀区中关村大街27号，交通便利，地铁2号线A口向北步行100米即可到达。",
                "category": "门店地址",
                "keywords": ["地址", "门店信息", "到达方式", "交通"],
            },
            {
                "content": "全身推拿能够舒缓全身肌肉疲劳，促进血液循环，缓解压力，特别适合久坐办公和体力劳动后放松。",
                "category": "服务介绍",
                "keywords": ["全身推拿", "效果", "作用", "好处", "适合"],
            },
            {
                "content": "肩颈推拿专门针对颈椎和肩部问题，能缓解颈椎疼痛、肩膀僵硬等问题，特别推荐给长期使用电脑的人群。",
                "category": "服务介绍",
                "keywords": ["肩颈推拿", "颈椎", "肩膀", "疼痛", "僵硬"],
            },
            {
                "content": "足底按摩通过刺激足部穴位，能够调节全身气血运行，缓解疲劳，改善睡眠质量。",
                "category": "服务介绍",
                "keywords": ["足底按摩", "脚", "穴位", "睡眠", "疲劳"],
            },
            {
                "content": "我们的技师都有3年以上专业经验，定期接受培训以确保服务质量。我们注重客户体验，力求为每位客户提供舒适的服务。",
                "category": "服务质量",
                "keywords": ["经验", "专业", "培训", "质量", "舒适"],
            },
            {
                "content": "如需取消或更改预约，请提前至少2小时通知我们。临时取消可能会产生一定费用。",
                "category": "预约政策",
                "keywords": ["取消", "更改", "改期", "退约", "政策"],
            },
            {
                "content": "我们提供会员卡服务，充值500元送50元，充值1000元送150元。会员还可享受预约优先权和生日优惠。",
                "category": "会员服务",
                "keywords": ["会员", "充值", "优惠", "折扣", "生日"],
            },
        ]

    async def initialize(self):
        """Initialize the knowledge service and vector index."""
        try:
            existing_docs = self.db.get_all_documents()

            if not existing_docs:
                logger.info("Knowledge base is empty, creating default documents")
                await self._create_default_knowledge()
            else:
                logger.info("Loaded %s knowledge documents from database", len(existing_docs))

            await self._build_vector_index()
            self.initialized = True
            logger.info("Knowledge service initialized")
        except Exception as e:
            logger.error("Knowledge service initialization failed: %s", e)
            raise

    async def _create_default_knowledge(self):
        """Create default knowledge documents."""
        for knowledge in self.default_knowledge:
            try:
                text_for_embedding = f"{knowledge['content']} {' '.join(knowledge['keywords'])}"
                embedding = embed_input(text_for_embedding)
                self.db.add_document(
                    content=knowledge["content"],
                    category=knowledge["category"],
                    keywords=knowledge["keywords"],
                    embedding=embedding,
                )
                logger.debug("Added default knowledge: %s...", knowledge["content"][:50])
            except Exception as e:
                logger.error("Failed to add default knowledge: %s", e)

    async def _build_vector_index(self):
        """Build the FAISS vector index."""
        try:
            documents = self.db.get_all_documents()
            if not documents:
                logger.warning("No documents available for vector index")
                return

            embeddings = []
            self.document_ids = []

            for doc in documents:
                if doc.get("embedding"):
                    embedding = doc["embedding"]
                else:
                    logger.warning("Document %s has no embedding, generating one", doc["id"])
                    text_for_embedding = f"{doc['content']} {' '.join(doc.get('keywords', []))}"
                    embedding = embed_input(text_for_embedding)
                    self.db.update_document(doc["id"], embedding=embedding)

                embeddings.append(embedding)
                self.document_ids.append(doc["id"])

            if embeddings:
                embeddings_array = np.array(embeddings).astype("float32")
                dimension = embeddings_array.shape[1]
                self.index = faiss.IndexFlatIP(dimension)
                self.index.add(embeddings_array)
                logger.info("Built vector index with %s vectors", len(embeddings))
            else:
                logger.warning("No valid embeddings available for vector index")
        except Exception as e:
            logger.error("Failed to build vector index: %s", e)
            raise

    async def search(self, query: str, top_k: int = 3, category: str = None) -> List[Dict]:
        """Search relevant documents with hybrid vector + keyword retrieval."""
        if not self.initialized or self.index is None:
            logger.warning("Knowledge service is not initialized or vector index is unavailable")
            return []

        try:
            documents = self.db.get_all_documents()
            if category:
                documents = [doc for doc in documents if doc.get("category") == category]
            if not documents:
                return []

            document_by_id = {doc["id"]: doc for doc in documents}
            vector_scores = self._search_vector(query, set(document_by_id))
            keyword_scores = self._calculate_keyword_scores(query, documents)

            vector_norm = self._normalize_scores(vector_scores)
            keyword_norm = self._normalize_scores(keyword_scores)
            vector_ranks = self._rank_scores(vector_scores)
            keyword_ranks = self._rank_scores(keyword_scores)
            rrf_scores = self._reciprocal_rank_fusion(
                [
                    (vector_ranks, self.VECTOR_WEIGHT),
                    (keyword_ranks, self.KEYWORD_WEIGHT),
                ]
            )
            candidate_ids = set(rrf_scores)
            if not candidate_ids:
                return []

            ranked_docs = []
            for doc_id in candidate_ids:
                doc = dict(document_by_id[doc_id])
                vector_score = vector_norm.get(doc_id, 0.0)
                keyword_score = keyword_norm.get(doc_id, 0.0)
                rrf_score = rrf_scores[doc_id]

                doc["score"] = round(rrf_score, 6)
                doc["rrf_score"] = round(rrf_score, 6)
                doc["vector_score"] = round(vector_score, 6)
                doc["keyword_score"] = round(keyword_score, 6)
                doc["vector_rank"] = vector_ranks.get(doc_id)
                doc["keyword_rank"] = keyword_ranks.get(doc_id)
                doc["retrieval_method"] = self._retrieval_method(
                    vector_ranks.get(doc_id),
                    keyword_ranks.get(doc_id),
                )
                ranked_docs.append(doc)

            ranked_docs.sort(
                key=lambda doc: (
                    doc.get("score", 0.0),
                    doc.get("keyword_rank") is not None and doc.get("vector_rank") is not None,
                    doc.get("keyword_score", 0.0),
                    doc.get("vector_score", 0.0),
                ),
                reverse=True,
            )

            for rank, doc in enumerate(ranked_docs[:top_k], start=1):
                doc["rank"] = rank
            return ranked_docs[:top_k]
        except Exception as e:
            logger.error("Knowledge search failed: %s", e)
            return []

    def _search_vector(self, query: str, allowed_doc_ids: set[int]) -> Dict[int, float]:
        query_embedding = embed_input(query)
        query_array = np.array([query_embedding]).astype("float32")
        fetch_k = len(self.document_ids)
        scores, indices = self.index.search(query_array, fetch_k)

        vector_scores = {}
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.document_ids):
                continue
            doc_id = self.document_ids[idx]
            if doc_id in allowed_doc_ids:
                vector_scores[doc_id] = float(score)
        return vector_scores

    def _calculate_keyword_scores(self, query: str, documents: List[Dict]) -> Dict[int, float]:
        """Calculate lightweight BM25 scores with exact keyword boosts."""
        query_tokens = self._tokenize_for_search(query)
        if not query_tokens:
            return {}

        doc_tokens = {
            doc["id"]: self._tokenize_for_search(self._document_search_text(doc))
            for doc in documents
        }
        doc_tokens = {doc_id: tokens for doc_id, tokens in doc_tokens.items() if tokens}
        if not doc_tokens:
            return {}

        query_counts = Counter(query_tokens)
        doc_counts = {doc_id: Counter(tokens) for doc_id, tokens in doc_tokens.items()}
        doc_lengths = {doc_id: len(tokens) for doc_id, tokens in doc_tokens.items()}
        avg_doc_length = sum(doc_lengths.values()) / len(doc_lengths)
        total_docs = len(doc_tokens)

        document_frequency = Counter()
        for token in query_counts:
            document_frequency[token] = sum(
                1 for counts in doc_counts.values() if token in counts
            )

        k1 = 1.5
        b = 0.75
        scores = {}
        for doc in documents:
            doc_id = doc["id"]
            counts = doc_counts.get(doc_id)
            if not counts:
                continue

            bm25_score = 0.0
            doc_length = doc_lengths[doc_id]
            for token, query_weight in query_counts.items():
                term_frequency = counts.get(token, 0)
                if not term_frequency:
                    continue
                doc_frequency = document_frequency[token]
                idf = math.log(1 + (total_docs - doc_frequency + 0.5) / (doc_frequency + 0.5))
                denominator = term_frequency + k1 * (
                    1 - b + b * doc_length / avg_doc_length
                )
                bm25_score += query_weight * idf * (
                    term_frequency * (k1 + 1) / denominator
                )

            final_score = bm25_score + self._exact_keyword_boost(query, doc)
            if final_score > 0:
                scores[doc_id] = final_score

        return scores

    def _document_search_text(self, doc: Dict) -> str:
        keywords = doc.get("keywords") or []
        keyword_text = " ".join(str(keyword) for keyword in keywords)
        return " ".join(
            [
                str(doc.get("category") or ""),
                str(doc.get("content") or ""),
                keyword_text,
                keyword_text,
            ]
        )

    def _tokenize_for_search(self, text: str) -> List[str]:
        normalized = (text or "").lower()
        tokens = re.findall(r"[a-z0-9]+", normalized)
        chinese_spans = re.findall(r"[\u4e00-\u9fff]+", normalized)
        for span in chinese_spans:
            tokens.append(span)
            tokens.extend(span[i : i + 2] for i in range(max(len(span) - 1, 0)))
            tokens.extend(span[i : i + 3] for i in range(max(len(span) - 2, 0)))
        return [token for token in tokens if token]

    def _exact_keyword_boost(self, query: str, doc: Dict) -> float:
        normalized_query = (query or "").lower()
        if not normalized_query:
            return 0.0

        category = str(doc.get("category") or "").lower()
        content = str(doc.get("content") or "").lower()
        keywords = [str(keyword).lower() for keyword in doc.get("keywords") or []]
        boost = 0.0

        if category and category in normalized_query:
            boost += 1.5

        for keyword in keywords:
            if not keyword:
                continue
            if keyword in normalized_query or normalized_query in keyword:
                boost += 2.0

        query_terms = [
            term
            for term in re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9]+", normalized_query)
            if len(term) >= 2
        ]
        haystack = f"{category} {content} {' '.join(keywords)}"
        for term in query_terms:
            if term in haystack:
                boost += 0.5

        return boost

    def _normalize_scores(self, scores: Dict[int, float]) -> Dict[int, float]:
        if not scores:
            return {}

        values = list(scores.values())
        min_score = min(values)
        max_score = max(values)
        if math.isclose(max_score, min_score):
            return {doc_id: 1.0 for doc_id, score in scores.items() if score > 0}

        return {
            doc_id: (score - min_score) / (max_score - min_score)
            for doc_id, score in scores.items()
        }

    def _rank_scores(self, scores: Dict[int, float]) -> Dict[int, int]:
        """Rank candidate scores descending for rank-based fusion."""
        return {
            doc_id: rank
            for rank, (doc_id, _score) in enumerate(
                sorted(scores.items(), key=lambda item: item[1], reverse=True),
                start=1,
            )
        }

    def _reciprocal_rank_fusion(
        self,
        ranked_lists: List[tuple[Dict[int, int], float]],
    ) -> Dict[int, float]:
        """Fuse independent candidate rankings with weighted RRF."""
        fused_scores: Dict[int, float] = {}
        for ranks, weight in ranked_lists:
            for doc_id, rank in ranks.items():
                fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + (
                    weight / (self.RRF_K + rank)
                )
        return fused_scores

    def _retrieval_method(self, vector_rank: int | None, keyword_rank: int | None) -> str:
        if vector_rank is not None and keyword_rank is not None:
            return "hybrid"
        if keyword_rank is not None:
            return "keyword"
        return "vector"

    async def add_document(self, content: str, category: str, keywords: List[str] = None) -> bool:
        """Add a knowledge document."""
        try:
            if keywords is None:
                keywords = []

            text_for_embedding = f"{content} {' '.join(keywords)}"
            embedding = embed_input(text_for_embedding)
            doc_id = self.db.add_document(content, category, keywords, embedding)
            await self._build_vector_index()

            logger.info("Added knowledge document %s: %s...", doc_id, content[:50])
            return True
        except Exception as e:
            logger.error("Failed to add knowledge document: %s", e)
            return False

    async def update_document(
        self,
        doc_id: int,
        content: str = None,
        category: str = None,
        keywords: List[str] = None,
    ) -> bool:
        """Update a knowledge document."""
        try:
            embedding = None
            if content is not None or keywords is not None:
                current_doc = self.db.get_document(doc_id)
                if not current_doc:
                    return False

                final_content = content if content is not None else current_doc["content"]
                final_keywords = keywords if keywords is not None else current_doc.get("keywords", [])
                text_for_embedding = f"{final_content} {' '.join(final_keywords)}"
                embedding = embed_input(text_for_embedding)

            success = self.db.update_document(doc_id, content, category, keywords, embedding)
            if success and embedding is not None:
                await self._build_vector_index()
            return success
        except Exception as e:
            logger.error("Failed to update knowledge document: %s", e)
            return False

    async def delete_document(self, doc_id: int, soft_delete: bool = True) -> bool:
        """Delete a knowledge document."""
        try:
            success = self.db.delete_document(doc_id, soft_delete)
            if success:
                await self._build_vector_index()
            return success
        except Exception as e:
            logger.error("Failed to delete knowledge document: %s", e)
            return False

    def get_all_documents(self, include_inactive: bool = False) -> List[Dict]:
        """Get all knowledge documents."""
        return self.db.get_all_documents(include_inactive)

    def get_document(self, doc_id: int) -> Dict:
        """Get one knowledge document."""
        return self.db.get_document(doc_id)

    def get_all_categories(self) -> List[str]:
        """Get all knowledge categories."""
        return self.db.get_all_categories()

    def get_documents_count(self) -> int:
        """Get active document count."""
        return self.db.get_documents_count()

    def search_by_category(self, category: str) -> List[Dict]:
        """Search documents by category."""
        return self.db.search_documents_by_category(category)

    def search_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """Search documents by exact keywords."""
        return self.db.search_documents_by_keywords(keywords)
