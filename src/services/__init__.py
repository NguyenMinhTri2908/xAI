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
    calculate_actuarial_emi,
    estimate_requested_term_months,
    compute_contractual_emi_and_dti,
    compute_derived_financials,
)
from src.services.ingestion_service import (
    load_dataset_from_source,
    load_dataset_from_upload,
    set_active_dataset,
    get_active_dataset,
    get_active_client_ids,
    get_client_row_data,
    get_client_table_summary,
    format_df_to_summary_records,
)

__all__ = [
    "generate_candidate_pool",
    "build_optimization_entry",
    "compute_alternative_proposals",
    "DEFAULT_CANDIDATE_TERMS",
    "DEFAULT_CREDIT_FACTORS",
    "process_shap_explanations",
    "calculate_actuarial_emi",
    "estimate_requested_term_months",
    "compute_contractual_emi_and_dti",
    "compute_derived_financials",
    "load_dataset_from_source",
    "load_dataset_from_upload",
    "set_active_dataset",
    "get_active_dataset",
    "get_active_client_ids",
    "get_client_row_data",
    "get_client_table_summary",
    "format_df_to_summary_records",
]
