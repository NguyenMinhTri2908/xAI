import reflex as rx
from typing import Dict, Any

class FeatureDrawerState(rx.State):
    """State điều khiển Drawer chi tiết feature."""
    is_open: bool = False
    selected_feature: Dict[str, Any] = {}

    def open_feature(self, feature_data: Dict[str, Any]):
        """Kích hoạt mở drawer và nạp dữ liệu của feature được click."""
        self.selected_feature = feature_data
        self.is_open = True

    def close_drawer(self):
        self.is_open = False