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
from typing import Dict, Any, Tuple, List, Optional

from src.config import MODEL_DIR, CONFIG_PATH, SCHEMA_PATH, BENCHMARK_PATH
from src.config.pricing_config import retail_pricing_config


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
        Phân tầng xếp hạng rủi ro (Credit Tier) và khuyến nghị chính sách đồng bộ với RetailPricingConfig:
        Ngưỡng Cut-off tối ưu T* = 6.80% (0.0680), kiểm soát Bad Rate danh mục <= 2.96%:
        - PD <= 3.40%: Tier A (Super Prime / Rủi ro thấp) -> APPROVE
        - 3.40% < PD <= 6.80%: Tier B (Prime / Thỏa mãn khẩu vị rủi ro) -> APPROVE
        - 6.80% < PD <= 10.20%: Tier C (Vùng xám / Cần hội đồng phê duyệt) -> WAITING / COMMITTEE REVIEW
        - PD > 10.20%: Tier D (High Risk / Vượt ngưỡng rủi ro) -> DECLINE
        """
        cutoff = retail_pricing_config.default_cutoff_pd
        if pd_score <= cutoff * 0.5:
            return "Tier A", "APPROVE"
        elif pd_score <= cutoff:
            return "Tier B", "APPROVE"
        elif pd_score <= cutoff * 1.5:
            return "Tier C", "WAITING / COMMITTEE REVIEW"
        else:
            return "Tier D", "DECLINE"

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
            "raw_value": df_clean[self.features].iloc[0].values
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

    def predict_batch_pd(self, df_input: pd.DataFrame) -> List[Dict[str, Any]]:
        """Tính toán nhanh xác suất vỡ nợ (PD) theo lô cho bảng Client Registry."""
        if df_input.empty:
            return []
        df_clean = self._align_and_cast_features(df_input)
        lgb_preds = [model.predict_proba(df_clean)[:, 1] for model in self.lgb_models]
        mean_lgb = np.mean(lgb_preds, axis=0)
        xgb_preds = [model.predict_proba(df_clean)[:, 1] for model in self.xgb_models]
        mean_xgb = np.mean(xgb_preds, axis=0)
        w_lgb = self.blend_weights.get("lightgbm", 0.5)
        w_xgb = self.blend_weights.get("xgboost", 0.5)
        final_pds = (mean_lgb * w_lgb) + (mean_xgb * w_xgb)

        results = []
        for pd_val in final_pds:
            tier, decision = self._determine_credit_tier(float(pd_val))
            pct = round(float(pd_val) * 100, 1)
            results.append({
                "pd_val": float(pd_val),
                "pd_display": f"{pct:.1f}%",
                "tier": tier,
                "decision": decision,
            })
        return results

    def predict_pd_fast(self, client_series: pd.Series) -> Tuple[float, str, str]:
        """Tính toán nhanh xác suất vỡ nợ (PD), Rating Tier và Policy Decision cho 1 hồ sơ (bỏ qua SHAP) phục vụ Terms Simulator."""
        df_row = pd.DataFrame([client_series])
        df_clean = self._align_and_cast_features(df_row)
        lgb_preds = [model.predict_proba(df_clean)[:, 1][0] for model in self.lgb_models]
        mean_lgb = float(np.mean(lgb_preds))
        xgb_preds = [model.predict_proba(df_clean)[:, 1][0] for model in self.xgb_models]
        mean_xgb = float(np.mean(xgb_preds))
        w_lgb = self.blend_weights.get("lightgbm", 0.5)
        w_xgb = self.blend_weights.get("xgboost", 0.5)
        final_pd = float((mean_lgb * w_lgb) + (mean_xgb * w_xgb))
        tier, decision = self._determine_credit_tier(final_pd)
        return final_pd, tier, decision

    def cache_client_features(self, client_series: pd.Series, client_id: Optional[str] = None):
        """Tiền xử lý và lưu cache 891 features đã align cho client được chọn (luôn reset index về 0)."""
        df_row = pd.DataFrame([client_series]).reset_index(drop=True)
        self._cached_clean_df = self._align_and_cast_features(df_row).reset_index(drop=True)
        cid = client_id or str(client_series.get("SK_ID_CURR", client_series.get("ID", "")))
        self._cached_client_id = str(cid) if cid else None

    def predict_pd_from_cache(
        self,
        credit: float,
        annuity: float,
        income: float,
        use_fast_lgb: bool = False,
    ) -> Tuple[Optional[float], str, str]:
        """Dự đoán siêu tốc (<20ms) bằng cách ghi đè trực tiếp các đòn bẩy tài chính lên DataFrame đã cache."""
        if getattr(self, "_cached_clean_df", None) is None:
            return None, "None", "None"

        try:
            df_c = self._cached_clean_df.copy()
            target_idx = df_c.index[0]
            eps = 1e-6
            df_c.loc[target_idx, "AMT_CREDIT"] = float(credit)
            df_c.loc[target_idx, "AMT_ANNUITY"] = float(annuity)
            df_c.loc[target_idx, "AMT_INCOME_TOTAL"] = float(income)
            df_c.loc[target_idx, "CREDIT_TO_INCOME"] = float(credit) / (float(income) + eps)
            df_c.loc[target_idx, "ANNUITY_TO_INCOME"] = float(annuity) / (float(income) + eps)
            df_c.loc[target_idx, "CREDIT_TO_ANNUITY"] = float(credit) / (float(annuity) + eps)

            if "AMT_GOODS_PRICE" in df_c.columns and pd.notna(df_c.loc[target_idx, "AMT_GOODS_PRICE"]):
                gp = float(df_c.loc[target_idx, "AMT_GOODS_PRICE"])
                df_c.loc[target_idx, "CREDIT_TO_GOODS_RATIO"] = float(credit) / (gp + eps)
                df_c.loc[target_idx, "GOODS_CREDIT_DIFF"] = gp - float(credit)
                df_c.loc[target_idx, "ANNUITY_TO_GOODS_RATIO"] = float(annuity) / (gp + eps)

            if "EMPLOYED_YEARS" in df_c.columns and pd.notna(df_c.loc[target_idx, "EMPLOYED_YEARS"]):
                try:
                    emp_yrs = float(df_c.loc[target_idx, "EMPLOYED_YEARS"])
                    if emp_yrs > 0:
                        df_c.loc[target_idx, "INCOME_PER_EMPLOYED_YEAR"] = float(income) / (emp_yrs + eps)
                except (ValueError, TypeError):
                    pass

            if use_fast_lgb:
                lgb_preds = [m.predict_proba(df_c)[:, 1][0] for m in self.lgb_models]
                final_pd = float(np.mean(lgb_preds))
            else:
                lgb_preds = [m.predict_proba(df_c)[:, 1][0] for m in self.lgb_models]
                xgb_preds = [m.predict_proba(df_c)[:, 1][0] for m in self.xgb_models]
                w_lgb = self.blend_weights.get("lightgbm", 0.5)
                w_xgb = self.blend_weights.get("xgboost", 0.5)
                final_pd = float((np.mean(lgb_preds) * w_lgb) + (np.mean(xgb_preds) * w_xgb))

            if np.isnan(final_pd) or final_pd <= 0.0001:
                return None, "None", "None"

            tier, decision = self._determine_credit_tier(final_pd)
            return final_pd, tier, decision
        except Exception as e:
            print(f"[predict_pd_from_cache] Error: {e}")
            return None, "None", "None"


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