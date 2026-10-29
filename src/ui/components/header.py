import reflex as rx
from src.state import UnderwritingState


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


def recommendation_card() -> rx.Component:
    """Card 3 (Phải): Recommendation (PD & Offered Rate RBP kèm Credit Decision Badge)."""
    return rx.card(
        rx.vstack(
            # Header: Tiêu đề "Recommendation" bên trái & Badge APPROVED/DECLINED sát mép phải
            rx.hstack(
                rx.hstack(
                    rx.icon("sparkles", size=16, color="#9CA3AF"),
                    rx.text(
                        "Recommendation",
                        size="3",
                        font_weight="600",
                        color="#9CA3AF",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.badge(
                    UnderwritingState.baseline_decision_status,
                    variant="surface",
                    color_scheme=rx.cond(
                        UnderwritingState.baseline_decision_status == "APPROVED",
                        "green",
                        "red",
                    ),
                    size="2",
                    style={
                        "color": UnderwritingState.baseline_decision_color,
                        "font_weight": "bold",
                        "font_family": "monospace",
                        "letter_spacing": "0.05em",
                    },
                ),
                width="100%",
                align="center",
            ),
            rx.divider(border_color="#1E293B", margin_y="1"),
            # Bố cục 2 cột song song cân xứng
            rx.hstack(
                # Cột bên trái — Xác suất vỡ nợ (Probability of Default - PD)
                rx.vstack(
                    rx.text("PROBABILITY OF DEFAULT", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        UnderwritingState.baseline_pd_display,
                        size="4",
                        weight="bold",
                        color="#FFFFFF",
                        font_family="monospace",
                    ),
                    spacing="1",
                    align_items="flex-start",
                    flex="1",
                ),
                # Vạch phân cách: Một đường kẻ dọc mờ tinh tế ngăn cách giữa hai cột
                rx.box(width="1px", height="32px", background="#1E293B", align_self="center"),
                # Cột bên phải — Lãi suất đề xuất (Offered Rate RBP)
                rx.vstack(
                    rx.text("OFFERED RATE (RBP)", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        UnderwritingState.baseline_rate_display,
                        size="4",
                        weight="bold",
                        color="#38BDF8",
                        font_family="monospace",
                    ),
                    spacing="1",
                    align_items="flex-start",
                    flex="1",
                    padding_left="3",
                ),
                width="100%",
                align="center",
                spacing="3",
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


ai_recommendation_card = recommendation_card



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