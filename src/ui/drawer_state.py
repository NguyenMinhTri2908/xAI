import os
import json
import reflex as rx
import pandas as pd
from typing import Dict, Any

FEATURE_DICT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "models", "feature_dictionary.json")
)
FEATURE_METADATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "models", "feature_metadata.json")
)

_CACHED_FEATURE_DICT: Dict[str, Dict[str, str]] = {}
_CACHED_CATEGORICAL_MAPPINGS: Dict[str, Any] = {}


def _get_feature_dict() -> Dict[str, Dict[str, str]]:
    global _CACHED_FEATURE_DICT
    if not _CACHED_FEATURE_DICT and os.path.exists(FEATURE_DICT_PATH):
        try:
            with open(FEATURE_DICT_PATH, "r", encoding="utf-8") as f:
                _CACHED_FEATURE_DICT = json.load(f)
        except Exception as e:
            print(f"[FeatureDrawerState] Error loading {FEATURE_DICT_PATH}: {e}")
    return _CACHED_FEATURE_DICT


def _get_categorical_mappings() -> Dict[str, Any]:
    global _CACHED_CATEGORICAL_MAPPINGS
    if not _CACHED_CATEGORICAL_MAPPINGS and os.path.exists(FEATURE_METADATA_PATH):
        try:
            with open(FEATURE_METADATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                _CACHED_CATEGORICAL_MAPPINGS = meta.get("categorical_mappings", {})
        except Exception as e:
            print(f"[FeatureDrawerState] Error loading {FEATURE_METADATA_PATH}: {e}")
    return _CACHED_CATEGORICAL_MAPPINGS


class FeatureDrawerState(rx.State):
    """State điều khiển Drawer chi tiết feature chuẩn Notion-style."""
    is_open: bool = False
    selected_feature: Dict[str, Any] = {}

    # Explicit base state vars for 100% reliable reactive websocket synchronization
    feature_title: str = "N/A"
    origin_table: str = "application"
    description: str = "No underwriting documentation recorded for this metric."
    client_value: str = "N/A"
    shap_direction_label: str = "Neutral Impact Baseline"
    shap_display_text: str = "0.0000"
    display_shap_value: str = "0.0000"
    shap_impact_color: str = "#9CA3AF"

    async def select_feature(
        self,
        feature_name: Any = None,
        feature_data: Any = None,
        feature_ref: Any = None,
        **kwargs
    ):
        """
        Chuẩn hóa logic mở Drawer:
        - Tự động lookup feature_name từ feature_dictionary.json
        - Tự động lấp đầy: origin_table, description, shap_impact, impact_direction, client_value
        - Kích hoạt is_open = True
        """
        feat_input = (
            feature_name
            if feature_name is not None
            else (feature_data if feature_data is not None else feature_ref)
        )
        if feat_input is None and kwargs:
            # Ignore standard DOM MouseEvent keys
            mouse_keys = {"_e", "event", "clientX", "clientY", "pageX", "pageY", "screenX", "screenY", "target", "currentTarget"}
            for k, v in kwargs.items():
                if k not in mouse_keys:
                    feat_input = v
                    break

        if feat_input is None:
            return

        # Bỏ qua nếu đối tượng truyền vào là DOM MouseEvent
        if isinstance(feat_input, dict):
            if any(k in feat_input for k in ["clientX", "clientY", "pageX", "pageY", "screenX", "screenY"]):
                return

        passed_shap = None
        passed_val = None
        passed_table = None
        passed_desc = None

        if isinstance(feat_input, dict):
            feat_str = str(
                feat_input.get("feature") or
                feat_input.get("name") or
                feat_input.get("feature_name") or
                feat_input.get("key") or
                ""
            ).strip().strip('"').strip("'")
            passed_shap = feat_input.get("shap_value", None)
            passed_val = feat_input.get("display_value", feat_input.get("raw_value", None))
            passed_table = feat_input.get("origin_table") or feat_input.get("table", None)
            passed_desc = feat_input.get("description", None)
        else:
            feat_str = str(feat_input).strip().strip('"').strip("'")

        if not feat_str:
            return

        # 1. Lookup metadata từ feature_dictionary.json (hỗ trợ case-insensitive)
        fdict = _get_feature_dict()
        meta = fdict.get(feat_str) or fdict.get(feat_str.upper()) or {}
        origin_table = passed_table or meta.get("table") or meta.get("origin_table") or "application"
        description = passed_desc or meta.get("description", "")
        if not description or description.strip() == "":
            description = f"Model underwriting feature for credit risk scoring (Table: {origin_table})."

        # 2. Truy cập UnderwritingState an toàn (bảo vệ bằng try...except)
        u_state = None
        try:
            from src.ui.state import UnderwritingState
            u_state = await self.get_state(UnderwritingState)
        except Exception as e:
            print(f"[FeatureDrawerState] Could not get UnderwritingState: {e}")

        # 3. Tính toán SHAP value
        shap_num = 0.0
        if passed_shap is not None:
            try:
                shap_num = float(passed_shap)
            except (ValueError, TypeError):
                shap_num = 0.0
        elif u_state is not None:
            if u_state.current_client_shap and feat_str in u_state.current_client_shap:
                shap_num = float(u_state.current_client_shap[feat_str])
            elif u_state.current_client_shap and feat_str.upper() in u_state.current_client_shap:
                shap_num = float(u_state.current_client_shap[feat_str.upper()])
            else:
                for factor in (u_state.top_risk_factors or []):
                    if factor.get("feature") in [feat_str, feat_str.upper()]:
                        shap_num = float(factor.get("shap_value", 0.0))
                        if passed_val is None:
                            passed_val = factor.get("display_value")
                        break
                if shap_num == 0.0:
                    for factor in (u_state.top_positive_factors or []):
                        if factor.get("feature") in [feat_str, feat_str.upper()]:
                            shap_num = float(factor.get("shap_value", 0.0))
                            if passed_val is None:
                                passed_val = factor.get("display_value")
                            break

        # 4. Trích xuất Client Value thực tế
        client_val_str = "N/A"
        if passed_val is not None and str(passed_val).strip() not in ["", "Portfolio Active", "Active", "None"]:
            client_val_str = str(passed_val)
        elif u_state is not None:
            for factor in (u_state.top_risk_factors or []) + (u_state.top_positive_factors or []):
                if factor.get("feature") in [feat_str, feat_str.upper()] and factor.get("display_value"):
                    val_str = str(factor.get("display_value"))
                    if val_str not in ["", "Portfolio Active", "Active", "None"]:
                        client_val_str = val_str
                        break

            if client_val_str == "N/A":
                try:
                    client_id = u_state.selected_client_id
                    if client_id:
                        from src.data_processing.ingestion_service import get_client_row_data
                        row = get_client_row_data(client_id)
                        if row is not None:
                            val = row.get(feat_str) if feat_str in row else row.get(feat_str.upper())
                            if pd.notna(val) and val is not None:
                                cat_mappings = _get_categorical_mappings()
                                key_cat = feat_str if feat_str in cat_mappings else feat_str.upper()
                                if key_cat in cat_mappings:
                                    val_code = str(int(val)) if isinstance(val, (int, float)) and not pd.isna(val) else str(val)
                                    client_val_str = cat_mappings[key_cat].get("code_to_label", {}).get(val_code, str(val))
                                else:
                                    try:
                                        fval = float(val)
                                        if fval.is_integer():
                                            client_val_str = f"{int(fval):,}"
                                        else:
                                            client_val_str = f"{fval:,.4f}".rstrip("0").rstrip(".")
                                    except (ValueError, TypeError):
                                        client_val_str = str(val)
                except Exception as e:
                    print(f"[FeatureDrawerState] Error extracting client value: {e}")

        # 5. Xác định hướng tác động & chuỗi hiển thị SHAP
        if shap_num < 0:
            impact_dir = "Reduces Default Risk (Favorable)"
            shap_text = f"{shap_num:.4f}"
            shap_color = "#10B981"
        elif shap_num > 0:
            impact_dir = "Increases Default Risk (Adverse)"
            shap_text = f"+{shap_num:.4f}"
            shap_color = "#EF4444"
        else:
            impact_dir = "Neutral Impact Baseline"
            shap_text = "0.0000"
            shap_color = "#9CA3AF"

        # 6. Gán cả Explicit State Vars và Dictionary 100% đồng bộ
        self.feature_title = feat_str
        self.origin_table = origin_table
        self.description = description
        self.client_value = client_val_str
        self.shap_direction_label = impact_dir
        self.shap_display_text = shap_text
        self.display_shap_value = shap_text
        self.shap_impact_color = shap_color

        self.selected_feature = {
            "feature": feat_str,
            "name": feat_str,
            "table": origin_table,
            "origin_table": origin_table,
            "description": description,
            "shap_value": shap_num,
            "shap_impact": shap_text,
            "impact_direction": impact_dir,
            "client_value": client_val_str,
            "display_value": client_val_str,
            "raw_value": client_val_str,
        }
        self.is_open = True

    async def open_feature(
        self,
        feature_data: Any = None,
        feature_name: Any = None,
        feature_ref: Any = None,
        **kwargs
    ):
        """Bảo đảm tương thích ngược tuyệt đối với mọi nguồn gọi open_feature."""
        return await self.select_feature(
            feature_name=feature_name,
            feature_data=feature_data,
            feature_ref=feature_ref,
            **kwargs
        )

    def close_drawer(self):
        self.is_open = False