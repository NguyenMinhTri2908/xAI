import reflex as rx
from src.ui.drawer_state import FeatureDrawerState


def property_row(icon_name: str, label: str, value_component: rx.Component) -> rx.Component:
    """Renders a Notion-style key-value property row with consistent dark mode typography and alignment."""
    return rx.hstack(
        rx.hstack(
            rx.icon(icon_name, size=14, color="#9CA3AF"),
            rx.text(label, size="2", color="#9CA3AF", weight="medium"),
            spacing="2",
            align="center",
            width="140px",
            flex_shrink=0,
        ),
        value_component,
        width="100%",
        align="center",
        padding_y="1",
    )


def feature_detail_drawer() -> rx.Component:
    """Notion-style Slide-over Feature Inspector: 520px fixed to the right edge with dark mode styling."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # 1. Notion Top Breadcrumb & Close Bar
                rx.hstack(
                    rx.hstack(
                        rx.icon("layout-list", size=14, color="#9CA3AF"),
                        rx.text("Feature Dictionary", size="1", color="#9CA3AF", weight="medium"),
                        rx.text("/", size="1", color="#4B5563"),
                        rx.text("Inspection", size="1", color="#6B7280"),
                        spacing="1",
                        align="center",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon_button(
                            rx.icon("x", size=16, color="#9CA3AF"),
                            variant="ghost",
                            color_scheme="gray",
                            on_click=FeatureDrawerState.close_drawer,
                            cursor="pointer",
                            size="1",
                            border_radius="6px",
                        )
                    ),
                    width="100%",
                    padding_bottom="2",
                ),

                # 2. Notion Page Title
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.icon("layers", size=20, color="#FFFFFF"),
                            background="#27272A",
                            padding="2",
                            border_radius="8px",
                            border="1px solid #3F3F46",
                        ),
                        rx.vstack(
                            rx.heading(
                                FeatureDrawerState.feature_title,
                                font_family="monospace",
                                size="4",
                                weight="bold",
                                color="#FFFFFF",
                            ),
                            rx.text(
                                "Model Attribution & Underwriting Definition",
                                size="1",
                                color="#9CA3AF",
                            ),
                            spacing="0",
                            align_items="flex-start",
                        ),
                        spacing="3",
                        align="center",
                    ),
                    width="100%",
                    align_items="flex-start",
                    padding_y="2",
                ),

                rx.divider(border_color="#27272A", margin_y="1"),

                # 3. Notion Properties Grid (Dark Property Badges with bg="#27272A")
                rx.vstack(
                    rx.text(
                        "PROPERTIES",
                        size="2",
                        weight="bold",
                        color="#9CA3AF",
                        letter_spacing="0.05em",
                        margin_bottom="1",
                    ),

                    # Property: Origin Table
                    property_row(
                        "database",
                        "Origin Table",
                        rx.box(
                            rx.hstack(
                                rx.icon("table-2", size=12, color="#9CA3AF"),
                                rx.text(
                                    FeatureDrawerState.origin_table,
                                    size="2",
                                    weight="medium",
                                    color="#F3F4F6",
                                    font_family="monospace",
                                ),
                                spacing="1",
                                align="center",
                            ),
                            background="#27272A",
                            border="1px solid #3F3F46",
                            border_radius="6px",
                            padding_x="2.5",
                            padding_y="1",
                            display="inline-flex",
                        ),
                    ),

                    # Property: Client Value
                    property_row(
                        "hash",
                        "Client Value",
                        rx.box(
                            rx.text(
                                FeatureDrawerState.client_value,
                                size="2",
                                weight="medium",
                                color="#F3F4F6",
                                font_family="monospace",
                            ),
                            background="#27272A",
                            border="1px solid #3F3F46",
                            border_radius="6px",
                            padding_x="2.5",
                            padding_y="1",
                            display="inline-flex",
                        ),
                    ),

                    # Property: Impact Direction
                    property_row(
                        "activity",
                        "Impact Direction",
                        rx.box(
                            rx.hstack(
                                rx.box(
                                    width="8px",
                                    height="8px",
                                    border_radius="50%",
                                    background=FeatureDrawerState.shap_impact_color,
                                ),
                                rx.text(
                                    FeatureDrawerState.shap_direction_label,
                                    size="2",
                                    weight="medium",
                                    color="#F3F4F6",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            background="#27272A",
                            border="1px solid #3F3F46",
                            border_radius="6px",
                            padding_x="2.5",
                            padding_y="1",
                            display="inline-flex",
                        ),
                    ),

                    # Property: SHAP Value (Unified Local Attribution)
                    property_row(
                        "gauge",
                        "SHAP Impact",
                        rx.box(
                            rx.text(
                                FeatureDrawerState.shap_display_text,
                                size="2",
                                weight="bold",
                                color=FeatureDrawerState.shap_impact_color,
                                font_family="monospace",
                            ),
                            background="#27272A",
                            border="1px solid #3F3F46",
                            border_radius="6px",
                            padding_x="2.5",
                            padding_y="1",
                            display="inline-flex",
                        ),
                    ),

                    width="100%",
                    spacing="2",
                    align_items="flex-start",
                ),

                rx.divider(border_color="#27272A", margin_y="1"),

                # 4. Description Section (Seamless display on drawer background without boxes/borders)
                rx.vstack(
                    rx.text(
                        "DESCRIPTION",
                        size="2",
                        weight="bold",
                        color="#9CA3AF",
                        letter_spacing="0.05em",
                        margin_bottom="1",
                    ),
                    rx.text(
                        FeatureDrawerState.description,
                        size="3",
                        weight="medium",
                        color="#F3F4F6",
                        line_height="1.6",
                    ),
                    spacing="2",
                    width="100%",
                    align_items="flex-start",
                ),

                spacing="0",
                width="100%",
                height="100%",
                padding_left="28px",
                padding_right="24px",
                padding_y="6",
                overflow_y="auto",
                background="#121212",
            ),
            position="fixed",
            top="0",
            right="0",
            bottom="0",
            left="auto",
            margin="0",
            width="520px",
            min_width="360px",
            max_width="520px",
            height="100vh",
            max_height="100vh",
            background="#121212",
            border_left="1px solid #27272A",
            box_shadow="-12px 0 36px rgba(0, 0, 0, 0.7)",
            border_radius="0",
            outline="none",
            padding="0",
        ),
        open=FeatureDrawerState.is_open,
        on_open_change=FeatureDrawerState.close_drawer,
    )