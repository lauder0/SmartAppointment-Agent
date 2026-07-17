"""Specialist subgraph adapters for Smart Appointment 3.0."""

from .availability_agent import availability_subgraph_node
from .booking_agent import booking_subgraph_node
from .consultation_agent import consultation_subgraph_node
from .fallback_agent import fallback_subgraph_node
from .recommendation_agent import recommendation_subgraph_node

__all__ = [
    "availability_subgraph_node",
    "booking_subgraph_node",
    "consultation_subgraph_node",
    "fallback_subgraph_node",
    "recommendation_subgraph_node",
]
