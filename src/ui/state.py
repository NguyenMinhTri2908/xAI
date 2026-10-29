"""Compatibility Shim for UnderwritingState.

This module re-exports state classes from `src.state` to ensure 100% backward
compatibility with any legacy imports.
"""
from src.state import (
    UnderwritingState,
    BaseUnderwritingState,
    DatasetState,
    InspectionState,
    SimulatorState,
    OptimizationState,
)

__all__ = [
    "UnderwritingState",
    "BaseUnderwritingState",
    "DatasetState",
    "InspectionState",
    "SimulatorState",
    "OptimizationState",
]
