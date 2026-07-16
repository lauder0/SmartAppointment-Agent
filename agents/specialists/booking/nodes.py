"""Internal workflow nodes for the booking specialist agent."""

from __future__ import annotations

from typing import Any, Dict

from agents.specialists.booking.behavior_actions import behavior_recorder_node
from agents.specialists.booking.actions import (
    booking_accept_recommendation_node,
    booking_complete_node,
    booking_confirmation_node,
    booking_confirmation_prompt_node,
    booking_create_node,
    booking_failed_node,
    booking_guard_node,
    booking_match_node,
    booking_missing_node,
    booking_parse_node,
)
from agents.specialists.fallback.actions import clarification_node
from agents.specialists.result_contract import apply_update


async def parse_slots(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await booking_parse_node(state))


async def ask_missing_slots(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await booking_missing_node(state))


async def match_slot(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await booking_match_node(state))


async def accept_recommendation(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await booking_accept_recommendation_node(state))


async def ask_confirmation(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await booking_confirmation_prompt_node(state))


async def fail_booking(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await booking_failed_node(state))


async def interpret_confirmation(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await booking_confirmation_node(state))


async def guard_booking(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await booking_guard_node(state))


async def create_transaction(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await booking_create_node(state))


async def record_behavior(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await behavior_recorder_node(state))


async def complete_booking(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await booking_complete_node(state))


async def clarify_booking(state: Dict[str, Any]) -> Dict[str, Any]:
    return apply_update(state, await clarification_node(state))


