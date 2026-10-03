import os
import json
import reflex as rx
from typing import Dict, List, Any
from src.config import BASE_DIR

FEATURE_DICT_PATH = os.path.join(BASE_DIR, "src/models/feature_dictionary.json")


class FeatureSearchState(rx.State):
    """Manages feature dictionary search, impact filtering, and real-time SHAP binding."""

    raw_feature_dict: Dict[str, Dict[str, str]] = {}
    client_shap: Dict[str, float] = {}
    search_query: str = ""
    selected_table: str = "All"
    selected_impact: str = "All"
    display_limit: int = 20

    async def load_feature_dictionary(self):
        """Loads feature dictionary from disk and immediately syncs current client's SHAP values."""
        if os.path.exists(FEATURE_DICT_PATH):
            with open(FEATURE_DICT_PATH, "r", encoding="utf-8") as f:
                self.raw_feature_dict = json.load(f)
        else:
            self.raw_feature_dict = {}

        # Import cục bộ tại đây để phá vỡ circular import
        from .state import UnderwritingState

        underwriting_state = await self.get_state(UnderwritingState)
        if underwriting_state.current_client_shap:
            self.client_shap = underwriting_state.current_client_shap

    def update_client_shap(self, shap_dict: Dict[str, float]):
        """Handler to receive live SHAP contributions from UnderwritingState on client switch."""
        self.client_shap = shap_dict

    @rx.var
    def available_tables(self) -> List[str]:
        tables = sorted(list({v.get("table", "Unknown") for v in self.raw_feature_dict.values()}))
        return ["All"] + tables

    @rx.var
    def available_impacts(self) -> List[str]:
        return ["All", "Increases Risk (+)", "Reduces Risk (-)"]

    @rx.var
    def filtered_features(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        query = self.search_query.strip().lower()

        for feat_name, meta in self.raw_feature_dict.items():
            tbl = meta.get("table", "Unknown")
            desc = meta.get("description", "")
            shap_val = float(self.client_shap.get(feat_name, 0.0))

            # 1. Lọc theo bảng
            if self.selected_table != "All" and tbl != self.selected_table:
                continue

            # 2. Lọc theo tác động SHAP (Dương / Âm)
            if self.selected_impact == "Increases Risk (+)" and shap_val <= 0:
                continue
            if self.selected_impact == "Reduces Risk (-)" and shap_val >= 0:
                continue

            # 3. Lọc theo từ khóa tìm kiếm
            if query:
                if query not in feat_name.lower() and query not in desc.lower():
                    continue

            # Gán nhãn và màu sắc
            if shap_val > 0:
                impact_text = f"+{shap_val:.4f}"
                impact_color = "red"
                impact_type = "RISK"
            elif shap_val < 0:
                impact_text = f"{shap_val:.4f}"
                impact_color = "green"
                impact_type = "TRUST"
            else:
                impact_text = "0.0000"
                impact_color = "gray"
                impact_type = "NEUTRAL"

            results.append({
                "name": feat_name,
                "table": tbl,
                "description": desc,
                "shap_value": shap_val,
                "impact_text": impact_text,
                "impact_color": impact_color,
                "impact_type": impact_type,
            })

        # Sắp xếp ưu tiên độ lớn tác động (tuyệt đối) giảm dần
        results.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        # Giới hạn số lượng nếu không gõ search để bảng load mượt
        if not query and self.selected_table == "All" and self.selected_impact == "All":
            return results[:self.display_limit]

        return results

    @rx.var
    def total_matches(self) -> int:
        return len(self.filtered_features)

    def set_search_query(self, query: str):
        self.search_query = query

    def set_selected_table(self, table: str):
        self.selected_table = table

    def set_selected_impact(self, impact: str):
        self.selected_impact = impact

    def load_more(self):
        self.display_limit += 20