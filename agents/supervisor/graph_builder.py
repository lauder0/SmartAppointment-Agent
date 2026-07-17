"""Build the Smart Appointment 3.0 supervisor graph."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agents.specialists import (
    availability_subgraph_node,
    booking_subgraph_node,
    consultation_subgraph_node,
    fallback_subgraph_node,
    recommendation_subgraph_node,
)
from agents.supervisor.orchestration.nodes import (
    supervisor_continue_node,
    supervisor_entry_node,
    supervisor_router_node,
)
from agents.supervisor.orchestration.response import supervisor_response_node
from agents.supervisor.orchestration.routing import (
    route_after_agent_result,
    route_after_supervisor_continue,
    route_supervisor_decision,
)
from agents.supervisor.state import SupervisorState


def build_smart_appointment_supervisor_graph():
    """Build and compile the supervisor + specialist subgraph workflow."""
    builder = StateGraph(SupervisorState)

    builder.add_node("supervisor_entry", supervisor_entry_node)
    builder.add_node("supervisor_router", supervisor_router_node)
    builder.add_node("supervisor_continue", supervisor_continue_node)
    builder.add_node("supervisor_response", supervisor_response_node)
    builder.add_node("consultation_subgraph", consultation_subgraph_node)
    builder.add_node("availability_subgraph", availability_subgraph_node)
    builder.add_node("booking_subgraph", booking_subgraph_node)
    builder.add_node("recommendation_subgraph", recommendation_subgraph_node)
    builder.add_node("fallback_subgraph", fallback_subgraph_node)

    builder.add_edge(START, "supervisor_entry")
    builder.add_edge("supervisor_entry", "supervisor_router")
    builder.add_conditional_edges(
        "supervisor_router",
        route_supervisor_decision,
        {
            "consultation": "consultation_subgraph",
            "availability": "availability_subgraph",
            "booking": "booking_subgraph",
            "recommendation": "recommendation_subgraph",
            "fallback": "fallback_subgraph",
        },
    )

    builder.add_conditional_edges(
        "consultation_subgraph",
        route_after_agent_result,
        {
            "continue": "supervisor_continue",
            "end": "supervisor_response",
        },
    )
    builder.add_conditional_edges(
        "availability_subgraph",
        route_after_agent_result,
        {
            "continue": "supervisor_continue",
            "end": "supervisor_response",
        },
    )
    builder.add_conditional_edges(
        "supervisor_continue",
        route_after_supervisor_continue,
        {
            "consultation": "consultation_subgraph",
            "availability": "availability_subgraph",
            "booking": "booking_subgraph",
            "recommendation": "recommendation_subgraph",
            "fallback": "fallback_subgraph",
            "response": "supervisor_response",
        },
    )
    builder.add_conditional_edges(
        "booking_subgraph",
        route_after_agent_result,
        {
            "continue": "supervisor_continue",
            "end": "supervisor_response",
        },
    )
    builder.add_conditional_edges(
        "recommendation_subgraph",
        route_after_agent_result,
        {
            "continue": "supervisor_continue",
            "end": "supervisor_response",
        },
    )
    builder.add_conditional_edges(
        "fallback_subgraph",
        route_after_agent_result,
        {
            "continue": "supervisor_continue",
            "end": "supervisor_response",
        },
    )
    builder.add_edge("supervisor_response", END)

    return builder.compile()
