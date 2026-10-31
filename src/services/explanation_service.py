"""
DOMAIN SERVICE: MODEL EXPLANATION & SHAP VISUALIZATION
======================================================
Cung cấp các hàm thuần túy (Pure Functions) xử lý kết quả SHAP Values từ mô hình:
- Trích xuất bảng tra cứu SHAP toàn diện (SHAP lookup dictionary)
- Tính toán tỉ lệ thanh bar tương đối (Normalized relative bar width)
- Phân tách yếu tố rủi ro (Risk factors) và yếu tố tích cực (Positive trust factors)
Không phụ thuộc vào Reflex State hoặc WebSocket context.
"""

import os
import json
from typing import Dict, List, Any, Tuple
from src.config import FEATURE_DICT_PATH, FEATURE_METADATA_PATH

_SHARED_FEATURE_DICT_CACHE: Dict[str, Dict[str, str]] = {}
_SHARED_CATEGORICAL_MAPPINGS_CACHE: Dict[str, Any] = {}


def get_cached_feature_dictionary() -> Dict[str, Dict[str, str]]:
    """Đọc và lưu bộ nhớ đệm duy nhất (Singleton Cache) cho feature_dictionary.json (891+ features)."""
    global _SHARED_FEATURE_DICT_CACHE
    if not _SHARED_FEATURE_DICT_CACHE and os.path.exists(FEATURE_DICT_PATH):
        try:
            with open(FEATURE_DICT_PATH, "r", encoding="utf-8") as f:
                _SHARED_FEATURE_DICT_CACHE = json.load(f)
        except Exception as e:
            print(f"[ExplanationService] Error loading {FEATURE_DICT_PATH}: {e}")
    return _SHARED_FEATURE_DICT_CACHE


def get_cached_categorical_mappings() -> Dict[str, Any]:
    """Đọc và lưu bộ nhớ đệm duy nhất cho bảng ánh xạ biến phân loại (categorical_mappings)."""
    global _SHARED_CATEGORICAL_MAPPINGS_CACHE
    if not _SHARED_CATEGORICAL_MAPPINGS_CACHE and os.path.exists(FEATURE_METADATA_PATH):
        try:
            with open(FEATURE_METADATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                _SHARED_CATEGORICAL_MAPPINGS_CACHE = meta.get("categorical_mappings", {})
        except Exception as e:
            print(f"[ExplanationService] Error loading {FEATURE_METADATA_PATH}: {e}")
    return _SHARED_CATEGORICAL_MAPPINGS_CACHE


def process_shap_explanations(
    model_result: Dict[str, Any],
    min_bar_pct: float = 6.0,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, float]]:
    """
    Xử lý và chuẩn hóa các giá trị SHAP từ kết quả suy luận của mô hình.

    Parameters:
        model_result: Dict chứa 'top_risk_factors', 'top_positive_factors', và tùy chọn 'all_shap_values'.
        min_bar_pct: Phần trăm tối thiểu của thanh bar hiển thị (để tránh thanh quá ngắn trên UI).

    Returns:
        Tuple gồm:
        - top_risks: Danh sách các yếu tố rủi ro đã được tính toán 'bar_width'
        - top_positives: Danh sách các yếu tố tích cực đã được tính toán 'bar_width'
        - shap_lookup: Dictionary map tên feature -> giá trị SHAP làm tròn 4 chữ số thập phân
    """
    raw_risks = [dict(item) for item in model_result.get("top_risk_factors", [])]
    raw_positives = [dict(item) for item in model_result.get("top_positive_factors", [])]

    shap_lookup: Dict[str, float] = {}
    if "all_shap_values" in model_result and isinstance(model_result["all_shap_values"], dict):
        shap_lookup = {
            str(k): round(float(v), 4)
            for k, v in model_result["all_shap_values"].items()
        }
    else:
        for item in raw_risks:
            feat = item.get("feature")
            if feat:
                shap_lookup[str(feat)] = round(float(item.get("shap_value", 0.0)), 4)
        for item in raw_positives:
            feat = item.get("feature")
            if feat:
                shap_lookup[str(feat)] = round(float(item.get("shap_value", 0.0)), 4)

    # Tính toán bar_width tỉ lệ chuẩn hóa cho nhóm rủi ro (top risks)
    if raw_risks:
        max_risk = max([abs(float(f.get("shap_value", 0.0))) for f in raw_risks]) or 1.0
        for f in raw_risks:
            val = abs(float(f.get("shap_value", 0.0)))
            pct = round((val / max_risk) * 100.0, 1)
            f["bar_width"] = f"{max(pct, min_bar_pct)}%"

    # Tính toán bar_width tỉ lệ chuẩn hóa cho nhóm tích cực (top positives)
    if raw_positives:
        max_trust = max([abs(float(f.get("shap_value", 0.0))) for f in raw_positives]) or 1.0
        for f in raw_positives:
            val = abs(float(f.get("shap_value", 0.0)))
            pct = round((val / max_trust) * 100.0, 1)
            f["bar_width"] = f"{max(pct, min_bar_pct)}%"

    return raw_risks, raw_positives, shap_lookup

