"""Service package.

Submodules are intentionally not imported eagerly so optional dependencies such
as FAISS are only required by the services that actually use them.
"""

__all__ = [
    "AppointmentPreferenceService",
    "AppointmentService",
    "KnowledgeService",
    "RecommendationService",
    "TechnicianService",
    "UserBehaviorService",
]
