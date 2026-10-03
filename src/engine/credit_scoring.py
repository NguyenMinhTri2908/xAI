import os
import sys
from pathlib import Path

# Ensure project root is present in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import joblib
import numpy as np
import pandas as pd
import shap
from typing import Dict, Any, Tuple, List

from src.config import MODEL_DIR, CONFIG_PATH, SCHEMA_PATH, BENCHMARK_PATH


class CreditScoringEngine:
    """
    Automated Credit Scoring & Underwriting Engine.
    - Loads 10-fold ensemble models (5 LightGBM + 5 XGBoost).
    - Computes Probability of Default (PD) via Weighted Soft Voting.
    - Assigns standard Credit Tiers (A, B, C, D) and underwriting recommendations.
    - Extracts local feature attribution via TreeSHAP and decodes categorical codes using metadata.
    """

    def __init__(self):
        print("⚡ Initializing Credit Scoring Engine...")
        self.config = self._load_json(CONFIG_PATH)
        self.metadata = self._load_json(SCHEMA_PATH)

        self.benchmarks = self._load_json(BENCHMARK_PATH) if os.path.exists(BENCHMARK_PATH) else {}

        self.features: List[str] = self.config["feature_names"]
        self.blend_weights: Dict[str, float] = self.config.get("weights", {
            "lightgbm": 0.5,
            "xgboost": 0.5
        })

        self.lgb_models = []
        self.xgb_models = []
        self._load_all_models()

        # Extract native training categories from the first XGBoost model to prevent category mismatches
        self._sync_native_categories()

        print("🔍 Initializing SHAP TreeExplainer...")
        self.shap_explainer = shap.TreeExplainer(self.lgb_models[0])

    def _load_json(self, path: str) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_all_models(self):
        print("📦 Loading 10-fold ensemble models into memory...")
        for fold in range(1, 6):
            lgb_path = os.path.join(MODEL_DIR, f"lgb_model_fold_{fold}.joblib")
            xgb_path = os.path.join(MODEL_DIR, f"xgb_model_fold_{fold}.joblib")

            if os.path.exists(lgb_path):
                self.lgb_models.append(joblib.load(lgb_path))
            else:
                raise FileNotFoundError(f"Missing model artifact: {lgb_path}")

            if os.path.exists(xgb_path):
                self.xgb_models.append(joblib.load(xgb_path))
            else:
                raise FileNotFoundError(f"Missing model artifact: {xgb_path}")
        print(
            f"   ✓ Successfully loaded: {len(self.lgb_models)} LightGBM folds and {len(self.xgb_models)} XGBoost folds.")

    def _sync_native_categories(self):
        """
        Synchronizes valid category values directly from the trained XGBoost model attributes.
        Falls back to metadata values excluding synthetic 'Missing' placeholders.
        """
        self.native_categories = {}
        first_xgb = self.xgb_models[0]

        # Check if native feature types or categories are stored in XGBoost booster
        raw_cats = getattr(first_xgb, "categorical_categories_", None)
        mappings = self.metadata.get("categorical_mappings", {})

        for col, map_info in mappings.items():
            valid_labels = [label for label in map_info.get("valid_labels", []) if label != "Missing"]
            self.native_categories[col] = valid_labels

    def _align_and_cast_features(self, df_input: pd.DataFrame) -> pd.DataFrame:
        """
        Enforces schema alignment, data types, and native categorical category constraints.
        Unknown or null values are mapped to np.nan so both tree engines route via default branches.
        """
        df_aligned = df_input.reindex(columns=self.features).copy()

        for col, valid_cats in self.native_categories.items():
            if col in df_aligned.columns:
                # Map values: retain valid training categories, set invalid/unknown to np.nan
                df_aligned[col] = df_aligned[col].apply(
                    lambda x: x if pd.notna(x) and str(x) in valid_cats else np.nan
                )
                df_aligned[col] = pd.Categorical(df_aligned[col], categories=valid_cats)

        # Enforce numeric columns to numeric float/int
        numeric_cols = [c for c in self.features if c not in self.native_categories]
        for c in numeric_cols:
            if c in df_aligned.columns:
                df_aligned[c] = pd.to_numeric(df_aligned[c], errors="coerce")

        return df_aligned

    def _determine_credit_tier(self, pd_score: float) -> Tuple[str, str]:
        """
        Risk tier stratification and automated policy recommendation:
        - Tier A (PD < 3.5%): Prime Low Risk -> Auto-Approve
        - Tier B (3.5% <= PD < 8.0%): Near-Prime Moderate Risk -> Standard Approve
        - Tier C (8.0% <= PD < 15.0%): Sub-Prime High Risk -> Manual Underwriter Review
        - Tier D (PD >= 15.0%): Deep Sub-Prime / Default Imminent -> Reject
        """
        if pd_score < 0.035:
            return "Tier A", "AUTO_APPROVE"
        elif pd_score < 0.080:
            return "Tier B", "STANDARD_APPROVE"
        elif pd_score < 0.150:
            return "Tier C", "MANUAL_REVIEW"
        else:
            return "Tier D", "REJECT"

    def predict_single(self, client_series: pd.Series) -> Dict[str, Any]:
        """Runs full inference and feature attribution for a single loan application record."""
        df_row = pd.DataFrame([client_series])
        df_clean = self._align_and_cast_features(df_row)

        # 1. LightGBM 5-fold ensemble prediction
        lgb_preds = [model.predict_proba(df_clean)[:, 1][0] for model in self.lgb_models]
        mean_lgb = float(np.mean(lgb_preds))

        # 2. XGBoost 5-fold ensemble prediction
        xgb_preds = [model.predict_proba(df_clean)[:, 1][0] for model in self.xgb_models]
        mean_xgb = float(np.mean(xgb_preds))

        # 3. Weighted ensemble blend
        w_lgb = self.blend_weights.get("lightgbm", 0.5)
        w_xgb = self.blend_weights.get("xgboost", 0.5)
        final_pd = float((mean_lgb * w_lgb) + (mean_xgb * w_xgb))

        # 4. Underwriting policy tier assignment
        tier, decision = self._determine_credit_tier(final_pd)

        # 5. TreeSHAP feature attribution
        shap_values = self.shap_explainer(df_clean)
        shap_array = shap_values.values[0]

        # Extract full 891 SHAP map for Feature Search Explorer
        all_shap_dict: Dict[str, float] = {
            feat: round(float(val), 4)
            for feat, val in zip(self.features, shap_array)
        }

        feature_importance = pd.DataFrame({
            "feature": self.features,
            "shap_value": shap_array,
            "raw_value": df_row[self.features].iloc[0].values
        })

        # Decode numeric/categorical values to human-readable strings via metadata contract
        mappings = self.metadata.get("categorical_mappings", {})

        def translate_value(row):
            col = row["feature"]
            val = row["raw_value"]
            if col in mappings:
                if pd.isna(val) or str(val).lower() in ["nan", "none"]:
                    return "Missing / Not Specified"
                val_str = str(int(val)) if isinstance(val, (int, float)) and not np.isnan(val) else str(val)
                return mappings[col].get("code_to_label", {}).get(val_str, str(val))
            return val

        feature_importance["display_value"] = feature_importance.apply(translate_value, axis=1)

        # Top 5 risk-increasing drivers (Negative factors)
        risk_drivers = (
            feature_importance.sort_values(by="shap_value", ascending=False)
            .head(5)
            .to_dict(orient="records")
        )

        # Top 5 risk-reducing drivers (Positive factors)
        trust_drivers = (
            feature_importance.sort_values(by="shap_value", ascending=True)
            .head(5)
            .to_dict(orient="records")
        )

        return {
            "probability_of_default": round(final_pd, 4),
            "score_percent": round(final_pd * 100, 2),
            "tier": tier,
            "decision": decision,
            "model_breakdown": {
                "lightgbm_mean_pd": round(mean_lgb, 4),
                "xgboost_mean_pd": round(mean_xgb, 4)
            },
            "top_risk_factors": risk_drivers,
            "top_positive_factors": trust_drivers,
            "all_shap_values": all_shap_dict  # <- Cung cấp toàn bộ 891 giá trị SHAP
        }


# ==============================================================================
# OFFLINE SANITY TEST
# ==============================================================================
if __name__ == "__main__":
    import time
    from src.config import DEMO_SAMPLES_PARQUET

    engine = CreditScoringEngine()

    print(f"📖 Loading sample records from: {DEMO_SAMPLES_PARQUET}")
    demo_df = pd.read_parquet(DEMO_SAMPLES_PARQUET)
    sample_client = demo_df.iloc[0]
    client_id = sample_client.get("SK_ID_CURR", "N/A")

    t0 = time.time()
    result = engine.predict_single(sample_client)
    latency = (time.time() - t0) * 1000

    print("=" * 80)
    print(f"📋 UNDERWRITING ASSESSMENT REPORT: SK_ID_CURR = {client_id}")
    print(f" • Probability of Default (PD) : {result['score_percent']}%")
    print(f" • Credit Rating Tier          : {result['tier']}")
    print(f" • Recommended Decision        : {result['decision']}")
    print(f" • Inference Latency           : {latency:.2f} ms")
    print(f" • Total SHAP Features Mapped  : {len(result['all_shap_values']):,}")
    print("\n🔍 TOP 3 RISK DRIVERS (SHAP Positive Contributions):")
    for idx, f in enumerate(result["top_risk_factors"][:3], 1):
        print(f"   {idx}. {f['feature']} (Value: {f['display_value']}) -> Impact: +{f['shap_value']:.4f}")
    print("\n🔍 TOP 3 TRUST FACTORS (SHAP Negative Contributions):")
    for idx, f in enumerate(result["top_positive_factors"][:3], 1):
        print(f"   {idx}. {f['feature']} (Value: {f['display_value']}) -> Impact: {f['shap_value']:.4f}")
    print("=" * 80)