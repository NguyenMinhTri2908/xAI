import reflex as rx
from ..drawer_state import FeatureDrawerState


def feature_detail_drawer() -> rx.Component:
    """Slide-over Inspector chuẩn: cố định mép phải, rộng đúng 1/3 màn hình."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # 1. Header Drawer
                rx.hstack(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("layers", size=18, color="#38BDF8"),
                            rx.heading(
                                FeatureDrawerState.selected_feature.get("feature", "N/A"),
                                font_family="monospace",
                                size="3",
                                weight="bold",
                                color="#F8FAFC",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        rx.text(
                            "Feature Attribution Details",
                            size="1",
                            color="#94A3B8",
                        ),
                        spacing="0",
                        align_items="flex-start",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon_button(
                            rx.icon("x", size=16),
                            variant="ghost",
                            color_scheme="gray",
                            on_click=FeatureDrawerState.close_drawer,
                            cursor="pointer",
                        )
                    ),
                    justify="between",
                    align="center",
                    width="100%",
                    padding_bottom="3",
                    border_bottom="1px solid #21262D",
                ),

                # 2. Nội dung chi tiết xếp dọc vừa vặn trong 1/3 màn hình
                rx.vstack(
                    # Khối 1: ORIGIN TABLE (Được đẩy lên trước Client Value)
                    rx.box(
                        rx.hstack(
                            rx.text(
                                "ORIGIN TABLE",
                                size="1",
                                color="#64748B",
                                weight="bold",
                            ),
                            rx.spacer(),
                            rx.badge(
                                FeatureDrawerState.selected_feature.get("table", "None"),
                                variant="surface",
                                color_scheme="blue",
                                size="1",
                            ),
                            width="100%",
                            align="center",
                        ),
                        padding="3",
                        background="#0D1117",
                        border="1px solid #21262D",
                        border_radius="8px",
                        width="100%",
                    ),

                    # Khối 2: CLIENT VALUE
                    rx.box(
                        rx.text(
                            "CLIENT VALUE",
                            size="1",
                            color="#64748B",
                            weight="bold",
                        ),
                        rx.text(
                            FeatureDrawerState.selected_feature.get("display_value", "None"),
                            size="3",
                            weight="bold",
                            color="#F8FAFC",
                            margin_top="1",
                        ),
                        padding="3",
                        background="#0D1117",
                        border="1px solid #21262D",
                        border_radius="8px",
                        width="100%",
                    ),

                    # Khối 3: SHAP IMPACT (Đổi màu theo tác động xác suất vỡ nợ PD)
                    rx.box(
                        rx.hstack(
                            rx.text(
                                "SHAP IMPACT",
                                size="1",
                                color="#64748B",
                                weight="bold",
                            ),
                            rx.spacer(),
                            rx.badge(
                                FeatureDrawerState.shap_direction_label,
                                color_scheme=rx.cond(
                                    FeatureDrawerState.shap_impact_color == "#10B981",
                                    "green",
                                    "red",
                                ),
                                variant="soft",
                                size="1",
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.text(
                            FeatureDrawerState.selected_feature.get("shap_value", "0.0"),
                            size="4",
                            weight="bold",
                            color=FeatureDrawerState.shap_impact_color,
                            margin_top="1",
                            font_family="monospace",
                        ),
                        padding="3",
                        background="#0D1117",
                        border="1px solid #21262D",
                        border_radius="8px",
                        width="100%",
                    ),

                    # Khối 4: UNDERWRITING CONTEXT (Chỉ chứa diễn giải nghiệp vụ thuần túy)
                    rx.box(
                        rx.vstack(
                            rx.text(
                                "UNDERWRITING CONTEXT",
                                size="1",
                                color="#64748B",
                                weight="bold",
                            ),
                            rx.text(
                                FeatureDrawerState.selected_feature.get(
                                    "description",
                                    "None",
                                ),
                                size="1",
                                color="#CBD5E1",
                                line_height="1.5",
                                margin_top="1",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        padding="3",
                        background="#0D1117",
                        border="1px solid #21262D",
                        border_radius="8px",
                        width="100%",
                    ),

                    spacing="3",
                    width="100%",
                    margin_top="3",
                ),

                spacing="3",
                width="100%",
                height="100%",
                padding="5",
                overflow_y="auto",
            ),
            position="fixed",
            top="0",
            right="0",
            bottom="0",
            left="auto",
            margin="0",
            width=["85vw", "33.33vw"],
            min_width="360px",
            max_width="520px",
            height="100vh",
            max_height="100vh",
            background="#161B22",
            border_left="1px solid #30363D",
            box_shadow="-8px 0 24px rgba(0, 0, 0, 0.6)",
            border_radius="0",
            outline="none",
        ),
        open=FeatureDrawerState.is_open,
        on_open_change=FeatureDrawerState.close_drawer,
    )