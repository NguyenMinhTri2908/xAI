import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from .feature_search_state import FeatureSearchState
from .formatters import format_client_age, format_client_experience

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import reflex as rx
import pandas as pd
from src.config import DEMO_SAMPLES_PARQUET
from src.engine.credit_scoring import CreditScoringEngine

_ENGINE = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = CreditScoringEngine()
    return _ENGINE


class UnderwritingState(rx.State):
    """Reflex state quản lý hồ sơ và thẩm định tín dụng."""

    client_list: List[Dict[str, Any]] = []
    selected_client_id: str = ""
    is_loading: bool = False

    current_pd: float = 0.0
    current_score_percent: float = 0.0
    current_tier: str = "None"
    current_decision: str = "None"
    top_risk_factors: List[Dict[str, Any]] = []
    top_positive_factors: List[Dict[str, Any]] = []
    selected_client_raw: Dict[str, Any] = {}

    current_client_shap: Dict[str, float] = {}

    def load_demo_clients(self):
        """Tải dữ liệu bảng từ demo_samples.parquet."""
        if not os.path.exists(DEMO_SAMPLES_PARQUET):
            return

        df = pd.read_parquet(DEMO_SAMPLES_PARQUET)
        summary_cols = ["SK_ID_CURR", "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY"]
        available_cols = [c for c in summary_cols if c in df.columns]

        table_df = df[available_cols].head(50).copy()

        if "AMT_INCOME_TOTAL" in table_df.columns:
            table_df["INCOME_DISPLAY"] = table_df["AMT_INCOME_TOTAL"].apply(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "None"
            )
        if "AMT_CREDIT" in table_df.columns:
            table_df["CREDIT_DISPLAY"] = table_df["AMT_CREDIT"].apply(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "None"
            )
        if "AMT_ANNUITY" in table_df.columns:
            table_df["ANNUITY_DISPLAY"] = table_df["AMT_ANNUITY"].apply(
                lambda x: f"${x:,.0f}" if pd.notna(x) and x > 0 else "None"
            )

        self.client_list = table_df.to_dict(orient="records")

        if self.client_list and not self.selected_client_id:
            first_id = str(self.client_list[0]["SK_ID_CURR"])
            return self.select_and_evaluate_client(first_id)

    # --- COMPUTED VARS (Trả về None nếu rỗng) ---

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
            return "None"
        pd_val = float(self.current_pd)
        pd_pct = pd_val * 100 if pd_val <= 1.0 else pd_val
        return f"{pd_pct:.1f}%"

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

    # --- LOGIC THẨM ĐỊNH VÀ TÍNH TOÁN ---

    def select_and_evaluate_client(self, client_id: str):
        self.selected_client_id = client_id
        self.is_loading = True

        df = pd.read_parquet(DEMO_SAMPLES_PARQUET)
        match = df[df["SK_ID_CURR"] == int(client_id)]

        if match.empty:
            self.is_loading = False
            return

        client_series = match.iloc[0]

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

        # 4. Tính toán TERM (Credit / Annuity)
        if credit_num > 0 and annuity_num > 0:
            term_months = round(credit_num / annuity_num)
            term_str = f"{term_months} months"
        else:
            term_str = "None"

        # 5. Tính toán PAYMENT-TO-INCOME (DTI)
        if income_num > 0 and annuity_num > 0:
            dti_ratio = (annuity_num / income_num) * 100
            dti_str = f"{dti_ratio:.1f}%"
        else:
            dti_str = "None"

        # 6. Gán Dictionary
        self.selected_client_raw = {
            "ID": str(client_id),
            "NAME": "Name",
            "AGE": format_client_age(client_series.get("AGE", client_series.get("DAYS_BIRTH"))),
            "EXPERIENCE": format_client_experience(client_series.get("EXPERIENCE", client_series.get("DAYS_EMPLOYED"))),
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
        # Nhận trực tiếp kết quả từ engine
        self.current_decision = result.get("decision", "None")

        raw_risks = [dict(item) for item in result.get("top_risk_factors", [])]
        raw_positives = [dict(item) for item in result.get("top_positive_factors", [])]

        shap_lookup: Dict[str, float] = {}
        if "all_shap_values" in result and isinstance(result["all_shap_values"], dict):
            shap_lookup = {k: round(float(v), 4) for k, v in result["all_shap_values"].items()}
        else:
            for item in raw_risks:
                feat = item.get("feature")
                if feat:
                    shap_lookup[feat] = round(float(item.get("shap_value", 0.0)), 4)
            for item in raw_positives:
                feat = item.get("feature")
                if feat:
                    shap_lookup[feat] = round(float(item.get("shap_value", 0.0)), 4)

        if raw_risks:
            max_risk = max([abs(float(f.get("shap_value", 0.0))) for f in raw_risks]) or 1.0
            for f in raw_risks:
                pct = round((abs(float(f.get("shap_value", 0.0))) / max_risk) * 100, 1)
                f["bar_width"] = f"{max(pct, 6.0)}%"

        if raw_positives:
            max_trust = max([abs(float(f.get("shap_value", 0.0))) for f in raw_positives]) or 1.0
            for f in raw_positives:
                pct = round((abs(float(f.get("shap_value", 0.0))) / max_trust) * 100, 1)
                f["bar_width"] = f"{max(pct, 6.0)}%"

        self.top_risk_factors = raw_risks
        self.top_positive_factors = raw_positives
        self.is_loading = False

        return FeatureSearchState.update_client_shap(shap_lookup)