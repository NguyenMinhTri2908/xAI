"""Optimization State Module for Underwriting App.

Manages AI loan restructuring, candidate search, and alternative loan term proposals.
Delegates heavy calculation algorithms to src.services.restructuring_service.
"""
from typing import Dict, List, Optional, Any
import reflex as rx

from src.config.pricing_config import retail_pricing_config
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

    @rx.var
    def has_more_proposals(self) -> bool:
        """Kiểm tra xem còn phương án thay thế chưa được hiển thị không."""
        return len(self.alternative_options) > self.visible_proposals_count

    @rx.var
    def visible_alternative_options(self) -> List[Dict[str, Any]]:
        """Danh sách phương án phụ được phép hiển thị theo cơ chế phân trang show more."""
        return self.alternative_options[: self.visible_proposals_count]

    @rx.var
    def visible_proposals_count_display(self) -> str:
        """Chuỗi hiển thị tiến độ số lượng phương án hiển thị."""
        total = len(self.alternative_options)
        visible = min(self.visible_proposals_count, total)
        return f"Showing {visible} of {total}"

    @property
    def recommended_proposal(self) -> Optional[Dict[str, Any]]:
        return self.recommended_option

    @property
    def alternative_proposals(self) -> List[Dict[str, Any]]:
        return self.alternative_options

    @rx.event
    def show_more_proposals(self):
        """Bung thêm 3 phương án khả thi tiếp theo."""
        self.visible_proposals_count += 3

    @property
    def selected_client_idx(self) -> str:
        """Alias tương thích ngược cho selected_client_id chống AttributeError."""
        return self.selected_client_id

    def _find_candidate_pool(
        self,
        base_credit: float,
        income: float,
        base_term: int = 12,
    ) -> List[Dict]:
        """Generate feasible restructuring candidates via pure domain service."""
        return generate_candidate_pool(
            engine=get_scoring_engine(),
            base_credit=base_credit,
            income=income,
            base_term=base_term,
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
    ) -> Dict[str, Any]:
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
    ) -> List[Dict[str, Any]]:
        """Compute alternative restructuring options via pure domain service."""
        proposals = compute_alternative_proposals(
            pool=pool,
            recommended_option=self.recommended_option or {},
            base_credit_val=base_credit,
            base_term_val=base_term,
            base_annuity_val=base_annuity,
            base_dti_val=base_dti,
            base_pd_percent_val=base_pd_percent,
            baseline_offered_rate=baseline_offered_rate,
        )
        return [p for p in proposals if p]

    @rx.event
    def toggle_alternative_options(self):
        """Toggle accordion/dropdown for alternative restructuring options."""
        self.show_alternative_options = not self.show_alternative_options
        if (
            self.show_alternative_options
            and not self.alternatives_loaded
            and bool(self.selected_client_id)
        ):
            income = float(self.baseline_amt_income_total or 0.0)
            base_credit = float(self.baseline_amt_credit or 0.0)
            base_term = int(self.baseline_term_months or 0)
            base_annuity = float(self.baseline_amt_annuity or 0.0)
            base_dti = float(self.baseline_dti or 0.0)
            base_pd_percent = float(self.baseline_score_percent or (self.baseline_pd * 100.0 if self.baseline_pd else 0.0))
            baseline_offered_rate = float(self.baseline_offered_rate or 0.0)

            # Early exit: Kiểm tra tính hợp lệ của dữ liệu cơ sở
            if base_credit <= 0.0 or income <= 0.0 or base_term <= 0:
                self.is_loading_alternatives = False
                return

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

            pool = self._find_candidate_pool(base_credit, income, base_term)
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

        # 1. Trích xuất chính xác dữ liệu cơ sở của khách hàng (Không gán số ma fallback 100k/50k/12m)
        income = float(self.baseline_amt_income_total or 0.0)
        base_credit = float(self.baseline_amt_credit or 0.0)
        base_term = int(self.baseline_term_months or 0)
        base_annuity = float(self.baseline_amt_annuity or 0.0)
        base_dti = float(self.baseline_dti or 0.0)
        base_pd_percent = float(self.baseline_score_percent or (self.baseline_pd * 100.0 if self.baseline_pd else 0.0))
        baseline_offered_rate = float(self.baseline_offered_rate or 0.0)

        # 2. Fail-fast / Early Exit: Dừng ngay nếu hồ sơ cơ sở thiếu hoặc không hợp lệ
        if base_credit <= 0.0 or income <= 0.0 or base_term <= 0:
            self.is_optimizing = False
            self.alert_message = "Cannot run AI Optimization: Baseline client profile data (Credit, Income, or Term) is missing or invalid."
            self.alert_type = "error"
            self.show_alert = True
            return

        # 3. Phân nhánh Fast-path: Nếu hồ sơ đã APPROVED thì báo ngay "Hồ sơ đã tối ưu, không cần cơ cấu"
        cutoff_pd = retail_pricing_config.default_cutoff_pd
        cutoff_percent = cutoff_pd * 100.0
        is_already_approved = (
            (base_pd_percent <= cutoff_percent and base_dti <= retail_pricing_config.target_dti_healthy)
            or (
                self.baseline_decision in ("APPROVED", "APPROVE")
                and self.baseline_decision_status != "DECLINED"
                and base_pd_percent <= cutoff_percent
            )
        )

        if is_already_approved:
            self.is_optimizing = False
            self.is_baseline_optimal = True
            self.recommended_option = None
            self.alternative_options = []
            self.optimization_options = []
            self.show_optimization_results = True
            self.status_message = "Hồ sơ hiện tại đã đáp ứng hoàn hảo khẩu vị rủi ro. Không yêu cầu tái cơ cấu."
            return

        # 4. Bắt đầu tìm kiếm phương án cứu hồ sơ DECLINED
        self.is_baseline_optimal = False
        self.is_optimizing = True
        self.visible_proposals_count = 2
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

        pool = self._find_candidate_pool(base_credit=base_credit, income=income, base_term=base_term)
        print(f"[AI Auto-Optimize] Candidate pool size: {len(pool)}")

        if not pool:
            self.is_optimizing = False
            self.show_optimization_results = True
            self.status_message = "No restructuring terms meet the risk appetite criteria for this client."
            return

        # 5. Phân bổ theo thứ hạng: Top 1 -> Recommended, Top 2..N -> Alternatives
        best = pool[0]
        self.recommended_option = self._build_optimization_entry(
            c=best,
            base_credit=base_credit,
            base_term=base_term,
            base_annuity=base_annuity,
            base_dti=base_dti,
            base_pd_percent=base_pd_percent,
            baseline_offered_rate=baseline_offered_rate,
            title="Recommended Proposal",
            opt_type="recommended",
        )

        formatted_alts = []
        for idx, alt in enumerate(pool[1:]):
            rank_num = idx + 2
            alt_entry = self._build_optimization_entry(
                c=alt,
                base_credit=base_credit,
                base_term=base_term,
                base_annuity=base_annuity,
                base_dti=base_dti,
                base_pd_percent=base_pd_percent,
                baseline_offered_rate=baseline_offered_rate,
                title=f"Option #{rank_num}",
                opt_type=f"option_{rank_num}",
            )
            formatted_alts.append(alt_entry)

        self.alternative_options = formatted_alts
        self.optimization_options = [self.recommended_option] + formatted_alts
        self.is_optimizing = False
        self.show_optimization_results = True

    @rx.event
    def apply_optimization_option(self, option: Optional[Dict[str, Any]] = None):
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
        self.is_baseline_optimal = False

    # Backwards compatibility alias
    auto_optimize_terms = ai_auto_optimize
