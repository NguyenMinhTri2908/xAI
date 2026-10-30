from typing import List, Dict, Any
import reflex as rx
import pandas as pd
from .dataset_state import DatasetState
from .feature_search_state import FeatureSearchState
from src.ui.utils.formatters import format_client_age, format_client_experience
from src.engine.credit_scoring import get_scoring_engine
from src.pricing.pricing_engine import pricing_engine
from src.data_processing.ingestion_service import (
    get_client_row_data,
    load_dataset_from_source,
    get_active_client_ids,
    get_client_table_summary,
)
from src.services.explanation_service import process_shap_explanations
from src.services.financial_service import compute_derived_financials


def get_engine():
    return get_scoring_engine()


class InspectionState(DatasetState):
    """Quản lý thông tin hồ sơ khách hàng đang thẩm định, đánh giá rủi ro và các chỉ số Baseline."""

    # Kết quả thẩm định
    selected_client_id: str = ""
    selected_client_raw: Dict[str, Any] = {}
    current_client_shap: Dict[str, float] = {}

    current_pd: float = 0.0
    current_score_percent: float = 0.0
    current_tier: str = "None"
    current_decision: str = "None"
    top_risk_factors: List[Dict[str, Any]] = []
    top_positive_factors: List[Dict[str, Any]] = []

    # Baseline values (Original client record)
    baseline_amt_credit: float = 0.0
    baseline_term_months: int = 12
    baseline_amt_annuity: float = 0.0
    baseline_amt_income_total: float = 0.0
    baseline_dti: float = 0.0
    baseline_pd: float = 0.0
    baseline_score_percent: float = 0.0
    baseline_tier: str = "None"
    baseline_decision: str = "None"
    baseline_offered_rate: float = 12.0
    baseline_rate_display: str = "12.00%"
    baseline_decision_status: str = "APPROVED"
    baseline_decision_color: str = "#34D399"
    credit_decision_status: str = "APPROVED"
    credit_decision_color: str = "#34D399"
    credit_decision_text: str = "Approved under Risk Appetite"
    interest_rate_factor: float = 0.08
    underwriter_notes: str = ""

    def set_underwriter_notes(self, text: str):
        self.underwriter_notes = text

    @rx.event
    def record_decision(self, decision_type: str):
        """Lưu quyết định của chuyên viên thẩm định và hiển thị thông báo."""
        self.alert_token += 1
        current_token = self.alert_token
        status_label = "Approved with Conditions" if decision_type == "CONDITIONAL" else "Declined"
        self.alert_message = f"✓ Decision recorded: {status_label} for Client #{self.selected_client_id}"
        self.alert_type = "success" if decision_type == "CONDITIONAL" else "error"
        self.show_alert = True
        return self.auto_dismiss_alert(current_token)

    @rx.event
    def inspect_client(self, client_id: str):
        """Lưu selected_client_id vào State, kích hoạt đánh giá và chuyển sang Trang 2."""
        if client_id:
            res = self.select_and_evaluate_client(str(client_id))
            events = []
            if isinstance(res, list):
                events.extend(res)
            elif res:
                events.append(res)
            events.append(rx.redirect("/inspection"))
            return events
        return rx.redirect("/inspection")

    @rx.event
    def load_demo_clients(self):
        """Khởi động mặc định nạp demo_samples.parquet vào State nếu chưa có dataset."""
        if not self.available_client_ids:
            df, source_label = load_dataset_from_source("demo_samples")
            self.selected_dataset_source = "demo_samples"
            self.active_source_label = source_label
            self.available_client_ids = get_active_client_ids()
            self.total_clients_count = len(self.available_client_ids)
            self.client_list = get_client_table_summary(100)

        if self.available_client_ids and (not self.selected_client_id or self.selected_client_id == "None"):
            first_id = self.available_client_ids[0]
            return self.select_and_evaluate_client(first_id)
        elif self.available_client_ids and self.selected_client_id:
            from src.state.simulator_state import SimulatorState
            return SimulatorState.reset_simulation_to_baseline

    @rx.event
    def select_previous_client(self):
        """Chọn hồ sơ phía trước trong danh sách."""
        if not self.available_client_ids or not self.selected_client_id:
            return
        try:
            idx = self.available_client_ids.index(str(self.selected_client_id))
            if idx > 0:
                prev_id = self.available_client_ids[idx - 1]
                return type(self).select_and_evaluate_client(prev_id)
        except ValueError:
            pass

    @rx.event
    def select_next_client(self):
        """Chọn hồ sơ kế tiếp trong danh sách."""
        if not self.available_client_ids or not self.selected_client_id:
            return
        try:
            idx = self.available_client_ids.index(str(self.selected_client_id))
            if idx < len(self.available_client_ids) - 1:
                next_id = self.available_client_ids[idx + 1]
                return type(self).select_and_evaluate_client(next_id)
        except ValueError:
            pass

    @rx.var
    def client_id_options(self) -> List[str]:
        """Danh sách ID hiển thị cho Dropdown chọn hồ sơ (tối đa 500 ID đầu để UI nhẹ mượt)."""
        return self.available_client_ids[:500]

    @rx.var
    def is_first_client(self) -> bool:
        if not self.available_client_ids or not self.selected_client_id:
            return True
        return self.available_client_ids[0] == str(self.selected_client_id)

    @rx.var
    def is_last_client(self) -> bool:
        if not self.available_client_ids or not self.selected_client_id:
            return True
        return self.available_client_ids[-1] == str(self.selected_client_id)

    @rx.var
    def current_client_index_display(self) -> str:
        if not self.available_client_ids or not self.selected_client_id:
            return "1"
        try:
            idx = self.available_client_ids.index(str(self.selected_client_id))
            return f"{idx + 1}"
        except ValueError:
            return "1"

    @rx.var
    def client_age(self) -> str:
        return str(self.selected_client_raw.get("AGE", "None"))

    @rx.var
    def client_experience(self) -> str:
        return str(self.selected_client_raw.get("EXPERIENCE", "None"))

    @rx.var
    def client_credit(self) -> str:
        return str(self.selected_client_raw.get("Credit", "None"))

    @rx.var
    def client_annuity(self) -> str:
        return str(self.selected_client_raw.get("Annuity", "None"))

    @rx.var
    def client_term(self) -> str:
        return str(self.selected_client_raw.get("TERM", "None"))

    @rx.var
    def client_dti(self) -> str:
        return str(self.selected_client_raw.get("PAYMENT_TO_INCOME", "None"))

    @rx.var
    def pd_display(self) -> str:
        if not self.selected_client_id or self.current_decision == "None":
            return "0.00%"
        pd_val = float(self.current_pd)
        pd_pct = pd_val * 100 if pd_val <= 1.0 else pd_val
        return f"{pd_pct:.2f}%"

    @rx.var
    def baseline_pd_display(self) -> str:
        return f"{self.baseline_score_percent:.2f}%"

    @rx.var
    def decision_color(self) -> str:
        dec = self.current_decision.upper()
        if "APPROVE" in dec:
            return "#10B981"  # Xanh lá
        elif "WAIT" in dec or "REVIEW" in dec or "COMMITTEE" in dec:
            return "#F59E0B"  # Vàng hổ phách
        elif "DECLINE" in dec or "REJECT" in dec:
            return "#EF4444"  # Đỏ
        return "#94A3B8"

    @rx.var
    def decision_bg_color(self) -> str:
        dec = self.current_decision.upper()
        if "APPROVE" in dec:
            return "rgba(16, 185, 129, 0.12)"
        elif "WAIT" in dec or "REVIEW" in dec or "COMMITTEE" in dec:
            return "rgba(245, 158, 11, 0.12)"
        elif "DECLINE" in dec or "REJECT" in dec:
            return "rgba(239, 68, 68, 0.12)"
        return "rgba(15, 23, 42, 0.6)"

    @rx.event
    def select_and_evaluate_client(self, client_id: str):
        if not client_id:
            return
        self.selected_client_id = str(client_id)
        self.is_loading = True

        # Clean Reset toàn bộ trạng thái AI Optimizer cũ chống rò rỉ dữ liệu giữa các hồ sơ
        self.is_optimizing = False
        self.is_baseline_optimal = False
        self.show_optimization_results = False
        self.recommended_option = None
        self.alternative_options = []
        self.optimization_options = []
        self.visible_proposals_count = 2
        self.status_message = ""

        raw_series = get_client_row_data(client_id)
        if raw_series is None:
            self.is_loading = False
            return

        # Đảm bảo tính bất biến (Immutability): Tạo bản sao độc lập (Deep Copy)
        client_series = raw_series.copy()

        # 1. Trích xuất AMT_CREDIT
        credit_val = client_series.get("AMT_CREDIT", None)
        try:
            credit_num = float(credit_val) if pd.notna(credit_val) else 0.0
            credit_str = f"${credit_num:,.0f}" if credit_num > 0 else "None"
        except (ValueError, TypeError):
            credit_num = 0.0
            credit_str = "None"

        # 2. Trích xuất AMT_ANNUITY
        annuity_val = client_series.get("AMT_ANNUITY", None)
        try:
            annuity_num = float(annuity_val) if pd.notna(annuity_val) else 0.0
            annuity_str = f"${annuity_num:,.0f} / mo" if annuity_num > 0 else "None"
        except (ValueError, TypeError):
            annuity_num = 0.0
            annuity_str = "None"

        # 3. Trích xuất AMT_INCOME_TOTAL
        income_val = client_series.get("AMT_INCOME_TOTAL", None)
        try:
            income_num = float(income_val) if pd.notna(income_val) else 0.0
            income_str = f"${income_num:,.0f}" if income_num > 0 else "None"
        except (ValueError, TypeError):
            income_num = 0.0
            income_str = "None"

        # 4 & 5. Tính toán TERM và DTI phái sinh qua Domain Financial Service
        fin_metrics = compute_derived_financials(credit_num, annuity_num, income_num)
        term_months = fin_metrics["term_months"]
        term_str = fin_metrics["term_display"]
        dti_ratio = fin_metrics["dti_percent"]
        dti_str = fin_metrics["dti_display"]

        # 6. Gán Dictionary Thông Tin Khách Hàng
        raw_age = client_series.get("AGE")
        if pd.isna(raw_age) or raw_age is None:
            raw_age = client_series.get("DAYS_BIRTH")
        if pd.isna(raw_age) or raw_age is None:
            raw_age = client_series.get("AGE_YEARS")

        raw_exp = client_series.get("EXPERIENCE")
        if pd.isna(raw_exp) or raw_exp is None:
            raw_exp = client_series.get("DAYS_EMPLOYED")
        if pd.isna(raw_exp) or raw_exp is None:
            raw_exp = client_series.get("EMPLOYED_YEARS")

        self.selected_client_raw = {
            "ID": str(client_id),
            "NAME": "Client Name",
            "AGE": format_client_age(raw_age),
            "EXPERIENCE": format_client_experience(raw_exp),
            "Credit": credit_str,
            "Annuity": annuity_str,
            "TERM": term_str,
            "PAYMENT_TO_INCOME": dti_str,
            "Income": income_str,
        }

        # 7. Chạy mô hình backend
        engine = get_engine()
        result = engine.predict_single(client_series)

        self.current_pd = result.get("probability_of_default", 0.0)
        self.current_score_percent = result.get("score_percent", 0.0)
        self.current_tier = result.get("tier", "None")
        self.current_decision = result.get("decision", "None")

        # Trích xuất và chuẩn hóa giải thích SHAP qua Domain Explanation Service
        raw_risks, raw_positives, shap_lookup = process_shap_explanations(result)
        self.top_risk_factors = raw_risks
        self.top_positive_factors = raw_positives
        self.current_client_shap = shap_lookup

        # 8. Cập nhật Baseline và khởi tạo Terms Simulator
        self.baseline_amt_credit = credit_num
        self.baseline_amt_annuity = annuity_num
        self.baseline_amt_income_total = income_num
        self.baseline_term_months = term_months if (credit_num > 0 and annuity_num > 0) else 12
        self.baseline_dti = dti_ratio if (income_num > 0 and annuity_num > 0) else 0.0
        self.baseline_pd = self.current_pd
        self.baseline_score_percent = self.current_score_percent
        self.baseline_tier = self.current_tier
        self.baseline_decision = self.current_decision

        pd_dec = float(self.baseline_score_percent) / 100.0
        client_term = int(getattr(self, "baseline_term_months", 24))

        # Tính toán lãi suất RBP Baseline
        p_res = pricing_engine.compute_baseline_pricing(pd_dec, client_term)
        self.baseline_offered_rate = p_res["applied_rate_percent"]
        self.baseline_rate_display = p_res["applied_rate_display"]

        # Đánh giá quyết định tín dụng theo Cut-off & DTI cho Baseline qua Pricing Engine tập trung
        eval_res = pricing_engine.evaluate_credit_decision(
            pd_decimal=pd_dec,
            dti_percent=float(self.baseline_dti),
        )
        self.baseline_decision_status = eval_res["decision"]
        self.baseline_decision_color = eval_res["color"]
        self.credit_decision_text = eval_res["status_text"]

        self.credit_decision_status = self.baseline_decision_status
        self.credit_decision_color = self.baseline_decision_color

        self.interest_rate_factor = fin_metrics["implied_rate_factor"]

        # Tiền xử lý và lưu cache 891 features cho client hiện tại
        try:
            engine.cache_client_features(client_series, str(client_id))
        except Exception as e:
            print(f"[cache_client_features] Warning: {e}")

        if hasattr(self, "reset_simulation_to_baseline"):
            try:
                self.reset_simulation_to_baseline()
            except Exception:
                pass
        self.is_loading = False

        from src.state.simulator_state import SimulatorState

        return [
            SimulatorState.reset_simulation_to_baseline,
            FeatureSearchState.update_client_shap(shap_lookup),
        ]

