import os
import json
import reflex as rx
from typing import Dict, List, Any
from src.config import BASE_DIR

FEATURE_DICT_PATH = os.path.join(BASE_DIR, "src/models/feature_dictionary.json")

# Nhãn mặc định chuẩn tiếng Anh nghiệp vụ
DEFAULT_SOURCE_LABEL = "All Data Sources"
DEFAULT_IMPACT_LABEL = "All Impact Directions"


class FeatureSearchState(rx.State):
    """Manages feature search, data source filtering, and real-time SHAP attribution."""

    raw_feature_dict: Dict[str, Dict[str, str]] = {}
    client_shap: Dict[str, float] = {}
    search_query: str = ""
    selected_source: str = DEFAULT_SOURCE_LABEL
    selected_impact: str = DEFAULT_IMPACT_LABEL
    display_limit: int = 25

    async def load_feature_dictionary(self):
        """Loads feature dictionary from disk and syncs client SHAP values."""
        if os.path.exists(FEATURE_DICT_PATH):
            with open(FEATURE_DICT_PATH, "r", encoding="utf-8") as f:
                self.raw_feature_dict = json.load(f)
        else:
            self.raw_feature_dict = {}

        # Import cục bộ để tránh circular import giữa state.py và feature_search_state.py
        from .state import UnderwritingState

        underwriting_state = await self.get_state(UnderwritingState)
        if underwriting_state.current_client_shap:
            self.client_shap = underwriting_state.current_client_shap

    def update_client_shap(self, shap_dict: Dict[str, float]):
        """Event handler to receive live SHAP contributions from UnderwritingState."""
        self.client_shap = shap_dict

    @rx.var
    def available_sources(self) -> List[str]:
        """Returns unique list of raw tables/data sources."""
        sources = sorted(list({v.get("table", "Unknown") for v in self.raw_feature_dict.values()}))
        return [DEFAULT_SOURCE_LABEL] + sources

    @rx.var
    def available_impacts(self) -> List[str]:
        """Dropdown options for risk impact direction."""
        return [
            DEFAULT_IMPACT_LABEL,
            "+ Increases Risk (Elevates PD)",
            "- Reduces Risk (Lowers PD)",
        ]

    @rx.var
    def filtered_features(self) -> List[Dict[str, Any]]:
        """Filters 891 features by keyword, data source, and SHAP direction."""
        results: List[Dict[str, Any]] = []
        query = self.search_query.strip().lower()

        for feat_name, meta in self.raw_feature_dict.items():
            tbl = meta.get("table", "Unknown")
            desc = meta.get("description", "")
            shap_val = float(self.client_shap.get(feat_name, 0.0))

            # 1. Lọc theo nguồn dữ liệu (Data Source)
            if self.selected_source != DEFAULT_SOURCE_LABEL and tbl != self.selected_source:
                continue

            # 2. Lọc theo hướng tác động SHAP (Impact Direction)
            if "+ Increases Risk" in self.selected_impact and shap_val <= 0:
                continue
            if "- Reduces Risk" in self.selected_impact and shap_val >= 0:
                continue

            # 3. Lọc theo từ khóa tìm kiếm
            if query:
                if query not in feat_name.lower() and query not in desc.lower():
                    continue

            # Định dạng nhãn và màu sắc
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

        # Nếu người dùng đang tìm kiếm hoặc lọc cụ thể -> Trả về toàn bộ kết quả khớp
        is_filtering = (
            query != ""
            or self.selected_source != DEFAULT_SOURCE_LABEL
            or self.selected_impact != DEFAULT_IMPACT_LABEL
        )

        if not is_filtering:
            return results[:self.display_limit]

        return results

    def set_search_query(self, query: str):
        self.search_query = query

    def set_selected_source(self, source: str):
        self.selected_source = source

    def set_selected_impact(self, impact: str):
        self.selected_impact = impact

    def load_more_on_scroll(self):
        """Tự động tải thêm 25 bản ghi khi người dùng cuộn chuột tới đáy bảng."""
        self.display_limit += 25