"""Compatibility Shim for FeatureDrawerState.

This module re-exports FeatureDrawerState from `src.state.drawer_state`
to ensure 100% backward compatibility.
"""
from src.state.drawer_state import FeatureDrawerState

__all__ = ["FeatureDrawerState"]
