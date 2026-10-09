import reflex as rx
from typing import Dict, Any


class FeatureDrawerState(rx.State):
    """State điều khiển Drawer chi tiết feature."""
    is_open: bool = False
    selected_feature: Dict[str, Any] = {}

    def open_feature(self, feature_data: Dict[str, Any]):
        """Kích hoạt mở drawer và nạp dữ liệu feature."""
        self.selected_feature = feature_data
        self.is_open = True

    def close_drawer(self):
        self.is_open = False

    @rx.var
    def shap_impact_color(self) -> str:
        """Trả về màu xanh nếu giảm rủi ro, đỏ nếu tăng rủi ro."""
        raw_val = str(self.selected_feature.get("shap_value", "0"))
        # Nếu bắt đầu bằng dấu trừ hoặc chứa từ khóa giảm
        if raw_val.startswith("-") or "Reduces" in raw_val or "decrease" in raw_val.lower():
            return "#10B981"  # Xanh lá
        return "#EF4444"      # Đỏ

    @rx.var
    def shap_direction_label(self) -> str:
        """Nhãn phụ giải thích hướng tác động."""
        raw_val = str(self.selected_feature.get("shap_value", "0"))
        if raw_val.startswith("-") or "Reduces" in raw_val:
            return "Reduces Default Risk (Favorable)"
        return "Increases Default Risk (Adverse)"