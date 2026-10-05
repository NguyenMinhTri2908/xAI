import reflex as rx
from src.ui.drawer_state import FeatureDrawerState


def property_row(icon_name: str, label: str, value_component: rx.Component) -> rx.Component:
    """Helper tạo 1 hàng thuộc tính chuẩn Property List Inspector."""
    return rx.hstack(
        # Cột trái: Icon + Tên nhãn thuộc tính
        rx.hstack(
            rx.icon(icon_name, size=15, color="#64748B"),
            rx.text(
                label,
                size="2",
                color="#8B949E",
                weight="medium",
            ),
            spacing="2",
            align="center",
            width="36%",
            min_width="120px",
            flex_shrink=0,
        ),
        # Cột phải: Giá trị
        rx.box(
            value_component,
            width="64%",
        ),
        align="start",
        width="100%",
        padding_y="3",
        border_bottom="1px solid rgba(255, 255, 255, 0.03)",
    )


def feature_detail_drawer() -> rx.Component:
    """Slide-over Inspector hoàn chỉnh: cố định mép phải, rộng 1/3 màn hình."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # 1. Header: Nút đóng
                rx.hstack(
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon_button(
                            rx.icon("x", size=18),
                            variant="ghost",
                            color_scheme="gray",
                            on_click=FeatureDrawerState.close_drawer,
                            cursor="pointer",
                            radius="full",
                        )
                    ),
                    width="100%",
                    justify="end",
                ),

                # Tên feature in hoa to, đậm ở trên cùng
                rx.heading(
                    FeatureDrawerState.selected_feature.get("feature", "FEATURE_NAME"),
                    size="6",
                    weight="bold",
                    color="#F0F6FC",
                    font_family="monospace",
                    margin_top="1",
                    margin_bottom="4",
                    word_break="break-word",
                ),

                # Đường phân cách mờ
                rx.divider(border_color="#21262D"),

                # 2. Danh sách thuộc tính 2 cột
                rx.vstack(
                    # Hàng 1: Origin Table
                    property_row(
                        "table-2",
                        "Origin Table",
                        rx.badge(
                            FeatureDrawerState.selected_feature.get("table", "application"),
                            variant="soft",
                            color_scheme="blue",
                            size="2",
                            radius="medium",
                            font_family="monospace",
                        ),
                    ),

                    # Hàng 2: Client Value
                    property_row(
                        "hash",
                        "Client Value",
                        rx.text(
                            FeatureDrawerState.selected_feature.get("display_value", "None"),
                            size="2",
                            weight="bold",
                            color="#F0F6FC",
                        ),
                    ),

                    # Hàng 3: SHAP Impact (Làm tròn 4 số và bỏ ngoặc đơn)
                    property_row(
                        "activity",
                        "SHAP Impact",
                        rx.hstack(
                            rx.text(
                                FeatureDrawerState.display_shap_value,
                                size="3",
                                weight="bold",
                                color=FeatureDrawerState.shap_impact_color,
                                font_family="monospace",
                            ),
                            rx.badge(
                                FeatureDrawerState.shap_direction_label,
                                color_scheme=rx.cond(
                                    FeatureDrawerState.shap_impact_color == "#10B981",
                                    "green",
                                    "red",
                                ),
                                variant="soft",
                                size="1",
                                radius="medium",
                            ),
                            spacing="3",
                            align="center",
                        ),
                    ),

                    # Hàng 4: Underwriting Context
                    property_row(
                        "align-left",
                        "Context Detail",
                        rx.text(
                            FeatureDrawerState.selected_feature.get(
                                "description",
                                "No specific underwriting notes recorded for this metric.",
                            ),
                            size="2",
                            color="#C9D1D9",
                            line_height="1.6",
                        ),
                    ),

                    spacing="0",
                    width="100%",
                    margin_top="7",
                ),

                spacing="0",
                width="100%",
                height="100%",
                padding="6",
                overflow_y="auto",
            ),
            position="fixed",
            top="0",
            right="0",
            bottom="0",
            left="auto",
            margin="0",
            width=["85vw", "33.33vw"],
            min_width="400px",
            max_width="560px",
            height="100vh",
            max_height="100vh",
            background="#161B22",
            border_left="1px solid #30363D",
            box_shadow="-8px 0 30px rgba(0, 0, 0, 0.7)",
            border_radius="0",
            outline="none",
        ),
        open=FeatureDrawerState.is_open,
        on_open_change=FeatureDrawerState.close_drawer,
    )