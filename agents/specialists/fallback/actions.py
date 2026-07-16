"""Clarification and unsupported handling nodes."""

from __future__ import annotations

from agents.understander.rules import (
    is_courtesy,
    is_greeting,
)
from agents.shared.node_utils import append_assistant_message, last_user_text
from agents.response_writer.composer import composer
from agents.shared.state import AgentState


async def unsupported_node(state: AgentState) -> AgentState:
    """Reply to out-of-domain requests."""
    user_input = last_user_text(state)
    booking = state.get("booking") or {}
    if is_greeting(user_input):
        if booking.get("status") == "awaiting_confirmation":
            reply = composer.reply(
                "greeting",
                {"agent_label": "预约机器人", "booking_pending": True},
            )
            return append_assistant_message(
                {
                    "final_response": reply,
                },
                reply,
            )

        reply = composer.reply("greeting")
        return append_assistant_message(
            {
                "final_response": reply,
            },
            reply,
        )

    if is_courtesy(user_input):
        if booking.get("status") == "awaiting_confirmation":
            reply = composer.reply(
                "courtesy",
                {"agent_label": "预约机器人", "booking_pending": True},
            )
            return append_assistant_message(
                {
                    "final_response": reply,
                },
                reply,
            )
        reply = composer.reply("courtesy")
        return append_assistant_message(
            {
                "final_response": reply,
            },
            reply,
        )

    reply = composer.reply("unsupported")
    return append_assistant_message(
        {
            "final_response": reply,
        },
        reply,
    )


async def clarification_node(state: AgentState) -> AgentState:
    """Ask a focused follow-up when the router sees a business-related but vague request."""
    booking = state.get("booking") or {}
    if booking.get("status") in {"drafting", "draft_ready", "matched", "awaiting_confirmation"}:
        reply = composer.reply(
            "clarification",
            {"agent_label": "预约机器人", "booking_active": True},
        )
        return append_assistant_message(
            {
                "final_response": reply,
            },
            reply,
        )

    reply = composer.reply("clarification")
    return append_assistant_message(
        {
            "final_response": reply,
        },
        reply,
    )
