"""Shared schemas for intent understanding and decision building."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from config.time_utils import utc_now_iso


ROUTER_ACTIONS = {
    "answer_knowledge",
    "query_availability",
    "start_or_continue_booking",
    "modify_booking",
    "confirm_booking",
    "cancel_booking",
    "generate_recommendation",
    "replace_recommendation",
    "select_recommended_technician",
    "ask_clarification",
    "unsupported",
}


class IntentSignal(TypedDict, total=False):
    """One explicit signal detected from the current utterance or context."""

    name: str
    intent_group: str
    subtype: str
    confidence: float
    source: str
    matched_text: str
    requires_context: bool
    attributes: Dict[str, Any]
    slots: Dict[str, Any]


class NormalizedInput(TypedDict, total=False):
    """Normalized user input and directly extracted candidate slots."""

    raw_text: str
    normalized_text: str
    candidate_slots: Dict[str, Any]
    availability_criteria: Dict[str, Any]


class LLMPlan(TypedDict, total=False):
    """Structured candidate plan produced by the LLM fallback."""

    action: str
    task_type: str
    primary_intent: str
    secondary_intents: List[str]
    confidence: float
    slot_updates: Dict[str, Any]
    missing_slots: List[str]
    risk_level: str
    requires_confirmation: bool
    reason: str
    evidence: List[str]


class TaskFrame(TypedDict, total=False):
    """Persistent representation of the current business task."""

    task_id: str
    task_type: str
    status: str
    primary_intent: str
    secondary_intents: List[str]
    collected_slots: Dict[str, Any]
    missing_slots: List[str]
    pending_next: Optional[str]
    execution_policy: str
    continuation: Optional[Dict[str, Any]]
    last_question_type: Optional[str]
    subtasks: List[Dict[str, Any]]
    confirmations_required: List[str]
    conflicts: List[Dict[str, Any]]
    invalidates: List[str]
    safety_flags: List[str]
    risk_level: str
    source: str
    confidence: float
    updated_at: str


class UnderstandingResult(TypedDict, total=False):
    """Full semantic interpretation before graph routing."""

    raw_text: str
    normalized_text: str
    signals: List[IntentSignal]
    primary_intent: str
    secondary_intents: List[str]
    task_type: str
    confidence: float
    slot_updates: Dict[str, Any]
    missing_slots: List[str]
    conflicts: List[Dict[str, Any]]
    invalidates: List[str]
    safety_flags: List[str]
    risk_level: str
    subtasks: List[Dict[str, Any]]
    next_action: str
    execution_policy: str
    continuation: Optional[Dict[str, Any]]
    route_reason: str
    requires_confirmation: bool
    clarification_question: Optional[str]
    task_frame: TaskFrame
    trace: Dict[str, Any]


class RouteDecision(TypedDict, total=False):
    """Executable decision consumed by the existing supervisor graph."""

    action: str
    reason: str
    confidence: float
    source: str
    task_type: str
    primary_intent: str
    secondary_intents: List[str]
    slot_updates: Dict[str, Any]
    missing_slots: List[str]
    conflicts: List[Dict[str, Any]]
    invalidates: List[str]
    safety_flags: List[str]
    risk_level: str
    execution_policy: str
    continuation: Optional[Dict[str, Any]]
    clarification_question: Optional[str]
    trace: Dict[str, Any]


def default_task_frame() -> TaskFrame:
    """Create an empty task frame."""
    return {
        "task_id": "",
        "task_type": "",
        "status": "idle",
        "primary_intent": "",
        "secondary_intents": [],
        "collected_slots": {},
        "missing_slots": [],
        "pending_next": None,
        "execution_policy": "single_action",
        "continuation": None,
        "last_question_type": None,
        "subtasks": [],
        "confirmations_required": [],
        "conflicts": [],
        "invalidates": [],
        "safety_flags": [],
        "risk_level": "low",
        "source": "",
        "confidence": 0.0,
        "updated_at": "",
    }


def now_iso() -> str:
    return utc_now_iso()


def compact_slots(slots: Dict[str, Any] | None) -> Dict[str, Any]:
    """Remove empty values while preserving meaningful false/zero values."""
    return {
        key: value
        for key, value in (slots or {}).items()
        if value not in (None, "", [], {}, "未知")
    }
