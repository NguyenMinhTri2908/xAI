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
    """Card 1 (Trái): Profile thông tin nhân thân."""
    return rx.box(
        rx.vstack(
            # Hàng Avatar + Tên + Mã ID + Badges[cite: 1]
            rx.hstack(
                rx.avatar(
                    fallback=rx.cond(
                        UnderwritingState.selected_client_raw.get("NAME", "") != "",
                        UnderwritingState.client_initials,
                        "NT",
                    ),
                    size="4",
                    radius="full",
                    color_scheme="gray",
                    variant="solid",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.heading(
                            rx.cond(
                                UnderwritingState.selected_client_raw.get("NAME", "") != "",
                                UnderwritingState.selected_client_raw.get("NAME"),
                                "Nguyen Minh Tuan",
                            ),
                            size="3",
                            weight="bold",
                            color="white",
                        ),
                        rx.badge(
                            rx.cond(
                                UnderwritingState.selected_client_id != "",
                                f"#{UnderwritingState.selected_client_id}",
                                "#LN-2026-8891",
                            ),
                            variant="surface",
                            color_scheme="gray",
                            size="1",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.badge(
                            rx.cond(
                                UnderwritingState.current_tier != "N/A",
                                f"Low-Medium Risk · {UnderwritingState.current_tier}",
                                "Low-Medium Risk · Tier B2",
                            ),
                            color_scheme="green",
                            variant="surface",
                            size="1",
                            radius="full",
                        ),
                        rx.badge(
                            "High Confidence · 91%",
                            color_scheme="gray",
                            variant="surface",
                            size="1",
                            radius="full",
                        ),
                        spacing="2",
                    ),
                    spacing="1",
                    align_items="flex-start",
                ),
                spacing="3",
                align="center",
                width="100%",
            ),
            rx.divider(border_color="#1E293B", margin_y="2"),
            # Grid 2x2: AGE, OCCUPATION, EXPERIENCE, RESIDENCE[cite: 1]
            rx.grid(
                rx.vstack(
                    rx.text("AGE", size="1", color="#64748B", weight="bold"),
                    rx.text(
                        rx.cond(
                            UnderwritingState.selected_client_raw.get("AGE", "") != "",
                            UnderwritingState.selected_client_raw.get("AGE"),
                            "28 years old",
                        ),
                        size="2",
                        weight="bold",
                        color="#F8FAFC",
                    ),
                    spacing="0",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("OCCUPATION", size="1", color="#64748B", weight="bold"),
                    rx.text(
                        rx.cond(
                            UnderwritingState.selected_client_raw.get("OCCUPATION", "") != "",
                            UnderwritingState.selected_client_raw.get("OCCUPATION"),
                            "SME Business Owner",
                        ),
                        size="2",
                        weight="bold",
                        color="#F8FAFC",
                    ),
                    spacing="0",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("EXPERIENCE / TENURE", size="1", color="#64748B", weight="bold"),
                    rx.text(
                        rx.cond(
                            UnderwritingState.selected_client_raw.get("EXPERIENCE", "") != "",
                            UnderwritingState.selected_client_raw.get("EXPERIENCE"),
                            "3.5 years",
                        ),
                        size="2",
                        weight="bold",
                        color="#F8FAFC",
                    ),
                    spacing="0",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("RESIDENCE", size="1", color="#64748B", weight="bold"),
                    rx.text(
                        rx.cond(
                            UnderwritingState.selected_client_raw.get("RESIDENCE", "") != "",
                            UnderwritingState.selected_client_raw.get("RESIDENCE"),
                            "Homeowner (4 years)",
                        ),
                        size="2",
                        weight="bold",
                        color="#F8FAFC",
                    ),
                    spacing="0",
                    align_items="flex-start",
                ),
                columns="2",
                spacing="3",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        background="#161B22",
        border="1px solid #21262D",
        border_radius="10px",
        padding="4",
        width="34%",
    )


def loan_terms_card() -> rx.Component:
    """Card 2 (Giữa): LOAN TERMS[cite: 1]."""
    return rx.box(
        rx.vstack(
            rx.text("LOAN TERMS", size="1", color="#64748B", weight="bold"),
            rx.grid(
                rx.vstack(
                    rx.text("REQUESTED AMOUNT", size="1", color="#94A3B8", weight="bold"),
                    rx.text(
                        rx.cond(
                            UnderwritingState.selected_client_raw.get("Credit", "") != "",
                            UnderwritingState.selected_client_raw.get("Credit"),
                            "$25,000",
                        ),
                        size="5",
                        weight="bold",
                        color="#F8FAFC",
                    ),
                    spacing="0",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("LOAN TERM", size="1", color="#94A3B8", weight="bold"),
                    rx.text(
                        rx.cond(
                            UnderwritingState.selected_client_raw.get("TERM", "") != "",
                            UnderwritingState.selected_client_raw.get("TERM"),
                            "24 months",
                        ),
                        size="5",
                        weight="bold",
                        color="#F8FAFC",
                    ),
                    spacing="0",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("EST. MONTHLY PAYMENT", size="1", color="#94A3B8", weight="bold"),
                    rx.text(
                        rx.cond(
                            UnderwritingState.selected_client_raw.get("Annuity", "") != "",
                            UnderwritingState.selected_client_raw.get("Annuity"),
                            "~$1.042 / month",
                        ),
                        size="3",
                        weight="bold",
                        color="#F8FAFC",
                    ),
                    spacing="0",
                    align_items="flex-start",
                ),
                rx.vstack(
                    rx.text("LOAN PURPOSE", size="1", color="#94A3B8", weight="bold"),
                    rx.hstack(
                        rx.icon("building", size=14, color="#94A3B8"),
                        rx.text(
                            rx.cond(
                                UnderwritingState.selected_client_raw.get("PURPOSE", "") != "",
                                UnderwritingState.selected_client_raw.get("PURPOSE"),
                                "SME Business Expansion",
                            ),
                            size="2",
                            weight="bold",
                            color="#F8FAFC",
                        ),
                        spacing="1",
                        align="center",
                    ),
                    spacing="0",
                    align_items="flex-start",
                ),
                columns="2",
                spacing="3",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        background="#161B22",
        border="1px solid #21262D",
        border_radius="10px",
        padding="4",
        width="34%",
    )


def ai_recommendation_card() -> rx.Component:
    """Card 3 (Phải): AI RECOMMENDATION ENGINE + SUGGESTED ACTION[cite: 1]."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("cpu", size=15, color="#F8FAFC"),
                    rx.text(
                        "AI RECOMMENDATION ENGINE",
                        size="1",
                        weight="bold",
                        color="#94A3B8",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.badge("91% Confidence", color_scheme="gray", variant="surface", size="1", radius="full"),
                justify="between",
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.text(
                    rx.cond(
                        UnderwritingState.current_score_percent > 0,
                        f"PD: {UnderwritingState.current_score_percent}%",
                        "PD: 4.8%",
                    ),
                    size="5",
                    weight="bold",
                    color="#10B981",
                ),
                align="center",
            ),
            rx.text("12-Month Probability of Default", size="1", color="#64748B"),
            # Hộp Suggested Action viền cam đậm giống thiết kế[cite: 1]
            rx.box(
                rx.vstack(
                    rx.text("SUGGESTED ACTION", size="1", weight="bold", color="#F59E0B"),
                    rx.heading(
                        rx.cond(
                            UnderwritingState.current_decision != "PENDING",
                            UnderwritingState.current_decision,
                            "Conditional Approval",
                        ),
                        size="3",
                        weight="bold",
                        color="#FCD34D",
                    ),
                    rx.text("Cap at $20,000 or reduce tenor", size="1", color="#D97706"),
                    spacing="1",
                    align_items="flex-start",
                ),
                background="#1C150A",
                border="1px solid #78350F",
                border_radius="8px",
                padding="3",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        background="#161B22",
        border="1px solid #21262D",
        border_radius="10px",
        padding="4",
        width="32%",
    )


def action_bar_view() -> rx.Component:
    """Hàng 4 nút quyết định phê duyệt bên dưới[cite: 1]."""
    return rx.hstack(
        rx.button(
            rx.icon("check-circle", size=16),
            "Approve",
            background="#059669",
            color="white",
            size="2",
            radius="medium",
            cursor="pointer",
        ),
        rx.button(
            rx.icon("x-circle", size=16),
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
                    spacing="3",
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