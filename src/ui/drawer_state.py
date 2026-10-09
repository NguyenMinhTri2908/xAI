import reflex as rx
from typing import Dict, Any
from .utils.formatters import format_shap_value


class FeatureDrawerState(rx.State):
    """State điều khiển Drawer chi tiết feature."""
    is_open: bool = False
    selected_feature: Dict[str, Any] = {}

    def open_feature(self, feature_data: Dict[str, Any]):
        """Kích hoạt mở drawer và nạp dữ liệu feature an toàn với metadata fallback."""
        data = dict(feature_data) if feature_data else {}
        feat_name = data.get("feature") or data.get("name", "")
        if feat_name:
            data["feature"] = feat_name
            # Tự động nạp table và description từ từ điển cache nếu thiếu
            try:
                from .feature_search_state import _CACHED_RAW_FEATURE_DICT
                if feat_name in _CACHED_RAW_FEATURE_DICT:
                    meta = _CACHED_RAW_FEATURE_DICT[feat_name]
                    if not data.get("table") or data.get("table") in ("None", "Unknown"):
                        data["table"] = meta.get("table", "application")
                    if not data.get("description") or data.get("description") in ("None", ""):
                        data["description"] = meta.get("description", "")
            except Exception:
                pass

        self.selected_feature = data
        self.is_open = True

    def close_drawer(self):
        self.is_open = False

    @rx.var
    def shap_formatted(self) -> Dict[str, str]:
        """Trả về dictionary định dạng SHAP thống nhất qua format_shap_value."""
        raw_val = self.selected_feature.get("shap_value", 0.0)
        return format_shap_value(raw_val)

    @rx.var
    def shap_impact_color(self) -> str:
        """Trả về màu hex: đỏ nếu tăng rủi ro, xanh lá nếu giảm rủi ro, xám nếu trung tính."""
        color = self.shap_formatted.get("color", "gray")
        if color == "green":
            return "#10B981"
        elif color == "red":
            return "#EF4444"
        return "#94A3B8"

    @rx.var
    def shap_color_scheme(self) -> str:
        """Trả về color scheme cho Reflex badge: green, red, gray."""
        return self.shap_formatted.get("color", "gray")

    @rx.var
    def shap_impact_type(self) -> str:
        """Trả về RISK, TRUST, hoặc NEUTRAL."""
        return self.shap_formatted.get("type", "NEUTRAL")

    @rx.var
    def shap_display_text(self) -> str:
        """Chuỗi hiển thị SHAP định dạng thống nhất: ví dụ +0.1234."""
        return self.shap_formatted.get("text", "0.0000")

    @rx.var
    def shap_direction_label(self) -> str:
        """Nhãn phụ giải thích hướng tác động chuẩn nghiệp vụ."""
        stype = self.shap_impact_type
        if stype == "RISK":
            return "Increases Default Risk (Adverse)"
        elif stype == "TRUST":
            return "Reduces Default Risk (Favorable)"
        return "Neutral Baseline (No Impact)"

    @rx.var
    def feature_name(self) -> str:
        return str(self.selected_feature.get("feature") or self.selected_feature.get("name") or "N/A")

    @rx.var
    def feature_table(self) -> str:
        return str(self.selected_feature.get("table", "Unknown"))

    @rx.var
    def feature_raw_value(self) -> str:
        val = self.selected_feature.get("raw_value")
        if val is not None and str(val) != "" and str(val) != "None":
            return str(val)
        disp = self.selected_feature.get("display_value")
        if disp is not None and str(disp) != "" and str(disp) != "None":
            return str(disp)
        return "N/A"

    @rx.var
    def feature_display_value(self) -> str:
        disp = self.selected_feature.get("display_value")
        if disp is not None and str(disp) != "" and str(disp) != "None":
            return str(disp)
        val = self.selected_feature.get("raw_value")
        if val is not None and str(val) != "" and str(val) != "None":
            return str(val)
        return "N/A"

    @rx.var
    def feature_description(self) -> str:
        desc = self.selected_feature.get("description")
        if desc and str(desc) not in ("None", ""):
            return str(desc)
        return "No underwriting documentation available for this feature."