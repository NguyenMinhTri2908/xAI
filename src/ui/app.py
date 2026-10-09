import reflex as rx
from src.ui.state import UnderwritingState
from .components.feature_search_view import feature_search_view

# Import các components con
from src.ui.components.shap_card import shap_card_view
from src.ui.components.cash_flow import cash_flow_view
from src.ui.components.what_if import what_if_view
from src.ui.components.decision_notes import decision_notes_view
from src.ui.drawer_state import FeatureDrawerState

# --- 1. IMPORT FEATURE DETAIL DRAWER ---
from src.ui.components.feature_drawer import feature_detail_drawer


# ==============================================================================
# HEADER COMPONENTS
# ==============================================================================

def breadcrumb_bar() -> rx.Component:
    """Thanh Breadcrumb tinh gọn tích hợp Drawer chọn hồ sơ."""
    return rx.box(
        rx.box(
            rx.hstack(
                rx.hstack(
                    # Nút Drawer mở danh sách khách hàng
                    rx.drawer.root(
                        rx.drawer.trigger(
                            rx.button(
                                rx.icon("panel-left", size=15),
                                rx.text("Queue", size="1", weight="bold"),
                                variant="surface",
                                color_scheme="gray",
                                size="1",
                                cursor="pointer",
                            )
                        ),
                        rx.drawer.overlay(background="rgba(0, 0, 0, 0.7)"),
                        rx.drawer.content(
                            rx.vstack(
                                rx.hstack(
                                    rx.vstack(
                                        rx.heading("Loan Applications Queue", size="3", color="white"),
                                        rx.text("Select a client to evaluate", size="1", color="#9CA3AF"),
                                        spacing="0",
                                    ),
                                    rx.spacer(),
                                    rx.drawer.close(
                                        rx.button(rx.icon("x", size=16), variant="ghost", color_scheme="gray", size="1")
                                    ),
                                    width="100%",
                                    align="center",
                                    padding_bottom="2",
                                    border_bottom="1px solid #1F2937",
                                ),
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
                                                    rx.table.cell(rx.text(row["SK_ID_CURR"], weight="medium", size="1")),
                                                    rx.table.cell(rx.text(row["INCOME_DISPLAY"], size="1")),
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
                                        size="1",
                                    ),
                                    overflow_y="auto",
                                    max_height="80vh",
                                    width="100%",
                                ),
                                spacing="3",
                                padding="4",
                                height="100%",
                                background="#111827",
                            ),
                            side="left",
                            width="340px",
                        ),
                    ),
                    rx.icon("landmark", size=15, color="#94A3B8"),
                    rx.text("Credit Appraisal Workbench", size="2", weight="bold", color="#F8FAFC"),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.badge("System Online", color_scheme="green", variant="surface"),
                justify="between",
                width="100%",
                align="center",
            ),
            max_width="1600px",
            margin="0 auto",
            padding_x="6",
            padding_y="2",
            width="100%",
        ),
        width="100%",
        background="#0D1117",
        border_bottom="1px solid #1E293B",
    )


def client_profile_card() -> rx.Component:
    """Card 1 (Trái): Thông tin cá nhân / Profile khách hàng."""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.hstack(
                    rx.icon("user", size=16, color="#9CA3AF"),
                    rx.text(
                        rx.cond(
                            UnderwritingState.selected_client_id != "",
                            f"ID: #{UnderwritingState.selected_client_id}",
                            "ID: N/A",
                        ),
                        size="3",
                        font_weight="600",
                        color="#9CA3AF",
                    ),
                    spacing="2",
                    align="center",
                ),
                width="100%",
                align="center",
            ),
            rx.divider(border_color="#1E293B", margin_y="1"),
            # Grid thông tin cá nhân
            rx.grid(
                rx.vstack(
                    rx.text("NAME", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        "Client Name",
                        size="4",
                        weight="bold",
                        color="#FFFFFF",
                    ),
                    spacing="1",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("APPLICANT AGE", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        UnderwritingState.client_age,
                        size="4",
                        weight="bold",
                        color="#FFFFFF",
                    ),
                    spacing="1",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("EMPLOYMENT TENURE", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        UnderwritingState.client_experience,
                        size="4",
                        weight="bold",
                        color="#FFFFFF",
                    ),
                    spacing="1",
                    align_items="flex-start",
                ),
                columns="2",
                spacing="3",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        background="#111827",
        border="1px solid #1F2937",
        border_radius="10px",
        padding="5",
        flex="1",
        width="100%",
    )


def loan_terms_card() -> rx.Component:
    """Card 2 (Giữa): Thông tin khoản vay / Điều kiện đề xuất."""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.hstack(
                    rx.icon("credit-card", size=16, color="#9CA3AF"),
                    rx.text(
                        "Loan Details",
                        size="3",
                        font_weight="600",
                        color="#9CA3AF",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.badge(
                    "Active Terms",
                    variant="surface",
                    color_scheme="gray",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            rx.divider(border_color="#1E293B", margin_y="1"),
            # 2x2 Grid
            rx.grid(
                rx.vstack(
                    rx.text("REQUESTED AMOUNT", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        UnderwritingState.client_credit,
                        size="4",
                        weight="bold",
                        color="#FFFFFF",
                    ),
                    spacing="1",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("LOAN TERM", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        UnderwritingState.client_term,
                        size="4",
                        weight="bold",
                        color="#FFFFFF",
                    ),
                    spacing="1",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("EST. MONTHLY PAYMENT", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        UnderwritingState.client_annuity,
                        size="4",
                        weight="bold",
                        color="#FFFFFF",
                    ),
                    spacing="1",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("DEBT-TO-INCOME (DTI)", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        UnderwritingState.client_dti,
                        size="4",
                        weight="bold",
                        color="#FFFFFF",
                    ),
                    spacing="1",
                    align_items="flex-start",
                ),
                columns="2",
                spacing="3",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        background="#111827",
        border="1px solid #1F2937",
        border_radius="10px",
        padding="5",
        flex="1",
        width="100%",
    )


def ai_recommendation_card() -> rx.Component:
    """Card 3 (Phải): Đánh giá & Khuyến nghị mô hình AI."""
    return rx.card(
        rx.vstack(
            # Header
            rx.hstack(
                rx.hstack(
                    rx.icon("sparkles", size=16, color="#9CA3AF"),
                    rx.text(
                        "AI Recommendation",
                        size="3",
                        font_weight="600",
                        color="#9CA3AF",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.badge(
                    rx.cond(
                        UnderwritingState.current_tier != "None",
                        f"Tier {UnderwritingState.current_tier}",
                        "Tier N/A",
                    ),
                    color_scheme="gray",
                    variant="surface",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            rx.divider(border_color="#1E293B", margin_y="1"),
            # Khôi phục layout 2 cột cũ với chuẩn typography và padding mới
            rx.grid(
                rx.vstack(
                    rx.text("PROBABILITY OF DEFAULT", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        UnderwritingState.pd_display,
                        size="4",
                        weight="bold",
                        color=UnderwritingState.decision_color,
                    ),
                    rx.text("Threshold: 16.0% (±1.0%)", size="1", color="#64748B", weight="medium"),
                    spacing="1",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("SUGGESTED ACTION", size="1", color="#9CA3AF", weight="medium"),
                    rx.box(
                        rx.hstack(
                            rx.icon(
                                rx.cond(
                                    UnderwritingState.decision_color == "#10B981",
                                    "check-circle-2",
                                    rx.cond(
                                        UnderwritingState.decision_color == "#F59E0B",
                                        "clock",
                                        "alert-triangle",
                                    ),
                                ),
                                size=14,
                                color=UnderwritingState.decision_color,
                            ),
                            rx.text(
                                UnderwritingState.current_decision,
                                size="2",
                                weight="bold",
                                color=UnderwritingState.decision_color,
                            ),
                            spacing="2",
                            align="center",
                        ),
                        background=UnderwritingState.decision_bg_color,
                        border=f"1px solid {UnderwritingState.decision_color}",
                        border_radius="6px",
                        padding_x="2.5",
                        padding_y="1",
                        display="inline-flex",
                    ),
                    rx.text(
                        rx.cond(
                            UnderwritingState.decision_color == "#F59E0B",
                            "Requires committee evaluation",
                            "Policy benchmark aligned",
                        ),
                        size="1",
                        color="#64748B",
                    ),
                    spacing="1",
                    align_items="flex-start",
                ),
                columns="2",
                spacing="3",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        background="#111827",
        border="1px solid #1F2937",
        border_radius="10px",
        padding="5",
        flex="1",
        width="100%",
    )


def action_bar_view() -> rx.Component:
    """Hàng 4 nút quyết định phê duyệt bên dưới."""
    return rx.hstack(
        rx.button(
            rx.icon("circle-check", size=16),
            "Approve",
            background="#059669",
            color="white",
            size="2",
            radius="medium",
            cursor="pointer",
        ),
        rx.button(
            rx.icon("circle-x", size=16),
            "Decline Loan",
            background="#DC2626",
            color="white",
            size="2",
            radius="medium",
            cursor="pointer",
        ),
        rx.button(
            rx.icon("check", size=16),
            "Approve with Conditions",
            variant="outline",
            color_scheme="gray",
            size="2",
            radius="medium",
            cursor="pointer",
        ),
        rx.button(
            rx.icon("users", size=16),
            "Escalate to Committee",
            rx.icon("chevron-down", size=14),
            variant="outline",
            color_scheme="gray",
            size="2",
            radius="medium",
            cursor="pointer",
        ),
        spacing="3",
        align="center",
        width="100%",
        padding_top="1",
    )


def full_underwriting_header() -> rx.Component:
    """Header tổng thể với căn lề max_width đồng bộ nội dung trang."""
    return rx.box(
        breadcrumb_bar(),
        rx.box(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        client_profile_card(),
                        loan_terms_card(),
                        ai_recommendation_card(),
                        spacing="4",
                        width="100%",
                        align_items="stretch",
                    ),
                    action_bar_view(),
                    spacing="3",
                    width="100%",
                ),
                max_width="1600px",
                margin="0 auto",
                padding_x="6",
                padding_y="4",
                width="100%",
            ),
            width="100%",
            background="#090D16",
        ),
        width="100%",
        position="sticky",
        top="0",
        z_index="50",
        border_bottom="1px solid #1E293B",
    )


# ==============================================================================
# MAIN PAGE INDEX
# ==============================================================================

def index() -> rx.Component:
    return rx.box(
        full_underwriting_header(),

        # Khung nội dung chính 2 cột (Căn lề max_width 1600px đồng nhất)
        rx.box(
            rx.hstack(
                # CỘT TRÁI (70%): SHAP CHART + FEATURE IMPACT EXPLORER
                rx.vstack(
                    shap_card_view(),
                    rx.box(
                        feature_search_view(),
                        background="#0F172A",
                        border="1px solid #1E293B",
                        border_radius="12px",
                        box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.3)",
                        width="100%",
                    ),
                    spacing="4",
                    width="70%",
                ),

                # CỘT PHẢI (30%): CASH FLOW, SIMULATOR & DECISION NOTES
                rx.vstack(
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

        # --- 2. ĐẶT FEATURE DETAIL DRAWER Ở ĐÂY ---
        feature_detail_drawer(),

        on_mount=UnderwritingState.load_demo_clients,
        width="100%",
        min_height="100vh",
        background="#090D16",
    )


app = rx.App()
app.add_page(index, title="Credit Underwriting Dashboard")