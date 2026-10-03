import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from .feature_search_state import FeatureSearchState

# Ensure project root is present in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import reflex as rx
import pandas as pd
from src.config import DEMO_SAMPLES_PARQUET
from src.engine.credit_scoring import CreditScoringEngine

# Global singleton engine to prevent reloading models on every state change
_ENGINE = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = CreditScoringEngine()
    return _ENGINE


class UnderwritingState(rx.State):
    """Reflex state managing customer records and credit underwriting evaluation."""

    # Table data
    client_list: List[Dict[str, Any]] = []
    selected_client_id: str = ""
    is_loading: bool = False

    # Current evaluation results
    current_pd: float = 0.0
    current_score_percent: float = 0.0
    current_tier: str = "N/A"
    current_decision: str = "PENDING"
    top_risk_factors: List[Dict[str, Any]] = []
    top_positive_factors: List[Dict[str, Any]] = []
    selected_client_raw: Dict[str, Any] = {}

    # Comprehensive SHAP map for all 891 features of the active client
    current_client_shap: Dict[str, float] = {}

    def load_demo_clients(self):
        """Loads records from demo_samples.parquet into the overview table."""
        if not os.path.exists(DEMO_SAMPLES_PARQUET):
            return

        df = pd.read_parquet(DEMO_SAMPLES_PARQUET)

        # Display key summary attributes in the table
        summary_cols = ["SK_ID_CURR", "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY"]
        available_cols = [c for c in summary_cols if c in df.columns]

        table_df = df[available_cols].head(50).copy()

        # Format display numbers
        if "AMT_INCOME_TOTAL" in table_df.columns:
            table_df["INCOME_DISPLAY"] = table_df["AMT_INCOME_TOTAL"].apply(lambda x: f"${x:,.0f}")
        if "AMT_CREDIT" in table_df.columns:
            table_df["CREDIT_DISPLAY"] = table_df["AMT_CREDIT"].apply(lambda x: f"${x:,.0f}")
        if "AMT_ANNUITY" in table_df.columns:
            table_df["ANNUITY_DISPLAY"] = table_df["AMT_ANNUITY"].apply(
                lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")

        self.client_list = table_df.to_dict(orient="records")

        # Automatically evaluate the first client by default
        if self.client_list and not self.selected_client_id:
            first_id = str(self.client_list[0]["SK_ID_CURR"])
            self.select_and_evaluate_client(first_id)

    def select_and_evaluate_client(self, client_id: str):
        """Selects a client, runs the inference engine, and updates underwriting metrics."""
        self.selected_client_id = client_id
        self.is_loading = True

        df = pd.read_parquet(DEMO_SAMPLES_PARQUET)
        match = df[df["SK_ID_CURR"] == int(client_id)]

        if match.empty:
            self.is_loading = False
            return

        client_series = match.iloc[0]
        self.selected_client_raw = {
            "ID": str(client_id),
            "Income": f"${client_series.get('AMT_INCOME_TOTAL', 0):,.0f}",
            "Credit": f"${client_series.get('AMT_CREDIT', 0):,.0f}",
            "Annuity": f"${client_series.get('AMT_ANNUITY', 0):,.0f}",
        }

        # Run scoring engine
        engine = get_engine()
        result = engine.predict_single(client_series)

        self.current_pd = result["probability_of_default"]
        self.current_score_percent = result["score_percent"]
        self.current_tier = result["tier"]
        self.current_decision = result["decision"]

        # Trích xuất danh sách thô
        raw_risks = [dict(item) for item in result.get("top_risk_factors", [])]
        raw_positives = [dict(item) for item in result.get("top_positive_factors", [])]

        # 1. Trích xuất SHAP lookup
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

        # 2. Tính bar_width cho nhóm Risk
        if raw_risks:
            max_risk = max([abs(float(f.get("shap_value", 0.0))) for f in raw_risks])
            if max_risk == 0:
                max_risk = 1.0
            for f in raw_risks:
                pct = round((abs(float(f.get("shap_value", 0.0))) / max_risk) * 100, 1)
                f["bar_width"] = f"{max(pct, 6.0)}%"

        # 3. Tính bar_width cho nhóm Trust
        if raw_positives:
            max_trust = max([abs(float(f.get("shap_value", 0.0))) for f in raw_positives])
            if max_trust == 0:
                max_trust = 1.0
            for f in raw_positives:
                pct = round((abs(float(f.get("shap_value", 0.0))) / max_trust) * 100, 1)
                f["bar_width"] = f"{max(pct, 6.0)}%"

        self.top_risk_factors = raw_risks
        self.top_positive_factors = raw_positives
        self.is_loading = False

        # Đẩy dữ liệu SHAP trực tiếp sang FeatureSearchState
        return FeatureSearchState.update_client_shap(shap_lookup)