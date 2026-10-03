import reflex as rx
from ..feature_search_state import FeatureSearchState


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
    """Component view displaying the searchable dictionary, live SHAP impact, and source filters."""
    return rx.vstack(
        # 1. Header & Counter Section
        rx.hstack(
            rx.vstack(
                rx.heading("Model Feature Dictionary & Live SHAP Impact", size="4", color="white"),
                rx.text(
                    "Search 891 audited features and inspect active client feature attributions.",
                    color="#9CA3AF",
                    size="1",
                ),
                spacing="0",
            ),
            rx.badge(
                rx.hstack(
                    rx.icon("layers", size=13),
                    rx.text(f"{FeatureSearchState.total_matches} Features"),
                    align="center",
                    spacing="1",
                ),
                color_scheme="cyan",
                variant="surface",
                size="2",
            ),
            justify="between",
            align="center",
            width="100%",
        ),

        rx.divider(border_color="#1E293B", margin_y="1"),

        # 2. Control Toolbar: Search Query + Table Selector + Impact Selector
        rx.hstack(
            rx.input(
                rx.input.slot(rx.icon("search", size=15)),
                placeholder="Search feature name or description (e.g., DPD, annuity, ratio)...",
                value=FeatureSearchState.search_query,
                on_change=FeatureSearchState.set_search_query,
                size="2",
                width="50%",
            ),
            rx.select(
                FeatureSearchState.available_tables,
                value=FeatureSearchState.selected_table,
                on_change=FeatureSearchState.set_selected_table,
                size="2",
                width="25%",
            ),
            rx.select(
                FeatureSearchState.available_impacts,
                value=FeatureSearchState.selected_impact,
                on_change=FeatureSearchState.set_selected_impact,
                size="2",
                width="25%",
            ),
            spacing="3",
            width="100%",
        ),

        # 3. Main Data Table
        rx.box(
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Feature Name", width="28%"),
                        rx.table.column_header_cell("Source Table", width="18%"),
                        rx.table.column_header_cell("SHAP Impact", width="16%"),
                        rx.table.column_header_cell("Underwriting Description", width="38%"),
                    )
                ),
                rx.table.body(
                    rx.foreach(
                        FeatureSearchState.filtered_features,
                        lambda item: rx.table.row(
                            # Tên biến kỹ thuật
                            rx.table.cell(
                                rx.text(
                                    item["name"],
                                    font_family="monospace",
                                    weight="bold",
                                    size="1",
                                    color="#F8FAFC",
                                )
                            ),
                            # Nhãn bảng dữ liệu gốc
                            rx.table.cell(table_badge(item["table"])),
                            # Badge hiển thị điểm SHAP tác động (Đỏ: rủi ro, Xanh: an toàn, Xám: trung tính)
                            rx.table.cell(
                                rx.badge(
                                    item["impact_text"],
                                    color_scheme=item["impact_color"],
                                    variant="solid",
                                    size="1",
                                )
                            ),
                            # Diễn giải nghiệp vụ tín dụng
                            rx.table.cell(
                                rx.text(
                                    item["description"],
                                    size="1",
                                    color="#94A3B8",
                                )
                            ),
                        ),
                    )
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
        ),

        # 4. Lazy-load button (Chỉ hiển thị khi đang xem danh sách mặc định)
        rx.cond(
            (FeatureSearchState.search_query == "")
            & (FeatureSearchState.selected_table == "All")
            & (FeatureSearchState.selected_impact == "All"),
            rx.button(
                "Load More Features (+20)",
                on_click=FeatureSearchState.load_more,
                variant="soft",
                color_scheme="gray",
                size="1",
                width="100%",
            ),
            rx.fragment(),
        ),

        on_mount=FeatureSearchState.load_feature_dictionary,
        spacing="3",
        width="100%",
        padding="4",
    )