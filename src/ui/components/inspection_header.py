"""Component Header & Breadcrumb Bar cho màn hình Thẩm định chi tiết (Inspection Workbench)."""
import reflex as rx
from src.state import UnderwritingState


def inspection_breadcrumb_bar() -> rx.Component:
    """Thanh Breadcrumb tinh gọn với nút Back to Data Management và bộ chọn Client ID."""
    return rx.box(
        rx.box(
            rx.hstack(
                # CỤM TRÁI: NÚT BACK VÀ TIÊU ĐỀ
                rx.hstack(
                    rx.button(
                        rx.hstack(
                            rx.icon("arrow-left", size=14),
                            rx.text("Back to Data Management", size="1", weight="bold"),
                            spacing="1",
                            align="center",
                        ),
                        variant="outline",
                        color_scheme="gray",
                        size="1",
                        cursor="pointer",
                        on_click=rx.redirect("/data"),
                    ),
                    rx.divider(orientation="vertical", height="16px", border_color="#1F2937"),
                    # Nút mở Queue Drawer (Điều khiển qua State)
                    rx.button(
                        rx.hstack(
                            rx.icon("panel-left", size=14),
                            rx.text("Queue", size="1", weight="bold"),
                            spacing="1",
                            align="center",
                        ),
                        variant="surface",
                        color_scheme="gray",
                        size="1",
                        cursor="pointer",
                        on_click=UnderwritingState.open_queue_drawer,
                    ),
                    rx.divider(orientation="vertical", height="16px", border_color="#1F2937"),
                    rx.hstack(
                        rx.icon("landmark", size=14, color="#38BDF8"),
                        rx.text(
                            "Client Inspection Workbench",
                            size="2",
                            weight="bold",
                            color="#F8FAFC",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    spacing="3",
                    align="center",
                ),

                # CỤM PHẢI: BỘ CHỌN HỒ SƠ CLIENT DROPDOWN + NÚT PREV/NEXT
                rx.hstack(
                    rx.hstack(
                        rx.text("Inspect Client:", size="1", color="#94A3B8", weight="medium"),
                        rx.select.root(
                            rx.select.trigger(
                                placeholder="Choose Client ID...",
                                size="1",
                                width="150px",
                            ),
                            rx.select.content(
                                rx.select.group(
                                    rx.foreach(
                                        UnderwritingState.client_id_options,
                                        lambda cid: rx.select.item(cid, value=cid),
                                    ),
                                ),
                            ),
                            value=UnderwritingState.selected_client_id,
                            on_change=UnderwritingState.select_and_evaluate_client,
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.divider(orientation="vertical", height="16px", border_color="#1F2937"),
                    # Bộ nút phân trang từng hồ sơ
                    rx.hstack(
                        rx.button(
                            rx.icon("chevron-left", size=13),
                            size="1",
                            variant="ghost",
                            color_scheme="gray",
                            on_click=UnderwritingState.select_previous_client,
                            disabled=UnderwritingState.is_first_client,
                        ),
                        rx.button(
                            rx.icon("chevron-right", size=13),
                            size="1",
                            variant="ghost",
                            color_scheme="gray",
                            on_click=UnderwritingState.select_next_client,
                            disabled=UnderwritingState.is_last_client,
                        ),
                        rx.badge(
                            rx.cond(
                                UnderwritingState.total_clients_count == 1,
                                "1 of 1",
                                "#" + UnderwritingState.current_client_index_display + " of " + UnderwritingState.total_clients_count.to_string(),
                            ),
                            variant="surface",
                            color_scheme="gray",
                            size="1",
                        ),
                        spacing="1",
                        align="center",
                    ),
                    rx.divider(orientation="vertical", height="16px", border_color="#1F2937"),
                    rx.badge("System Online", color_scheme="green", variant="surface", size="1"),
                    spacing="3",
                    align="center",
                ),
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
            rx.hstack(
                rx.hstack(
                    rx.icon("user", size=16, color="#9CA3AF"),
                    rx.text(
                        rx.cond(
                            UnderwritingState.selected_client_id != "",
                            "ID: #" + UnderwritingState.selected_client_id,
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
            rx.hstack(
                rx.vstack(
                    rx.text("PROBABILITY OF DEFAULT", size="1", color="#9CA3AF", weight="medium"),
                    rx.text(
                        UnderwritingState.pd_display,
                        size="4",
                        weight="bold",
                        color="#FFFFFF",
                        font_family="monospace",
                    ),
                    spacing="1",
                    align_items="flex-start",
                    flex="1",
                ),
                rx.box(width="1px", height="32px", background="#1E293B", align_self="center"),
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
    """Hàng nút hành động quyết định phê duyệt."""
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


def full_inspection_header() -> rx.Component:
    """Header tổng thể của Trang Inspection Workbench."""
    return rx.box(
        inspection_breadcrumb_bar(),
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

