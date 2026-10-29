"""State Management Package for Underwriting Application.

Implements Clean Architecture & Reflex Modular State Pattern:
BaseUnderwritingState -> DatasetState -> InspectionState -> SimulatorState -> OptimizationState -> UnderwritingState.
Also houses FeatureDrawerState and FeatureSearchState.
"""
import reflex as rx
from src.state.base_state import BaseUnderwritingState
from src.state.dataset_state import DatasetState
from src.state.inspection_state import InspectionState
from src.state.simulator_state import SimulatorState
from src.state.optimization_state import OptimizationState
from src.state.drawer_state import FeatureDrawerState
from src.state.feature_search_state import FeatureSearchState


class UnderwritingState(OptimizationState):
    """Unified Facade State for the Underwriting Application.

    Inherits all capabilities:
    - BaseUnderwritingState: Schema, feature metadata, dataset discovery helpers.
    - DatasetState: Dataset registry, pagination, file uploading.
    - InspectionState: Client selection, SHAP parsing, baseline credit evaluation.
    - SimulatorState: What-if sliders, real-time recalculations, two-way input bindings.
    - OptimizationState: AI loan restructuring search, alternative proposals.
    """
    pass


__all__ = [
    "UnderwritingState",
    "BaseUnderwritingState",
    "DatasetState",
    "InspectionState",
    "SimulatorState",
    "OptimizationState",
    "FeatureDrawerState",
    "FeatureSearchState",
]

