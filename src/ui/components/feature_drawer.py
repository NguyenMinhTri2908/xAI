import reflex as rx
from ..drawer_state import FeatureDrawerState


def feature_detail_drawer() -> rx.Component:
    """Slide-over Drawer trượt từ bên phải (Right side), chiếm ~1/3 màn hình."""
    return rx.drawer.root(
        rx.drawer.overlay(
            background_color="rgba(0, 0, 0, 0.55)",
            backdrop_filter="blur(3px)",
        ),
        rx.drawer.portal(
            rx.drawer.content(
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
                        rx.drawer.close(
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
                        padding_bottom="2",
                        border_bottom="1px solid #21262D",
                    ),

                    # 2. Nội dung chi tiết xếp dọc vừa vặn cho 1/3 màn hình
                    rx.vstack(
                        # Box 1: Raw Value
                        rx.box(
                            rx.text(
                                "RAW / CLIENT VALUE",
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

                        # Box 2: SHAP Impact
                        rx.box(
                            rx.text(
                                "TREE-SHAP IMPACT",
                                size="1",
                                color="#64748B",
                                weight="bold",
                            ),
                            rx.text(
                                FeatureDrawerState.selected_feature.get("shap_value", "0.0"),
                                size="3",
                                weight="bold",
                                color="#38BDF8",
                                margin_top="1",
                            ),
                            padding="3",
                            background="#0D1117",
                            border="1px solid #21262D",
                            border_radius="8px",
                            width="100%",
                        ),

                        # Box 3: Underwriting Context
                        rx.box(
                            rx.text(
                                "UNDERWRITING CONTEXT",
                                size="1",
                                color="#64748B",
                                weight="bold",
                            ),
                            rx.text(
                                FeatureDrawerState.selected_feature.get(
                                    "description",
                                    "No manual override notes recorded for this feature metric.",
                                ),
                                size="1",
                                color="#CBD5E1",
                                margin_top="1",
                                line_height="1.5",
                            ),
                            padding="3",
                            background="#0D1117",
                            border="1px solid #21262D",
                            border_radius="8px",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                        margin_top="2",
                    ),

                    spacing="3",
                    width="100%",
                    height="100%",
                    padding="4",
                ),
                # --- THUỘC TÍNH BẮT BUỘC ĐỂ TRƯỢT TỪ BÊN PHẢI VÀ RỘNG 1/3 ---
                side="right",                           # Định hướng xuất hiện bên tay phải
                width=["85vw", "33.33vw"],              # Chiếm đúng 1/3 chiều rộng màn hình (33.33vw)
                min_width="360px",                      # Không bị co rúm trên màn hình nhỏ
                max_width="520px",                      # Không quá to trên màn hình siêu rộng
                height="100vh",
                top="0",
                right="0",
                position="fixed",
                background="#161B22",
                border_left="1px solid #30363D",
            )
        ),
        open=FeatureDrawerState.is_open,
        on_open_change=FeatureDrawerState.close_drawer,
        direction="right",
    )