import os
import json
import reflex as rx
from typing import Dict, List, Any
from .utils.formatters import format_shap_value

FEATURE_DICT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "models", "feature_dictionary.json")
)


def _load_cached_feature_dict() -> Dict[str, Dict[str, str]]:
    """Tải và lưu trữ bộ nhớ đệm từ điển feature ngay khi nạp module."""
    if os.path.exists(FEATURE_DICT_PATH):
        try:
            with open(FEATURE_DICT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[FeatureSearchState] Error reading {FEATURE_DICT_PATH}: {e}")
            return {}
    return {}


# Cache từ điển feature toàn diện (891+ features) khi nạp module
_CACHED_RAW_FEATURE_DICT: Dict[str, Dict[str, str]] = _load_cached_feature_dict()

# Nhãn mặc định chuẩn tiếng Anh nghiệp vụ
DEFAULT_SOURCE_LABEL = "All Data Sources"
DEFAULT_IMPACT_LABEL = "All Impact Directions"


class FeatureSearchState(rx.State):
    """Manages feature search, data source filtering, and real-time SHAP attribution."""

    raw_feature_dict: Dict[str, Dict[str, str]] = _CACHED_RAW_FEATURE_DICT
    client_shap: Dict[str, float] = {}
    search_query: str = ""
    selected_source: str = DEFAULT_SOURCE_LABEL
    selected_impact: str = DEFAULT_IMPACT_LABEL
    display_limit: int = 25

    def _ensure_dict_loaded(self):
        """Hàm trợ giúp nội bộ: Đảm bảo metadata luôn được nạp nếu chưa có trong RAM."""
        if not self.raw_feature_dict:
            self.raw_feature_dict = _CACHED_RAW_FEATURE_DICT or _load_cached_feature_dict()

    async def load_feature_dictionary(self):
        """Loads feature dictionary from disk and syncs client SHAP values."""
        self._ensure_dict_loaded()

        # Import cục bộ để tránh circular import giữa state.py và feature_search_state.py
        from .state import UnderwritingState

        underwriting_state = await self.get_state(UnderwritingState)
        if underwriting_state.current_client_shap:
            self.client_shap = underwriting_state.current_client_shap

    def update_client_shap(self, shap_dict: Dict[str, float]):
        """Event handler nhận SHAP đồng thời tự động nạp từ điển nếu chưa có."""
        self.client_shap = shap_dict
        # Tự động nạp dữ liệu metadata ngay khi hồ sơ khách hàng được chọn
        self._ensure_dict_loaded()

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

            # Định dạng nhãn và màu sắc thống nhất qua format_shap_value
            shap_info = format_shap_value(shap_val)

            results.append({
                "name": feat_name,
                "table": tbl,
                "description": desc,
                "shap_value": shap_val,
                "impact_text": shap_info["text"],
                "impact_color": shap_info["color"],
                "impact_type": shap_info["type"],
            })

        # Sắp xếp ưu tiên độ lớn tác động (tuyệt đối) giảm dần
        results.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

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