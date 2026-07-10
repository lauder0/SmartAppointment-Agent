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
from agents.supervisor.nodes import (
    supervisor_entry_node,
    supervisor_router_node,
)
from agents.supervisor.routing import route_supervisor_decision
from agents.supervisor.state import SupervisorState


def build_smart_appointment_supervisor_graph():
    """Build and compile the supervisor + specialist subgraph workflow."""
    builder = StateGraph(SupervisorState)

    builder.add_node("supervisor_entry", supervisor_entry_node)
    builder.add_node("supervisor_router", supervisor_router_node)
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

    builder.add_edge("consultation_subgraph", END)
    builder.add_edge("availability_subgraph", END)
    builder.add_edge("booking_subgraph", END)
    builder.add_edge("recommendation_subgraph", END)
    builder.add_edge("fallback_subgraph", END)

    return builder.compile()
