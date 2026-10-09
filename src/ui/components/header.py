import reflex as rx
from ..state import UnderwritingState


def breadcrumb_bar() -> rx.Component:
    """Thanh breadcrumb trên cùng màu tối và thông tin reviewer."""
    return rx.hstack(
        rx.hstack(
            rx.icon("landmark", size=15, color="#94A3B8"),
            rx.text(
                "Credit Appraisal Workbench",
                size="2",
                weight="bold",
                color="#F8FAFC",
            ),
            rx.text("/", size="2", color="#475569"),
            rx.text("SME Lending Queue", size="2", color="#94A3B8"),
            spacing="2",
            align="center",
        ),
        rx.hstack(
            rx.icon("calendar", size=14, color="#64748B"),
            rx.text("Submitted Sep 22, 2026", size="1", color="#94A3B8"),
            rx.text("·", size="1", color="#64748B"),
            rx.text("Reviewer: Credit Risk Officer", size="1", color="#94A3B8"),
            spacing="2",
            align="center",
        ),
        justify="between",
        width="100%",
        padding_y="2",
        padding_x="6",
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
    """Hàng 4 nút quyết định phê duyệt bên dưới[cite: 1]."""
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


def header_view() -> rx.Component:
    """Component Header hoàn chỉnh bọc ngoài[cite: 1]."""
    return rx.vstack(
        breadcrumb_bar(),
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
            padding_x="6",
            padding_y="4",
            width="100%",
            background="#090D16",
        ),
        width="100%",
        spacing="0",
    )