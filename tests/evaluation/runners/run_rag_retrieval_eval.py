"""Evaluate the current knowledge retrieval implementation.

This script measures retrieval quality through KnowledgeService.search, so the
numbers reflect whichever retriever is currently active, including the hybrid
vector + keyword implementation.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CASE_FILE = Path(__file__).resolve().parents[1] / "cases" / "rag_retrieval_cases.json"


@dataclass
class RetrievalResult:
    case_id: str
    query: str
    hit_rank: int | None
    latency_ms: float
    top_docs: list[dict[str, Any]]


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["cases"]


def doc_matches(doc: dict[str, Any], case: dict[str, Any]) -> bool:
    category = str(doc.get("category") or "")
    content = str(doc.get("content") or "")
    keywords = " ".join(str(item) for item in doc.get("keywords") or [])
    haystack = f"{category} {content} {keywords}"

    expected_categories = case.get("expected_categories", [])
    expected_terms = case.get("expected_terms", [])
    category_hit = any(expected == category for expected in expected_categories)
    term_hit = any(term in haystack for term in expected_terms)
    return category_hit or term_hit


async def evaluate_case(service: Any, case: dict[str, Any], top_k: int) -> RetrievalResult:
    started = time.perf_counter()
    docs = await service.search(case["query"], top_k=top_k)
    latency_ms = (time.perf_counter() - started) * 1000
    hit_rank = None
    for index, doc in enumerate(docs, start=1):
        if doc_matches(doc, case):
            hit_rank = index
            break
    compact_docs = [
        {
            "rank": index,
            "id": doc.get("id"),
            "category": doc.get("category"),
            "score": doc.get("score"),
            "vector_score": doc.get("vector_score"),
            "keyword_score": doc.get("keyword_score"),
            "retrieval_method": doc.get("retrieval_method"),
            "content": str(doc.get("content") or "")[:120],
        }
        for index, doc in enumerate(docs, start=1)
    ]
    return RetrievalResult(
        case_id=case["id"],
        query=case["query"],
        hit_rank=hit_rank,
        latency_ms=latency_ms,
        top_docs=compact_docs,
    )


def recall_at(results: list[RetrievalResult], k: int) -> float:
    if not results:
        return 0.0
    hits = sum(1 for result in results if result.hit_rank is not None and result.hit_rank <= k)
    return hits / len(results)


def mean_reciprocal_rank(results: list[RetrievalResult]) -> float:
    if not results:
        return 0.0
    total = sum(1 / result.hit_rank for result in results if result.hit_rank)
    return total / len(results)


def print_result(result: RetrievalResult, show_docs: bool) -> None:
    status = "HIT" if result.hit_rank else "MISS"
    rank_text = f"@{result.hit_rank}" if result.hit_rank else ""
    print(f"{status:<4} {rank_text:<3} {result.case_id} ({result.latency_ms:.0f} ms): {result.query}")
    if show_docs or not result.hit_rank:
        for doc in result.top_docs:
            print(
                f"  #{doc['rank']} category={doc['category']} "
                f"score={doc['score']} vector={doc['vector_score']} "
                f"keyword={doc['keyword_score']} method={doc['retrieval_method']} "
                f"content={doc['content']}"
            )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAG retrieval eval.")
    parser.add_argument("--cases-file", type=Path, default=CASE_FILE)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--show-docs", action="store_true")
    parser.add_argument("--json-report", type=Path)
    args = parser.parse_args()

    from services.knowledge_service import KnowledgeService

    service = KnowledgeService()
    await service.initialize()
    cases = load_cases(args.cases_file)

    results = []
    for case in cases:
        result = await evaluate_case(service, case, args.top_k)
        results.append(result)
        print_result(result, args.show_docs)

    print("\nMetrics:")
    print(f"  cases                 {len(results)}")
    print(f"  recall@1              {recall_at(results, 1):.3f}")
    print(f"  recall@3              {recall_at(results, 3):.3f}")
    print(f"  recall@5              {recall_at(results, 5):.3f}")
    print(f"  mrr                   {mean_reciprocal_rank(results):.3f}")
    print(f"  avg_latency_ms        {sum(r.latency_ms for r in results) / len(results):.0f}")

    misses = [result for result in results if not result.hit_rank]
    if misses:
        print("\nMisses:")
        for result in misses:
            print(f"  {result.case_id}: {result.query}")

    if args.json_report:
        payload = {
            "top_k": args.top_k,
            "metrics": {
                "recall_at_1": recall_at(results, 1),
                "recall_at_3": recall_at(results, 3),
                "recall_at_5": recall_at(results, 5),
                "mrr": mean_reciprocal_rank(results),
                "avg_latency_ms": sum(r.latency_ms for r in results) / len(results),
            },
            "results": [
                {
                    "case_id": result.case_id,
                    "query": result.query,
                    "hit_rank": result.hit_rank,
                    "latency_ms": result.latency_ms,
                    "top_docs": result.top_docs,
                }
                for result in results
            ],
        }
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON report written to {args.json_report}")

    return 1 if misses else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
