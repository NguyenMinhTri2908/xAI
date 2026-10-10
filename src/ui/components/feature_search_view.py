import reflex as rx
from ..feature_search_state import FeatureSearchState
from src.ui.drawer_state import FeatureDrawerState


def table_badge(table_name: str) -> rx.Component:
    """Renders a styled color-coded badge for each raw source table."""
    color_map = {
        "application": "blue",
        "bureau": "purple",
        "bureau_balance": "indigo",
        "previous_application": "teal",
        "POS_CASH_balance": "amber",
        "installments_payments": "emerald",
        "credit_card_balance": "crimson",
    }
    return rx.badge(
        table_name,
        color_scheme=color_map.get(table_name, "gray"),
        variant="soft",
        size="1",
        radius="medium",
    )


def feature_search_view() -> rx.Component:
    """Component view displaying feature search, real-time SHAP impact, and auto-scroll streaming."""
    return rx.vstack(
        # 1. Header
        rx.vstack(
            rx.heading("Feature Search & Attribution", size="4", color="white", weight="bold"),
            rx.text(
                "Search 891 audited features and inspect active client local attributions.",
                color="#9CA3AF",
                size="2",
            ),
            spacing="0",
            width="100%",
            padding_top="2px",
            padding_left="12px",
        ),

        rx.divider(border_color="#1E293B", margin_y="1"),

        # 2. Control Toolbar: All Data Sources & All Impact Directions
        rx.hstack(
            rx.input(
                rx.input.slot(rx.icon("search", size=15)),
                placeholder="Search feature name or underwriting keywords...",
                value=FeatureSearchState.search_query,
                on_change=FeatureSearchState.set_search_query,
                size="2",
                width="46%",
            ),
            rx.select(
                FeatureSearchState.available_sources,
                value=FeatureSearchState.selected_source,
                on_change=FeatureSearchState.set_selected_source,
                size="2",
                width="27%",
            ),
            rx.select(
                FeatureSearchState.available_impacts,
                value=FeatureSearchState.selected_impact,
                on_change=FeatureSearchState.set_selected_impact,
                size="2",
                width="27%",
            ),
            spacing="3",
            width="100%",
        ),

        # 3. Data Table hỗ trợ auto-scroll
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Feature Name", width="28%"),
                        rx.table.column_header_cell("Data Source", width="18%"),
                        rx.table.column_header_cell("SHAP Impact", width="16%"),
                        rx.table.column_header_cell("Underwriting Description", width="38%"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        FeatureSearchState.filtered_features,
                        lambda item: rx.table.row(
                            rx.table.cell(
                                rx.text(
                                    item["name"],
                                    font_family="monospace",
                                    weight="bold",
                                    size="1",
                                    color="#F8FAFC",
                                )
                            ),
                            rx.table.cell(table_badge(item["table"])),
                            rx.table.cell(
                                rx.badge(
                                    item["impact_text"],
                                    color_scheme=item["impact_color"],
                                    variant="solid",
                                    size="1",
                                )
                            ),
                            rx.table.cell(
                                rx.text(
                                    item["description"],
                                    size="1",
                                    color="#94A3B8",
                                )
                            ),
                            # Hiệu ứng hover sáng toàn dòng + Click mở Notion-style Drawer
                            cursor="pointer",
                            transition="background 0.15s ease",
                            _hover={
                                "background": "rgba(56, 189, 248, 0.08)",
                            },
                            on_click=lambda: FeatureDrawerState.select_feature(item["name"]),
                        ),
                    ),
                    # Dòng thông báo trạng thái cuộn nhẹ ở cuối danh sách
                    rx.cond(
                        (FeatureSearchState.search_query == "")
                        & (FeatureSearchState.selected_source == "All Data Sources")
                        & (FeatureSearchState.selected_impact == "All Impact Directions"),
                        rx.table.row(
                            rx.table.cell(
                                rx.center(
                                    rx.text(
                                        "Scroll down to stream more features...",
                                        size="1",
                                        color="#64748B",
                                    ),
                                    padding="2",
                                    width="100%",
                                ),
                                col_span=4,
                            )
                        ),
                        rx.fragment(),
                    ),
                ),
                variant="surface",
                size="1",
                width="100%",
            ),
            max_height="480px",
            overflow_y="auto",
            width="100%",
            border="1px solid #1E293B",
            border_radius="8px",
            background="#0B132B",
            on_scroll=FeatureSearchState.load_more_on_scroll,
        ),

        on_mount=FeatureSearchState.load_feature_dictionary,
        spacing="3",
        width="100%",
        padding="4",
    )