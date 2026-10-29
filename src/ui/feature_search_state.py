"""Compatibility Shim for FeatureSearchState.

This module re-exports FeatureSearchState from `src.state.feature_search_state`
to ensure 100% backward compatibility.
"""
from src.state.feature_search_state import FeatureSearchState

__all__ = ["FeatureSearchState"]
