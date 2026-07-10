"""Specialist subgraph adapters for Smart Appointment 3.0."""

from .availability import availability_subgraph_node
from .booking import booking_subgraph_node
from .consultation import consultation_subgraph_node
from .fallback import fallback_subgraph_node
from .recommendation import recommendation_subgraph_node

__all__ = [
    "availability_subgraph_node",
    "booking_subgraph_node",
    "consultation_subgraph_node",
    "fallback_subgraph_node",
    "recommendation_subgraph_node",
]
