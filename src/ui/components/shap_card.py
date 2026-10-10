import reflex as rx
from src.ui.state import UnderwritingState
from src.ui.drawer_state import FeatureDrawerState

def risk_driver_row(factor: dict) -> rx.Component:
    """Hàng yếu tố làm tăng rủi ro (Đỏ) có Hover sáng hàng + Tooltip chuỗi hợp lệ."""
    row_content = rx.hstack(
        # Cột 1: Feature & value
        rx.hstack(
            rx.text(factor["feature"], font_family="monospace", font_size="13px", color="#E5E7EB", weight="medium"),
            rx.text("=", font_family="monospace", font_size="13px", color="#9CA3AF"),
            rx.text(factor["display_value"].to_string(), font_family="monospace", font_size="13px", color="#FFFFFF", weight="bold"),
            spacing="2",
            width="35%",
            overflow="hidden",
            white_space="nowrap",
        ),
        # Cột 2: Khung bên trái chứa nhãn số và thanh bar đỏ
        rx.hstack(
            rx.text(
                "+" + factor["shap_value"].to_string()[:6],
                font_family="monospace",
                font_size="12px",
                color="#F87171",
                font_weight="bold",
                margin_right="8px",
            ),
            rx.box(
                rx.box(
                    height="18px",
                    width=factor["bar_width"],
                    background="#EF4444",
                    border_radius="4px 0 0 4px",
                    transition="all 0.2s ease-in-out",
                ),
                width="180px",
                display="flex",
                justify_content="flex-end",
            ),
            width="32.5%",
            justify="end",
            align="center",
        ),
        # Trục trung tâm (Baseline)
        rx.box(width="1px", height="24px", background="#374151"),
        # Cột 3: Vùng trống bên phải
        rx.box(width="32.5%"),
        width="100%",
        align="center",
        padding_x="3",
        padding_y="1.5",
        border_radius="6px",
        cursor="pointer",
        _hover={
            "background": "rgba(255, 255, 255, 0.06)",
        },
        transition="background 0.15s ease",
        on_click=lambda: FeatureDrawerState.select_feature(factor["feature"]),
    )

    # Tooltip.content chỉ nhận chuỗi văn bản (String)
    tooltip_text = (
        factor["feature"].to_string()
        + " = "
        + factor["display_value"].to_string()
        + " · Increases PD by "
        + factor["shap_value"].to_string()[:6]
        + " · Hover or click to view data lineage"
    )

    return rx.tooltip(
        row_content,
        content=tooltip_text,
    )


def trust_driver_row(factor: dict) -> rx.Component:
    """Hàng yếu tố làm giảm rủi ro (Xanh) có Hover sáng hàng + Tooltip chuỗi hợp lệ."""
    row_content = rx.hstack(
        # Cột 1: Feature & value
        rx.hstack(
            rx.text(factor["feature"], font_family="monospace", font_size="13px", color="#E5E7EB", weight="medium"),
            rx.text("=", font_family="monospace", font_size="13px", color="#9CA3AF"),
            rx.text(factor["display_value"].to_string(), font_family="monospace", font_size="13px", color="#FFFFFF", weight="bold"),
            spacing="2",
            width="35%",
            overflow="hidden",
            white_space="nowrap",
        ),
        # Cột 2: Vùng trống bên trái
        rx.box(width="32.5%"),
        # Trục trung tâm (Baseline)
        rx.box(width="1px", height="24px", background="#374151"),
        # Cột 3: Khung bên phải chứa thanh bar xanh và nhãn số
        rx.hstack(
            rx.box(
                rx.box(
                    height="18px",
                    width=factor["bar_width"],
                    background="#10B981",
                    border_radius="0 4px 4px 0",
                    transition="all 0.2s ease-in-out",
                ),
                width="180px",
                display="flex",
                justify_content="flex-start",
            ),
            rx.text(
                factor["shap_value"].to_string()[:7],
                font_family="monospace",
                font_size="12px",
                color="#34D399",
                font_weight="bold",
                margin_left="8px",
            ),
            width="32.5%",
            justify="start",
            align="center",
        ),
        width="100%",
        align="center",
        padding_x="3",
        padding_y="1.5",
        border_radius="6px",
        cursor="pointer",
        _hover={
            "background": "rgba(255, 255, 255, 0.06)",
        },
        transition="background 0.15s ease",
        on_click=lambda: FeatureDrawerState.select_feature(factor["feature"]),
    )

    # Tooltip.content chỉ nhận chuỗi văn bản (String)
    tooltip_text = (
        factor["feature"].to_string()
        + " = "
        + factor["display_value"].to_string()
        + " · Reduces PD by "
        + factor["shap_value"].to_string()[:7]
        + " · Hover or click to view data lineage"
    )

    return rx.tooltip(
        row_content,
        content=tooltip_text,
    )


def shap_card_view() -> rx.Component:
    return rx.card(
        rx.vstack(
            # Tiêu đề Card
            rx.hstack(
                rx.hstack(
                    rx.icon("bar-chart-3", size=18, color="#9CA3AF"),
                    rx.vstack(
                        rx.heading("Risk Driver Contributions", size="3", color="white"),
                        rx.text("SHAP attribution · select a driver to view source evidence", size="1", color="#9CA3AF"),
                        spacing="0",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    "Open evidence panel",
                    variant="ghost",
                    color_scheme="gray",
                    size="1",
                    cursor="pointer",
                ),
                width="100%",
                align="center",
                padding_bottom="3",
            ),

            # Tiêu đề cột
            rx.hstack(
                rx.text("Feature & value", size="1", color="#9CA3AF", width="35%", padding_left="3"),
                rx.text("Increases risk", size="1", color="#9CA3AF", width="32.5%", text_align="right", padding_right="8px"),
                rx.box(width="1px", height="12px", background="#374151"),
                rx.text("Reduces risk", size="1", color="#9CA3AF", width="32.5%", padding_left="8px"),
                width="100%",
                align="center",
                padding_bottom="2",
                border_bottom="1px solid #1F2937",
            ),

            # Danh sách Trust (Xanh - Giảm rủi ro)
            rx.vstack(
                rx.foreach(
                    UnderwritingState.top_positive_factors,
                    lambda f: trust_driver_row(f),
                ),
                width="100%",
                spacing="1",
                padding_top="2",
            ),

            # Danh sách Risk (Đỏ - Tăng rủi ro)
            rx.vstack(
                rx.foreach(
                    UnderwritingState.top_risk_factors,
                    lambda f: risk_driver_row(f),
                ),
                width="100%",
                spacing="1",
                padding_top="1",
            ),

            # Chân trang (Baseline note)
            rx.hstack(
                rx.text("Neutral baseline", size="1", color="#6B7280", padding_left="3"),
                rx.spacer(),
                rx.text("Negative pulls reduce PD · positive pulls increase PD", size="1", color="#6B7280"),
                width="100%",
                align="center",
                padding_top="4",
                border_top="1px solid #1F2937",
                margin_top="3",
            ),
            spacing="1",
            width="100%",
        ),
        background="#111827",
        border="1px solid #1F2937",
        border_radius="10px",
        padding="5",
        width="100%",
    )