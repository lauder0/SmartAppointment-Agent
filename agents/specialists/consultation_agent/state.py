"""Consultation agent private state helpers."""

from __future__ import annotations

from typing import Any, Dict


def consultation_state_from_supervisor(state: Dict[str, Any]) -> Dict[str, Any]:
    return dict(state.get("consultation") or {})


def completed_consultation_state(
    current: Dict[str, Any],
    answer: str | None,
    retrieved_docs: list[Dict[str, Any]],
    topic: str = "knowledge",
) -> Dict[str, Any]:
    updated = dict(current)
    updated.update(
        {
            "status": "completed",
            "last_topic": topic,
            "retrieved_docs": retrieved_docs,
            "last_answer": answer,
        }
    )
    return updated
