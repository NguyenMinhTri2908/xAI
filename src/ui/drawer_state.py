import reflex as rx
from typing import Dict, Any


class FeatureDrawerState(rx.State):
    """State điều khiển Slide-over Feature Detail Drawer."""
    is_open: bool = False
    selected_feature: Dict[str, Any] = {}

    def open_feature(self, feature_data: Dict[str, Any]):
        """Nạp dữ liệu feature và mở drawer."""
        self.selected_feature = feature_data
        self.is_open = True

    def close_drawer(self):
        """Đóng drawer."""
        self.is_open = False

    @rx.var
    def shap_impact_color(self) -> str:
        """Màu xanh nếu giảm PD (favorable), màu đỏ nếu tăng PD (adverse)."""
        raw_val = str(self.selected_feature.get("shap_value", "0"))
        if raw_val.startswith("-") or "Reduces" in raw_val or "decrease" in raw_val.lower():
            return "#10B981"  # Xanh ngọc
        return "#EF4444"      # Đỏ

    @rx.var
    def shap_direction_label(self) -> str:
        """Nhãn nghiệp vụ giải thích hướng tác động của SHAP."""
        raw_val = str(self.selected_feature.get("shap_value", "0"))
        if raw_val.startswith("-") or "Reduces" in raw_val:
            return "Reduces Risk (Favorable)"
        return "Increases Risk (Adverse)"