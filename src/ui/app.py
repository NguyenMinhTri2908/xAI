import reflex as rx
from src.ui.state import UnderwritingState

# Import các components con đã module hóa
from src.ui.components.shap_card import shap_card_view
from src.ui.components.kpi_card import kpi_card_view
from src.ui.components.cash_flow import cash_flow_view
from src.ui.components.what_if import what_if_view
from src.ui.components.decision_notes import decision_notes_view


def top_fixed_header() -> rx.Component:
    return rx.box(
        rx.box(
            rx.hstack(
                # Nút mở Sidebar Drawer (Đẩy ngang từ trái qua phải)
                rx.hstack(
                    rx.drawer.root(
                        rx.drawer.trigger(
                            rx.button(
                                rx.icon("panel-left", size=18),
                                rx.text("Queue", size="2"),
                                variant="surface",
                                color_scheme="gray",
                                size="2",
                                cursor="pointer",
                            )
                        ),
                        rx.drawer.overlay(background="rgba(0, 0, 0, 0.6)"),
                        # side="left" bảo đảm đẩy ngang từ hông trái ra
                        rx.drawer.content(
                            rx.vstack(
                                rx.hstack(
                                    rx.vstack(
                                        rx.heading("Loan Applications Queue", size="4", color="white"),
                                        rx.text("Select a client to evaluate", size="1", color="#9CA3AF"),
                                        spacing="0",
                                    ),
                                    rx.spacer(),
                                    rx.drawer.close(
                                        rx.button(rx.icon("x", size=18), variant="ghost", color_scheme="gray", size="1")
                                    ),
                                    width="100%",
                                    align="center",
                                    padding_bottom="3",
                                    border_bottom="1px solid #1F2937",
                                ),
                                # Danh sách bảng trong Drawer
                                rx.box(
                                    rx.table.root(
                                        rx.table.header(
                                            rx.table.row(
                                                rx.table.column_header_cell("Client ID"),
                                                rx.table.column_header_cell("Income"),
                                                rx.table.column_header_cell("Action"),
                                            )
                                        ),
                                        rx.table.body(
                                            rx.foreach(
                                                UnderwritingState.client_list,
                                                lambda row: rx.table.row(
                                                    rx.table.cell(rx.text(row["SK_ID_CURR"], weight="medium", size="2")),
                                                    rx.table.cell(rx.text(row["INCOME_DISPLAY"], size="2")),
                                                    rx.table.cell(
                                                        rx.drawer.close(
                                                            rx.button(
                                                                "Open",
                                                                size="1",
                                                                variant=rx.cond(
                                                                    UnderwritingState.selected_client_id == row["SK_ID_CURR"].to_string(),
                                                                    "solid",
                                                                    "soft",
                                                                ),
                                                                on_click=lambda: UnderwritingState.select_and_evaluate_client(
                                                                    row["SK_ID_CURR"].to_string()
                                                                ),
                                                            )
                                                        )
                                                    ),
                                                    style={
                                                        "background_color": rx.cond(
                                                            UnderwritingState.selected_client_id == row["SK_ID_CURR"].to_string(),
                                                            "#1F2937",
                                                            "transparent",
                                                        )
                                                    },
                                                ),
                                            )
                                        ),
                                        width="100%",
                                        variant="surface",
                                    ),
                                    overflow_y="auto",
                                    max_height="80vh",
                                    width="100%",
                                ),
                                spacing="4",
                                padding="4",
                                height="100%",
                                background="#111827",
                            ),
                            side="left",
                            width="360px",
                        ),
                    ),
                    rx.badge("#LN-2026-8891", color_scheme="blue", variant="surface", size="2"),
                    rx.text("Trần Văn A", font_weight="bold", size="3", color="white"),
                    rx.badge("Age: 34", variant="soft", color_scheme="gray"),
                    spacing="3",
                    align="center",
                ),
                # Thông tin Loan Terms & Cut-off 16%
                rx.hstack(
                    rx.vstack(
                        rx.text("LOAN TERMS", size="1", color="#9CA3AF", font_weight="bold"),
                        rx.text("$25,000 / 24 mos", font_weight="bold", size="2", color="white"),
                        rx.text("Suggested Rate: 11.2% APR (Tier B)", size="1", color="#9CA3AF"),
                        align_items="flex-end",
                        spacing="0",
                    ),
                    rx.divider(orientation="vertical", size="2", color_scheme="gray"),
                    rx.vstack(
                        rx.badge("PD: 4.8%", color_scheme="amber", size="3", variant="solid"),
                        rx.text("Cut-off: 16.0%", size="1", color="#9CA3AF"),
                        align_items="center",
                        spacing="0",
                    ),
                    spacing="4",
                    align="center",
                ),
                justify="between",
                width="100%",
                align="center",
            ),
            max_width="1600px",
            margin="0 auto",
            padding_x="6",
            padding_y="3",
        ),
        position="sticky",
        top="0",
        z_index="50",
        background="#0F172A",
        border_bottom="1px solid #1E293B",
        box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.3)",
        width="100%",
    )


def index() -> rx.Component:
    return rx.box(
        top_fixed_header(),

        # Khung nội dung chính với giới hạn max_width và padding 2 bên cân đối
        rx.box(
            rx.hstack(
                # CỘT TRÁI (70%): BẢO ĐẢM RỘNG RÃI CHO BIỂU ĐỒ SHAP
                rx.vstack(
                    shap_card_view(),
                    spacing="4",
                    width="70%",
                ),

                # CỘT PHẢI (30%): KPI, CASH FLOW, SIMULATOR & DECISION NOTES
                rx.vstack(
                    kpi_card_view(),
                    cash_flow_view(),
                    what_if_view(),
                    decision_notes_view(),
                    spacing="4",
                    width="30%",
                ),
                width="100%",
                spacing="5",
                align_items="flex-start",
            ),
            max_width="1600px",
            margin="0 auto",
            padding_x="6",
            padding_y="5",
            width="100%",
        ),
        on_mount=UnderwritingState.load_demo_clients,
        width="100%",
        min_height="100vh",
        background="#090D16",
    )


app = rx.App()
app.add_page(index, title="Credit Underwriting Dashboard")