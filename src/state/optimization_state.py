"""Optimization State Module for Underwriting App.

Manages AI loan restructuring, candidate search, and alternative loan term proposals.
Delegates heavy calculation algorithms to src.services.restructuring_service.
"""
from typing import Dict, List, Optional
import reflex as rx

from src.state.simulator_state import SimulatorState
from src.engine.credit_scoring import get_scoring_engine
from src.data_processing.ingestion_service import get_client_row_data
from src.services.restructuring_service import (
    generate_candidate_pool,
    build_optimization_entry,
    compute_alternative_proposals,
)


class OptimizationState(SimulatorState):
    """Sub-state managing loan restructuring optimization and alternative proposals."""

    is_optimizing: bool = False
    is_loading_alternatives: bool = False
    alternatives_loaded: bool = False
    optimization_options: List[Dict[str, str]] = []
    recommended_option: Optional[Dict[str, str]] = None
    alternative_options: List[Dict[str, str]] = []
    show_optimization_results: bool = False
    show_alternative_options: bool = False

    @property
    def selected_client_idx(self) -> str:
        """Alias tương thích ngược cho selected_client_id chống AttributeError."""
        return self.selected_client_id

    def _find_candidate_pool(
        self,
        base_credit: float,
        income: float,
    ) -> List[Dict]:
        """Generate feasible restructuring candidates via pure domain service."""
        return generate_candidate_pool(
            engine=get_scoring_engine(),
            base_credit=base_credit,
            income=income,
            interest_rate_factor=self.interest_rate_factor,
        )

    def _build_optimization_entry(
        self,
        c: Dict,
        base_credit: float,
        base_term: int,
        base_annuity: float,
        base_dti: float,
        base_pd_percent: float,
        baseline_offered_rate: float,
        title: str,
        opt_type: str,
    ) -> Dict[str, str]:
        """Construct a UI-ready optimization option dictionary via pure domain service."""
        return build_optimization_entry(
            c=c,
            base_credit_val=base_credit,
            base_term_val=base_term,
            base_annuity_val=base_annuity,
            base_dti_val=base_dti,
            base_pd_percent_val=base_pd_percent,
            baseline_offered_rate=baseline_offered_rate,
            title=title,
            opt_type=opt_type,
        )

    def _compute_alternative_options(
        self,
        pool: List[Dict],
        base_credit: float,
        base_term: int,
        base_annuity: float,
        base_dti: float,
        base_pd_percent: float,
        baseline_offered_rate: float,
    ) -> List[Dict[str, str]]:
        """Compute alternative restructuring options via pure domain service."""
        return compute_alternative_proposals(
            pool=pool,
            recommended_option=self.recommended_option or {},
            base_credit_val=base_credit,
            base_term_val=base_term,
            base_annuity_val=base_annuity,
            base_dti_val=base_dti,
            base_pd_percent_val=base_pd_percent,
            baseline_offered_rate=baseline_offered_rate,
        )

    @rx.event
    def toggle_alternative_options(self):
        """Toggle accordion/dropdown for alternative restructuring options."""
        self.show_alternative_options = not self.show_alternative_options
        if (
            self.show_alternative_options
            and not self.alternatives_loaded
            and bool(self.selected_client_id)
        ):
            self.is_loading_alternatives = True
            yield

            engine = get_scoring_engine()
            if (getattr(engine, "_cached_clean_df", None) is None or getattr(engine, "_cached_client_id", None) != str(self.selected_client_id)) and self.selected_client_id:
                try:
                    row_data = get_client_row_data(self.selected_client_id)
                    if row_data is not None:
                        engine.cache_client_features(row_data, str(self.selected_client_id))
                except Exception as e:
                    print(f"[Alternatives] Warning caching features: {e}")

            income = float(self.baseline_amt_income_total or self.sim_amt_income_total or 50000.0)
            base_credit = float(self.baseline_amt_credit or self.sim_amt_credit or 100000.0)
            base_term = int(self.baseline_term_months or self.sim_term_months or 12)
            base_annuity = float(self.baseline_amt_annuity or self.sim_amt_annuity or 5000.0)
            base_dti = float(self.sim_dti or self.baseline_dti or 0.0)
            base_pd_percent = float(self.sim_score_percent or self.baseline_score_percent or 0.0)
            baseline_offered_rate = float(self.baseline_offered_rate or self.sim_offered_rate or 12.0)

            pool = self._find_candidate_pool(base_credit, income)
            self.alternative_options = self._compute_alternative_options(
                pool=pool,
                base_credit=base_credit,
                base_term=base_term,
                base_annuity=base_annuity,
                base_dti=base_dti,
                base_pd_percent=base_pd_percent,
                baseline_offered_rate=baseline_offered_rate,
            )
            self.alternatives_loaded = True
            self.is_loading_alternatives = False

    @rx.event
    def ai_auto_optimize(self):
        """Run automated loan restructuring optimization to reach approval."""
        print(f"[AI Auto-Optimize] Triggered. selected_client_id={self.selected_client_id}")
        if not self.selected_client_id or self.selected_client_id == "None":
            if self.available_client_ids:
                self.selected_client_id = self.available_client_ids[0]
            else:
                self.alert_message = "Please select a client profile before optimizing."
                self.alert_type = "warning"
                self.show_alert = True
                return

        self.is_optimizing = True
        self.optimization_options = []
        self.recommended_option = None
        self.alternative_options = []
        self.alternatives_loaded = False
        self.show_alternative_options = False
        yield

        engine = get_scoring_engine()
        # Đảm bảo cache features cho client hiện tại
        if (getattr(engine, "_cached_clean_df", None) is None or getattr(engine, "_cached_client_id", None) != str(self.selected_client_id)) and self.selected_client_id:
            try:
                row_data = get_client_row_data(self.selected_client_id)
                if row_data is not None:
                    engine.cache_client_features(row_data, str(self.selected_client_id))
                    print(f"[AI Auto-Optimize] Re-cached client features for {self.selected_client_id}")
            except Exception as e:
                print(f"[AI Auto-Optimize] Warning caching features: {e}")

        income = float(self.baseline_amt_income_total or self.sim_amt_income_total or 50000.0)
        base_credit = float(self.baseline_amt_credit or self.sim_amt_credit or 100000.0)
        base_term = int(self.baseline_term_months or self.sim_term_months or 12)
        base_annuity = float(self.baseline_amt_annuity or self.sim_amt_annuity or 5000.0)
        base_dti = float(self.sim_dti or self.baseline_dti or 0.0)
        base_pd_percent = float(self.sim_score_percent or self.baseline_score_percent or 0.0)
        baseline_offered_rate = float(self.baseline_offered_rate or self.sim_offered_rate or 12.0)

        pool = self._find_candidate_pool(base_credit, income)
        print(f"[AI Auto-Optimize] Candidate pool size: {len(pool)}")

        if not pool:
            self.is_optimizing = False
            self.show_optimization_results = True
            self.status_message = "No restructuring terms meet the risk appetite criteria for this client."
            return

        best = pool[0]
        self.recommended_option = self._build_optimization_entry(
            c=best,
            base_credit=base_credit,
            base_term=base_term,
            base_annuity=base_annuity,
            base_dti=base_dti,
            base_pd_percent=base_pd_percent,
            baseline_offered_rate=baseline_offered_rate,
            title="AI Recommended Restructuring",
            opt_type="recommended",
        )
        self.optimization_options = [self.recommended_option]
        self.is_optimizing = False
        self.show_optimization_results = True

    @rx.event
    def apply_optimization_option(self, option: Optional[Dict[str, str]] = None):
        """Apply an optimization option's loan parameters to the simulator."""
        target = option or self.recommended_option
        if not target:
            return

        credit_val = float(target.get("credit", self.sim_amt_credit))
        term_val = int(target.get("term", self.sim_term_months))
        annuity_val = float(target.get("annuity", self.sim_amt_annuity))

        self.sim_amt_credit = credit_val
        self.sim_amt_credit_str = f"{int(credit_val):,}"
        self.sim_term_months = term_val
        self.sim_term_months_str = str(term_val)
        self.sim_amt_annuity = annuity_val
        self.sim_amt_annuity_str = f"{int(annuity_val):,}"

        self.recalculate_simulation_pd()
        self.show_optimization_results = False

    @rx.event
    def close_optimization_results(self):
        """Dismiss optimization results modal or card."""
        self.show_optimization_results = False

    # Backwards compatibility alias
    auto_optimize_terms = ai_auto_optimize
