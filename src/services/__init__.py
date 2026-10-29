"""
Domain Services Package.

Contains pure, decoupled business logic and domain algorithms:
- RestructuringService: AI grid search, hard feasibility filter, RBP candidate pricing.
- ExplanationService: SHAP feature attributions and bar width calculations.
- FinancialService: Derived credit metrics (DTI, Tenure, Implied interest factors).
"""

from src.services.restructuring_service import (
    generate_candidate_pool,
    build_optimization_entry,
    compute_alternative_proposals,
    DEFAULT_CANDIDATE_TERMS,
    DEFAULT_CREDIT_FACTORS,
)
from src.services.explanation_service import (
    process_shap_explanations,
)
from src.services.financial_service import (
    compute_derived_financials,
)

__all__ = [
    "generate_candidate_pool",
    "build_optimization_entry",
    "compute_alternative_proposals",
    "DEFAULT_CANDIDATE_TERMS",
    "DEFAULT_CREDIT_FACTORS",
    "process_shap_explanations",
    "compute_derived_financials",
]
