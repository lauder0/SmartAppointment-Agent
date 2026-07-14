"""Compatibility wrapper for the renamed decision builder module."""

from .decision_builder import build_understanding_result

model_task = build_understanding_result

__all__ = ["build_understanding_result", "model_task"]
