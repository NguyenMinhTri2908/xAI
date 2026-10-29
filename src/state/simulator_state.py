from typing import List
import reflex as rx
from .inspection_state import InspectionState, get_engine
from .base_state import DEFAULT_RECOMMENDED_OPTION
from src.config.pricing_config import retail_pricing_config
from src.pricing.pricing_engine import pricing_engine
from src.data_processing.ingestion_service import get_client_row_data


class SimulatorState(InspectionState):
    """Quản lý các đòn bẩy mô phỏng What-If (4 Sliders, Inputs, Real-time Recalculation)."""

    # Simulation active levers
    sim_amt_credit: float = 0.0
    sim_term_months: int = 12
    sim_amt_annuity: float = 0.0
    sim_amt_income_total: float = 0.0
    sim_dti: float = 0.0
    interest_rate_factor: float = 0.08
    is_sim_calculating: bool = False
    sim_offered_rate: float = 12.0
    sim_rate_display: str = "12.00%"
    sim_rate_delta_text: str = ""
    sim_rate_delta_color: str = "#94A3B8"
    sim_decision_status: str = "APPROVED"
    sim_decision_color: str = "#34D399"
    sim_credit_decision: str = "APPROVED"
    sim_credit_decision_color: str = "#34D399"

    # Two-way bound string variables for text input fields
    sim_amt_credit_str: str = "0"
    sim_term_months_str: str = "12"
    sim_amt_annuity_str: str = "0"
    sim_amt_income_str: str = "0"

    # Simulation real-time predicted outcomes
    sim_pd: float = 0.0
    sim_score_percent: float = 0.0
    sim_tier: str = "None"
    sim_decision: str = "None"
    sim_delta_pts: float = 0.0
    sim_delta_text: str = "0.00 pts"
    sim_delta_color: str = "#94A3B8"

    @rx.var
    def sim_credit_slider_min(self) -> float:
        base = float(self.baseline_amt_credit or self.sim_amt_credit or 100000.0)
        if base <= 0:
            base = 100000.0
        return float(round(base * 0.5, -2))

    @rx.var
    def sim_credit_slider_max(self) -> float:
        base = float(self.baseline_amt_credit or self.sim_amt_credit or 100000.0)
        if base <= 0:
            base = 100000.0
        return float(max(round(base * 1.5, -2), round(base * 0.5, -2) + 1000.0))

    @rx.var
    def sim_income_slider_min(self) -> float:
        base = float(self.baseline_amt_income_total or self.sim_amt_income_total or 50000.0)
        if base <= 0:
            base = 50000.0
        return float(round(base * 0.7, -2))

    @rx.var
    def sim_income_slider_max(self) -> float:
        base = float(self.baseline_amt_income_total or self.sim_amt_income_total or 50000.0)
        if base <= 0:
            base = 50000.0
        return float(max(round(base * 2.0, -2), round(base * 0.7, -2) + 1000.0))

    @rx.var
    def sim_annuity_slider_min(self) -> float:
        base_credit = float(self.baseline_amt_credit or self.sim_amt_credit or 100000.0)
        if base_credit <= 0:
            base_credit = 100000.0
        credit_min = base_credit * 0.5
        min_annuity = (credit_min / 60.0) * (1.0 + self.interest_rate_factor)
        return float(max(round(min_annuity, -2), 500.0))

    @rx.var
    def sim_annuity_slider_max(self) -> float:
        income = float(self.sim_amt_income_total or self.baseline_amt_income_total or 50000.0)
        if income <= 0:
            income = 50000.0
        max_dti = income * 0.70
        min_annuity = self.sim_annuity_slider_min
        return float(max(round(max_dti, -2), min_annuity + 1000.0))

    @rx.var
    def sim_amt_credit_slider(self) -> List[float]:
        val = float(self.sim_amt_credit or self.baseline_amt_credit or 100000.0)
        c_min = self.sim_credit_slider_min
        c_max = self.sim_credit_slider_max
        if c_min >= c_max:
            c_max = c_min + 1000.0
        clamped = min(max(val, c_min), c_max)
        return [clamped]

    @rx.var
    def sim_term_months_slider(self) -> List[float]:
        val = float(self.sim_term_months or self.baseline_term_months or 12.0)
        clamped = min(max(val, 3.0), 60.0)
        return [clamped]

    @rx.var
    def sim_amt_annuity_slider(self) -> List[float]:
        val = float(self.sim_amt_annuity or self.baseline_amt_annuity or 5000.0)
        a_min = self.sim_annuity_slider_min
        a_max = self.sim_annuity_slider_max
        if a_min >= a_max:
            a_max = a_min + 1000.0
        clamped = min(max(val, a_min), a_max)
        return [clamped]

    @rx.var
    def sim_amt_income_slider(self) -> List[float]:
        val = float(self.sim_amt_income_total or self.baseline_amt_income_total or 50000.0)
        i_min = self.sim_income_slider_min
        i_max = self.sim_income_slider_max
        if i_min >= i_max:
            i_max = i_min + 1000.0
        clamped = min(max(val, i_min), i_max)
        return [clamped]

    @rx.var
    def sim_credit_min_display(self) -> str:
        return f"${self.sim_credit_slider_min:,.0f} (-50%)"

    @rx.var
    def sim_credit_max_display(self) -> str:
        return f"${self.sim_credit_slider_max:,.0f} (+50%)"

    @rx.var
    def sim_income_min_display(self) -> str:
        return f"${self.sim_income_slider_min:,.0f}"

    @rx.var
    def sim_income_max_display(self) -> str:
        return f"${self.sim_income_slider_max:,.0f}"

    @rx.var
    def sim_annuity_min_display(self) -> str:
        return f"${self.sim_annuity_slider_min:,.0f}"

    @rx.var
    def sim_annuity_max_display(self) -> str:
        return f"${self.sim_annuity_slider_max:,.0f}"

    @rx.var
    def sim_amt_credit_display(self) -> str:
        val = float(self.sim_amt_credit or self.baseline_amt_credit or 0.0)
        return f"${val:,.0f}"

    @rx.var
    def sim_term_months_display(self) -> str:
        val = int(self.sim_term_months or self.baseline_term_months or 12)
        return f"{val} Months"

    @rx.var
    def sim_amt_annuity_display(self) -> str:
        val = float(self.sim_amt_annuity or self.baseline_amt_annuity or 0.0)
        return f"${val:,.0f} / mo"

    @rx.var
    def sim_amt_income_display(self) -> str:
        val = float(self.sim_amt_income_total or self.baseline_amt_income_total or 0.0)
        return f"${val:,.0f}"

    @rx.var
    def sim_dti_display(self) -> str:
        val = float(self.sim_dti or self.baseline_dti or 0.0)
        return f"{val:.1f}%"

    @rx.var
    def sim_status_color(self) -> str:
        if self.sim_decision == "APPROVE":
            return "#10B981"
        elif self.sim_decision == "DECLINE":
            return "#EF4444"
        return "#F59E0B"

    @rx.var
    def sim_dti_color(self) -> str:
        if self.sim_dti <= 35.0:
            return "#10B981"
        elif self.sim_dti <= retail_pricing_config.max_dti_limit:
            return "#F59E0B"
        return "#EF4444"

    @rx.var
    def is_sim_dti_exceeded(self) -> bool:
        """Kiểm tra tỷ lệ DTI mô phỏng có vượt trần cho phép (max_dti_limit) hay không."""
        return float(self.sim_dti) > retail_pricing_config.max_dti_limit

    @rx.var
    def is_scenario_viable(self) -> bool:
        """Kiểm tra phương án mô phỏng có khả thi hay không (DTI <= max_dti_limit và PD không tăng quá 2.0 pts so với baseline)."""
        try:
            dti_ok = float(self.sim_dti) <= retail_pricing_config.max_dti_limit
            pd_ok = float(self.sim_score_percent) <= (float(self.baseline_score_percent) + 2.0)
            return dti_ok and pd_ok
        except (ValueError, TypeError):
            return True

    @rx.var
    def is_simulated_changed(self) -> bool:
        """Kiểm tra xem người dùng đã điều chỉnh bất kỳ tham số nào khác với Baseline hay chưa."""
        return (
            abs(self.sim_amt_credit - self.baseline_amt_credit) > 1.0
            or self.sim_term_months != self.baseline_term_months
            or abs(self.sim_amt_annuity - self.baseline_amt_annuity) > 1.0
            or abs(self.sim_amt_income_total - self.baseline_amt_income_total) > 1.0
            or abs(self.sim_score_percent - self.baseline_score_percent) > 0.001
        )

    @rx.var
    def pd_display_value(self) -> str:
        return f"{self.sim_score_percent:.2f}%"

    @rx.var
    def pd_delta_badge_text(self) -> str:
        diff = round(self.sim_score_percent - self.baseline_score_percent, 2)
        if diff > 0.0:
            return f"(+{diff:.2f}% pts)"
        elif diff < 0.0:
            return f"(-{abs(diff):.2f}% pts)"
        return ""

    @rx.var
    def pd_delta_color(self) -> str:
        diff = self.sim_score_percent - self.baseline_score_percent
        return "#10B981" if diff < 0.0 else "#EF4444"

    @rx.var
    def diff_credit_text(self) -> str:
        diff = round(self.sim_amt_credit - self.baseline_amt_credit)
        if diff > 0:
            return f"(+${diff:,.0f})"
        elif diff < 0:
            return f"(-${abs(diff):,.0f})"
        return ""

    @rx.var
    def diff_credit_color(self) -> str:
        diff = self.sim_amt_credit - self.baseline_amt_credit
        return "#10B981" if diff > 0 else "#EF4444"

    @rx.var
    def diff_term_text(self) -> str:
        diff = self.sim_term_months - self.baseline_term_months
        if diff > 0:
            return f"(+{diff}m)"
        elif diff < 0:
            return f"(-{abs(diff)}m)"
        return ""

    @rx.var
    def diff_term_color(self) -> str:
        diff = self.sim_term_months - self.baseline_term_months
        return "#10B981" if diff > 0 else "#EF4444"

    @rx.var
    def diff_annuity_text(self) -> str:
        diff = round(self.sim_amt_annuity - self.baseline_amt_annuity)
        if diff > 0:
            return f"(+${diff:,.0f})"
        elif diff < 0:
            return f"(-${abs(diff):,.0f})"
        return ""

    @rx.var
    def diff_annuity_color(self) -> str:
        diff = self.sim_amt_annuity - self.baseline_amt_annuity
        return "#10B981" if diff > 0 else "#EF4444"

    @rx.var
    def diff_income_text(self) -> str:
        diff = round(self.sim_amt_income_total - self.baseline_amt_income_total)
        if diff > 0:
            return f"(+${diff:,.0f})"
        elif diff < 0:
            return f"(-${abs(diff):,.0f})"
        return ""

    @rx.var
    def diff_income_color(self) -> str:
        diff = self.sim_amt_income_total - self.baseline_amt_income_total
        return "#10B981" if diff > 0 else "#EF4444"

    @rx.event
    def reset_simulation_to_baseline(self):
        """Khôi phục lại toàn bộ tham số Simulator về mức Baseline ban đầu của khách hàng."""
        # 1. Tính toán dứt điểm các giá trị an toàn (fallback hợp lệ chống kẹp kịch biên Radix UI)
        base_credit = float(self.baseline_amt_credit or 0.0)
        if base_credit <= 0.0:
            base_credit = 100000.0

        base_term = int(self.baseline_term_months or 0)
        if base_term <= 0:
            base_term = 12
        base_term = min(max(base_term, 3), 60)

        base_income = float(self.baseline_amt_income_total or 0.0)
        if base_income <= 0.0:
            base_income = 50000.0

        base_annuity = float(self.baseline_amt_annuity or 0.0)
        if base_annuity <= 0.0:
            base_annuity = round((base_credit / base_term) * (1.0 + self.interest_rate_factor), 1)

        base_dti = float(self.baseline_dti or 0.0)
        if base_dti <= 0.0:
            base_dti = round((base_annuity / base_income) * 100.0, 1)

        # 2. Gán các giá trị con trượt và giá trị số học
        self.sim_amt_credit = base_credit
        self.sim_term_months = base_term
        self.sim_amt_annuity = base_annuity
        self.sim_amt_income_total = base_income
        self.sim_dti = base_dti
        self.sim_pd = float(self.baseline_pd or 0.0)
        self.sim_score_percent = float(self.baseline_score_percent or 0.0)
        self.sim_tier = str(self.baseline_tier or "None")
        self.sim_decision = str(self.baseline_decision or "None")
        self.sim_offered_rate = float(self.baseline_offered_rate or 12.0)
        self.sim_rate_display = str(self.baseline_rate_display or "12.00%")
        self.sim_rate_delta_text = ""
        self.sim_rate_delta_color = "#94A3B8"
        self.sim_decision_status = str(self.baseline_decision_status or "APPROVED")
        self.sim_decision_color = str(self.baseline_decision_color or "#34D399")
        self.sim_credit_decision = self.sim_decision_status
        self.sim_credit_decision_color = self.sim_decision_color
        self.is_sim_calculating = False
        self.sim_delta_pts = 0.0
        self.sim_delta_text = "0.00 pts"
        self.sim_delta_color = "#94A3B8"

        if hasattr(self, "is_optimizing"):
            self.is_optimizing = False
        if hasattr(self, "is_loading_alternatives"):
            self.is_loading_alternatives = False
        if hasattr(self, "alternatives_loaded"):
            self.alternatives_loaded = False
        if hasattr(self, "show_optimization_results"):
            self.show_optimization_results = False
        if hasattr(self, "optimization_options"):
            self.optimization_options = []
        if hasattr(self, "recommended_option"):
            self.recommended_option = dict(DEFAULT_RECOMMENDED_OPTION)
        if hasattr(self, "alternative_options"):
            self.alternative_options = []
        if hasattr(self, "show_alternative_options"):
            self.show_alternative_options = False

        # 3. Đồng bộ chuỗi hiển thị input chống mất số (undefined)
        self.sim_amt_credit_str = f"{int(self.sim_amt_credit):,}"
        self.sim_term_months_str = str(int(self.sim_term_months))
        self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"
        self.sim_amt_income_str = f"{int(self.sim_amt_income_total):,}"

    def _sync_credit_or_term_drag(self):
        term = max(self.sim_term_months, 1)
        self.sim_amt_annuity = round((self.sim_amt_credit / term) * (1.0 + self.interest_rate_factor), 1)
        income = max(self.sim_amt_income_total, 1.0)
        self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
        self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"
        self.sim_amt_credit_str = f"{int(self.sim_amt_credit):,}"
        self.sim_term_months_str = str(int(self.sim_term_months))

    def _sync_credit_or_term_changed(self):
        self._sync_credit_or_term_drag()
        self.recalculate_simulation_pd()

    def _sync_annuity_changed(self):
        annuity = max(self.sim_amt_annuity, 1.0)
        raw_term = (self.sim_amt_credit * (1.0 + self.interest_rate_factor)) / annuity
        snapped_steps = [3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
        self.sim_term_months = min(snapped_steps, key=lambda s: abs(s - raw_term))
        income = max(self.sim_amt_income_total, 1.0)
        self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
        self.sim_term_months_str = str(int(self.sim_term_months))
        self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"
        self.recalculate_simulation_pd()

    def _sync_income_changed(self):
        income = max(self.sim_amt_income_total, 1.0)
        self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
        self.sim_amt_income_str = f"{int(self.sim_amt_income_total):,}"
        self.recalculate_simulation_pd()

    @rx.event
    def set_sim_credit_from_slider(self, val: List[float]):
        if val:
            clamped = min(max(float(val[0]), self.sim_credit_slider_min), self.sim_credit_slider_max)
            if clamped == self.sim_amt_credit:
                return
            self.sim_amt_credit = clamped
            self.is_sim_calculating = True
            self._sync_credit_or_term_drag()

    @rx.event
    def set_sim_term_from_slider(self, val: List[float]):
        if val:
            raw_val = min(max(float(val[0]), 3.0), 60.0)
            snapped_steps = [3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
            new_term = min(snapped_steps, key=lambda s: abs(s - raw_val))
            if new_term == self.sim_term_months:
                return
            self.sim_term_months = new_term
            self.is_sim_calculating = True
            self._sync_credit_or_term_drag()

    @rx.event
    def set_sim_annuity_from_slider(self, val: List[float]):
        if val:
            clamped = min(max(float(val[0]), self.sim_annuity_slider_min), self.sim_annuity_slider_max)
            if clamped == self.sim_amt_annuity:
                return
            self.sim_amt_annuity = clamped
            self.is_sim_calculating = True
            raw_term = (self.sim_amt_credit * (1.0 + self.interest_rate_factor)) / max(self.sim_amt_annuity, 1.0)
            snapped_steps = [3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
            self.sim_term_months = min(snapped_steps, key=lambda s: abs(s - raw_term))
            income = max(self.sim_amt_income_total, 1.0)
            self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
            self.sim_term_months_str = str(int(self.sim_term_months))
            self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"

    @rx.event
    def set_sim_income_from_slider(self, val: List[float]):
        if val:
            clamped = min(max(float(val[0]), self.sim_income_slider_min), self.sim_income_slider_max)
            if clamped == self.sim_amt_income_total:
                return
            self.sim_amt_income_total = clamped
            self.is_sim_calculating = True
            income = max(self.sim_amt_income_total, 1.0)
            self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
            self.sim_amt_income_str = f"{int(self.sim_amt_income_total):,}"

    @rx.event
    def commit_sim_slider(self, val: List[float]):
        self.recalculate_simulation_pd()

    @rx.event
    def set_sim_term_preset(self, months: int):
        self.sim_term_months = int(months)
        self._sync_credit_or_term_changed()

    @rx.event
    def set_sim_credit_from_input(self, val: str):
        self.sim_amt_credit_str = val
        clean = val.replace("$", "").replace(",", "").strip()
        try:
            num = float(clean)
            if num > 0:
                self.sim_amt_credit = num
                term = max(self.sim_term_months, 1)
                self.sim_amt_annuity = round((self.sim_amt_credit / term) * (1.0 + self.interest_rate_factor), 1)
                self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"
                income = max(self.sim_amt_income_total, 1.0)
                self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
                self.recalculate_simulation_pd()
        except (ValueError, TypeError):
            pass

    @rx.event
    def set_sim_term_from_input(self, val: str):
        self.sim_term_months_str = val
        clean = val.replace("m", "").replace("mo", "").replace("months", "").strip()
        try:
            num = int(clean)
            if num > 0:
                self.sim_term_months = num
                term = max(self.sim_term_months, 1)
                self.sim_amt_annuity = round((self.sim_amt_credit / term) * (1.0 + self.interest_rate_factor), 1)
                self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"
                income = max(self.sim_amt_income_total, 1.0)
                self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
                self.recalculate_simulation_pd()
        except (ValueError, TypeError):
            pass

    @rx.event
    def set_sim_annuity_from_input(self, val: str):
        self.sim_amt_annuity_str = val
        clean = val.replace("$", "").replace(",", "").replace("/ mo", "").strip()
        try:
            num = float(clean)
            if num > 0:
                self.sim_amt_annuity = num
                raw_term = (self.sim_amt_credit * (1.0 + self.interest_rate_factor)) / self.sim_amt_annuity
                snapped_steps = [3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
                self.sim_term_months = min(snapped_steps, key=lambda s: abs(s - raw_term))
                self.sim_term_months_str = str(int(self.sim_term_months))
                income = max(self.sim_amt_income_total, 1.0)
                self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
                self.recalculate_simulation_pd()
        except (ValueError, TypeError):
            pass

    @rx.event
    def set_sim_income_from_input(self, val: str):
        self.sim_amt_income_str = val
        clean = val.replace("$", "").replace(",", "").strip()
        try:
            num = float(clean)
            if num > 0:
                self.sim_amt_income_total = num
                income = max(self.sim_amt_income_total, 1.0)
                self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
                self.recalculate_simulation_pd()
        except (ValueError, TypeError):
            pass

    @rx.event
    def recalculate_simulation_pd(self):
        """Chạy suy luận lại xác suất vỡ nợ (PD), Rating Tier, Lãi suất RBP và Quyết định tín dụng theo thời gian thực."""
        if not self.selected_client_id:
            self.is_sim_calculating = False
            return

        try:
            engine = get_engine()
            if (getattr(engine, "_cached_clean_df", None) is None or getattr(engine, "_cached_client_id", None) != str(self.selected_client_id)) and self.selected_client_id:
                client_series = get_client_row_data(self.selected_client_id)
                if client_series is not None:
                    engine.cache_client_features(client_series, str(self.selected_client_id))

            credit = float(self.sim_amt_credit)
            annuity = float(self.sim_amt_annuity)
            income = float(self.sim_amt_income_total)
            if credit <= 0:
                credit = float(self.baseline_amt_credit) if float(self.baseline_amt_credit) > 0 else 100000.0
            if annuity <= 0:
                annuity = float(self.baseline_amt_annuity) if float(self.baseline_amt_annuity) > 0 else 5000.0
            if income <= 0:
                income = float(self.baseline_amt_income_total) if float(self.baseline_amt_income_total) > 0 else 50000.0

            sim_pd, sim_tier, sim_decision = engine.predict_pd_from_cache(
                credit=credit,
                annuity=annuity,
                income=income,
            )

            baseline_pd_dec = float(self.baseline_score_percent) / 100.0 if self.baseline_score_percent > 0 else (float(self.baseline_pd) if self.baseline_pd > 0 else 0.0377)
            import math
            if sim_pd is None or math.isnan(float(sim_pd)) or float(sim_pd) <= 0.0001:
                print(f"[recalculate_simulation_pd] Warning: sim_pd was {sim_pd}, falling back to baseline {baseline_pd_dec}")
                sim_pd = baseline_pd_dec
                sim_tier = self.baseline_tier if self.baseline_tier != "None" else "Tier A"
                sim_decision = self.baseline_decision if self.baseline_decision != "None" else "APPROVE"

            self.sim_pd = float(sim_pd)
            self.sim_score_percent = round(self.sim_pd * 100.0, 2)
            self.sim_tier = sim_tier
            self.sim_decision = sim_decision

            delta = round(self.sim_score_percent - self.baseline_score_percent, 2)
            self.sim_delta_pts = delta

            if delta > 0.0:
                self.sim_delta_text = f"▲ +{abs(delta):.2f} pts"
                self.sim_delta_color = "#EF4444"
            elif delta < 0.0:
                self.sim_delta_text = f"▼ -{abs(delta):.2f} pts"
                self.sim_delta_color = "#10B981"
            else:
                self.sim_delta_text = "0.00 pts"
                self.sim_delta_color = "#94A3B8"

            pricing_res = pricing_engine.compute_baseline_pricing(
                self.sim_pd,
                int(self.sim_term_months),
            )
            self.sim_offered_rate = pricing_res["applied_rate_percent"]
            self.sim_rate_display = pricing_res["applied_rate_display"]

            diff_rate = round(self.sim_offered_rate - self.baseline_offered_rate, 2)
            if abs(diff_rate) < 0.01:
                self.sim_rate_delta_text = ""
            else:
                sign = "+" if diff_rate > 0 else ""
                self.sim_rate_delta_text = f"({sign}{diff_rate:.2f}%)"
                self.sim_rate_delta_color = "#F87171" if diff_rate > 0 else "#34D399"

            eval_res = pricing_engine.evaluate_credit_decision(
                pd_decimal=float(self.sim_pd),
                dti_percent=float(self.sim_dti),
            )
            self.sim_decision_status = eval_res["decision"]
            self.sim_decision_color = eval_res["color"]
            self.sim_credit_decision = self.sim_decision_status
            self.sim_credit_decision_color = self.sim_decision_color

            print(f"[recalculate_simulation_pd] Client ID={self.selected_client_id} | Output sim_pd={self.sim_pd:.4f} ({self.sim_score_percent}%) | Baseline PD={self.baseline_pd:.4f} ({self.baseline_score_percent}%) | Delta={delta:+.2f} pts | Decision={self.sim_decision_status}")

        except Exception as e:
            print(f"[recalculate_simulation_pd] Error: {e}")
            baseline_pd_dec = float(self.baseline_score_percent) / 100.0 if self.baseline_score_percent > 0 else (float(self.baseline_pd) if self.baseline_pd > 0 else 0.0377)
            self.sim_pd = float(baseline_pd_dec)
            self.sim_score_percent = round(self.sim_pd * 100.0, 2)
            self.sim_delta_pts = 0.0
            self.sim_delta_text = "0.00 pts"
            self.sim_delta_color = "#94A3B8"
            eval_res = pricing_engine.evaluate_credit_decision(
                pd_decimal=float(self.sim_pd),
                dti_percent=float(self.sim_dti),
            )
            self.sim_decision_status = eval_res["decision"]
            self.sim_decision_color = eval_res["color"]
            self.sim_credit_decision = self.sim_decision_status
            self.sim_credit_decision_color = self.sim_decision_color
            try:
                pricing_res = pricing_engine.compute_baseline_pricing(
                    self.sim_pd,
                    int(self.sim_term_months),
                )
                self.sim_offered_rate = pricing_res["applied_rate_percent"]
                self.sim_rate_display = pricing_res["applied_rate_display"]
            except Exception:
                pass
        finally:
            self.is_sim_calculating = False

