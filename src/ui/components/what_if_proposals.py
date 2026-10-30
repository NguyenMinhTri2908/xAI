"""
UI SUB-COMPONENT: AI RESTRUCTURING PROPOSALS & ACTION CONTROLS
==============================================================
Chứa các thẻ hiển thị phương án cơ cấu nợ AI:
- Thẻ chính: Recommended Proposal
- Nút kích hoạt Lazy Loading: Alternative Options Trigger
- Thẻ kịch bản phụ: Secondary Scenario Cards (Shortest Tenure, Balanced Compromise)
- Khối nút tác vụ: [ Reset to Baseline ] và [ AI Auto-Optimize ]
"""

import reflex as rx
from src.state import UnderwritingState


def scenario_metrics_grid(opt: rx.Var[dict], is_primary: bool = False) -> rx.Component:
    """Lưới thông số 2 cột độc lập chuẩn CSS Grid, tách biệt giá trị và delta theo chiều dọc chống chồng chữ."""
    val_size = "4" if is_primary else "3"

    return rx.box(
        # Ô 1: PROPOSED CREDIT
        rx.vstack(
            rx.text(
                "PROPOSED CREDIT",
                size="1",
                color="#64748B",
                style={
                    "font_size": "10px",
                    "font_weight": "600",
                    "letter_spacing": "0.05em",
                    "white_space": "nowrap",
                },
            ),
            rx.text(
                opt["credit_display"],
                size=val_size,
                weight="bold",
                color="#38BDF8",
                font_family="monospace",
                style={"white_space": "nowrap"},
            ),
            rx.cond(
                opt["credit_delta_text"] != "",
                rx.text(
                    opt["credit_delta_text"],
                    size="1",
                    weight="medium",
                    color=opt["credit_delta_color"],
                    font_family="monospace",
                    style={"white_space": "nowrap", "font_size": "11px"},
                ),
                rx.fragment(),
            ),
            spacing="0",
            align_items="flex-start",
            min_width="0",
        ),

        # Ô 2: PROPOSED TENURE
        rx.vstack(
            rx.text(
                "PROPOSED TENURE",
                size="1",
                color="#64748B",
                style={
                    "font_size": "10px",
                    "font_weight": "600",
                    "letter_spacing": "0.05em",
                    "white_space": "nowrap",
                },
            ),
            rx.text(
                opt["term_display"],
                size=val_size,
                weight="bold",
                color="#F8FAFC",
                font_family="monospace",
                style={"white_space": "nowrap"},
            ),
            rx.cond(
                opt["term_delta_text"] != "",
                rx.text(
                    opt["term_delta_text"],
                    size="1",
                    weight="medium",
                    color=opt["term_delta_color"],
                    font_family="monospace",
                    style={"white_space": "nowrap", "font_size": "11px"},
                ),
                rx.fragment(),
            ),
            spacing="0",
            align_items="flex-start",
            min_width="0",
        ),

        # Ô 3: PROPOSED ANNUITY
        rx.vstack(
            rx.text(
                "PROPOSED ANNUITY",
                size="1",
                color="#64748B",
                style={
                    "font_size": "10px",
                    "font_weight": "600",
                    "letter_spacing": "0.05em",
                    "white_space": "nowrap",
                },
            ),
            rx.text(
                opt["annuity_display"],
                size=val_size,
                weight="bold",
                color=opt["annuity_val_color"],
                font_family="monospace",
                style={"white_space": "nowrap"},
            ),
            rx.cond(
                opt["annuity_delta_text"] != "",
                rx.text(
                    opt["annuity_delta_text"],
                    size="1",
                    weight="medium",
                    color=opt["annuity_delta_color"],
                    font_family="monospace",
                    style={"white_space": "nowrap", "font_size": "11px"},
                ),
                rx.fragment(),
            ),
            spacing="0",
            align_items="flex-start",
            min_width="0",
        ),

        # Ô 4: NEW DTI RATIO
        rx.vstack(
            rx.text(
                "NEW DTI RATIO",
                size="1",
                color="#64748B",
                style={
                    "font_size": "10px",
                    "font_weight": "600",
                    "letter_spacing": "0.05em",
                    "white_space": "nowrap",
                },
            ),
            rx.text(
                opt["dti_display"],
                size=val_size,
                weight="bold",
                color=opt["dti_val_color"],
                font_family="monospace",
                style={"white_space": "nowrap"},
            ),
            rx.cond(
                opt["dti_delta_text"] != "",
                rx.text(
                    opt["dti_delta_text"],
                    size="1",
                    weight="medium",
                    color=opt["dti_delta_color"],
                    font_family="monospace",
                    style={"white_space": "nowrap", "font_size": "11px"},
                ),
                rx.fragment(),
            ),
            spacing="0",
            align_items="flex-start",
            min_width="0",
        ),
        display="grid",
        grid_template_columns="1fr 1fr",
        gap="12px",
        width="100%",
    )


def recommended_proposal_card(opt: rx.Var[dict]) -> rx.Component:
    """Card kịch bản AI chính: Recommended Proposal."""
    return rx.box(
        rx.vstack(
            # Header: Sparkles icon + Tiêu đề Recommended Proposal
            rx.hstack(
                rx.icon("sparkles", size=18, color="#A78BFA"),
                rx.text(
                    "Recommended Proposal",
                    size="3",
                    weight="bold",
                    color="#F8FAFC",
                    style={"font_size": "15px", "font_weight": "600"},
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            # Lưới thông số 2x2
            scenario_metrics_grid(opt, is_primary=True),
            # Divider phân tách
            rx.divider(border_color="#1E293B", margin_y="1"),
            # Khối Predicted PD & Offered Rate RBP
            rx.hstack(
                rx.vstack(
                    rx.text(
                        "PREDICTED PD",
                        size="1",
                        color="#64748B",
                        style={"font_size": "10px", "font_weight": "600", "letter_spacing": "0.05em", "white_space": "nowrap"},
                    ),
                    rx.hstack(
                        rx.text(
                            opt["pd_display"],
                            size="5",
                            weight="bold",
                            color="#34D399",
                            font_family="monospace",
                            style={"white_space": "nowrap", "letter_spacing": "-0.02em", "font_size": "20px"},
                        ),
                        rx.cond(
                            opt["pd_delta_text"] != "",
                            rx.text(
                                opt["pd_delta_text"],
                                size="1",
                                weight="bold",
                                color=opt["pd_delta_color"],
                                font_family="monospace",
                                style={"white_space": "nowrap", "font_size": "12px"},
                            ),
                            rx.fragment(),
                        ),
                        align="baseline",
                        spacing="1",
                    ),
                    spacing="1",
                    align_items="flex-start",
                    flex="1",
                ),
                rx.box(width="1px", height="32px", background="#1E293B"),
                rx.vstack(
                    rx.text(
                        "OFFERED RATE (RBP)",
                        size="1",
                        color="#64748B",
                        style={"font_size": "10px", "font_weight": "600", "letter_spacing": "0.05em", "white_space": "nowrap"},
                    ),
                    rx.hstack(
                        rx.text(
                            opt["rate_display"],
                            size="5",
                            weight="bold",
                            color="#38BDF8",
                            font_family="monospace",
                            style={"white_space": "nowrap", "letter_spacing": "-0.02em", "font_size": "20px"},
                        ),
                        rx.cond(
                            opt["rate_delta_text"] != "",
                            rx.text(
                                opt["rate_delta_text"],
                                size="1",
                                weight="bold",
                                color=opt["rate_delta_color"],
                                font_family="monospace",
                                style={"white_space": "nowrap", "font_size": "12px"},
                            ),
                            rx.fragment(),
                        ),
                        align="baseline",
                        spacing="1",
                    ),
                    spacing="1",
                    align_items="flex-start",
                    flex="1",
                    padding_left="2",
                ),
                width="100%",
                align="center",
            ),
            # Nút Apply Recommended Proposal
            rx.button(
                "Apply Recommended Proposal",
                size="3",
                variant="solid",
                width="100%",
                cursor="pointer",
                style={
                    "background": "linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)",
                    "color": "#FFFFFF",
                    "font_weight": "600",
                    "font_size": "14px",
                    "border_radius": "8px",
                    "height": "40px",
                    "box_shadow": "0 2px 10px rgba(99, 102, 241, 0.3)",
                    "transition": "all 0.15s ease",
                    "_hover": {
                        "filter": "brightness(1.1)",
                        "box_shadow": "0 4px 14px rgba(99, 102, 241, 0.4)",
                    },
                },
                on_click=UnderwritingState.apply_optimization_option(opt),
            ),
            spacing="3",
            width="100%",
        ),
        padding="4",
        background="#0D1322",
        border="1px solid #1E293B",
        border_radius="12px",
        width="100%",
        box_shadow="0 4px 12px rgba(0, 0, 0, 0.3)",
    )


def alternative_options_trigger() -> rx.Component:
    """Nút đóng/mở (Collapsible Trigger) cho các phương án thay thế với hiệu ứng Lazy Loading."""
    return rx.button(
        rx.cond(
            UnderwritingState.is_loading_alternatives,
            rx.hstack(
                rx.spinner(size="1"),
                rx.text(
                    "Calculating alternative suggestions...",
                    size="2",
                    weight="medium",
                    color="#A78BFA",
                    style={"font_size": "13px"},
                ),
                spacing="2",
                align="center",
                justify="center",
            ),
            rx.hstack(
                rx.text(
                    rx.cond(
                        UnderwritingState.show_alternative_options,
                        "Hide alternative suggestions",
                        "Show more suggestions",
                    ),
                    size="2",
                    weight="medium",
                    color="#94A3B8",
                    style={"font_size": "13px"},
                ),
                rx.icon(
                    rx.cond(
                        UnderwritingState.show_alternative_options,
                        "chevron-up",
                        "chevron-down",
                    ),
                    size=14,
                    color="#94A3B8",
                ),
                spacing="2",
                align="center",
                justify="center",
            ),
        ),
        variant="surface",
        color_scheme="gray",
        width="100%",
        cursor="pointer",
        disabled=UnderwritingState.is_loading_alternatives,
        on_click=UnderwritingState.toggle_alternative_options,
        style={
            "background": "#0F172A",
            "border": "1px solid #1E293B",
            "border_radius": "8px",
            "height": "36px",
            "color": "#94A3B8",
            "transition": "all 0.15s ease",
            "_hover": {
                "background": "#1E293B",
                "color": "#F8FAFC",
                "border_color": "#334155",
            },
        },
    )


def secondary_scenario_card(opt: rx.Var[dict]) -> rx.Component:
    """Card hiển thị 1 kịch bản phụ (Shortest Tenure, Balanced Compromise)."""
    return rx.box(
        rx.vstack(
            # 1. Header trên cùng 1 hàng: Tiêu đề (trái) + Nút [Apply Option] (phải)
            rx.hstack(
                rx.text(
                    opt["title"],
                    size="2",
                    weight="bold",
                    color="#F8FAFC",
                    style={"font_weight": "600", "font_size": "14px", "white_space": "nowrap"},
                ),
                rx.button(
                    "Apply Option",
                    size="1",
                    variant="surface",
                    cursor="pointer",
                    style={
                        "background": "#1E293B",
                        "border": "1px solid #334155",
                        "color": "#F8FAFC",
                        "font_size": "11px",
                        "font_weight": "500",
                        "padding": "0 10px",
                        "height": "26px",
                        "border_radius": "6px",
                        "transition": "all 0.15s ease",
                        "_hover": {
                            "background": "#334155",
                            "border_color": "#475569",
                        },
                    },
                    on_click=UnderwritingState.apply_optimization_option(opt),
                ),
                width="100%",
                justify="between",
                align="center",
            ),
            # 2. Lưới thông số 2x2
            scenario_metrics_grid(opt, is_primary=False),
            # 3. Chân thẻ hiển thị rủi ro (PREDICTED PD & OFFERED RATE)
            rx.hstack(
                rx.hstack(
                    rx.text(
                        "PREDICTED PD",
                        size="1",
                        color="#64748B",
                        style={
                            "font_size": "10px",
                            "font_weight": "600",
                            "letter_spacing": "0.05em",
                            "white_space": "nowrap",
                        },
                    ),
                    rx.text(
                        opt["pd_display"],
                        size="2",
                        weight="bold",
                        color=opt["pd_color"],
                        font_family="monospace",
                        style={"white_space": "nowrap"},
                    ),
                    rx.cond(
                        opt["pd_delta_text"] != "",
                        rx.text(
                            opt["pd_delta_text"],
                            size="1",
                            weight="medium",
                            color=opt["pd_delta_color"],
                            font_family="monospace",
                            style={"white_space": "nowrap"},
                        ),
                        rx.fragment(),
                    ),
                    align="baseline",
                    spacing="1",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.text(
                        "RATE",
                        size="1",
                        color="#64748B",
                        style={
                            "font_size": "10px",
                            "font_weight": "600",
                            "letter_spacing": "0.05em",
                            "white_space": "nowrap",
                        },
                    ),
                    rx.text(
                        opt["rate_display"],
                        size="2",
                        weight="bold",
                        color="#38BDF8",
                        font_family="monospace",
                        style={"white_space": "nowrap"},
                    ),
                    align="baseline",
                    spacing="1",
                ),
                align="center",
                width="100%",
                padding_top="1",
                style={"white_space": "nowrap"},
            ),
            spacing="3",
            width="100%",
        ),
        padding="3.5",
        background="#0D1322",
        border="1px solid #1E293B",
        border_radius="10px",
        width="100%",
        box_shadow="0 2px 4px rgba(0, 0, 0, 0.2)",
    )


# Alias tương thích ngược
optimization_scenario_card = secondary_scenario_card


def compact_alternative_card(opt: rx.Var[dict]) -> rx.Component:
    """Card hiển thị 1 kịch bản phụ compact theo thứ hạng (Option #2, Option #3...)."""
    return rx.box(
        rx.vstack(
            # Hàng 1: Badge Thứ hạng + PD + Rate (trái) | Nút [Apply] (phải)
            rx.hstack(
                rx.hstack(
                    rx.badge(
                        opt["title"],
                        size="1",
                        variant="surface",
                        color_scheme="indigo",
                        style={"font_weight": "600", "font_size": "11px"},
                    ),
                    rx.hstack(
                        rx.text("PD:", size="1", color="#64748B", style={"font_size": "11px"}),
                        rx.text(
                            opt["pd_display"],
                            size="1",
                            weight="bold",
                            color=opt["pd_color"],
                            font_family="monospace",
                        ),
                        spacing="1",
                        align="center",
                    ),
                    rx.hstack(
                        rx.text("Rate:", size="1", color="#64748B", style={"font_size": "11px"}),
                        rx.text(
                            opt["rate_display"],
                            size="1",
                            weight="bold",
                            color="#38BDF8",
                            font_family="monospace",
                        ),
                        spacing="1",
                        align="center",
                    ),
                    spacing="3",
                    align="center",
                ),
                rx.button(
                    "Apply",
                    size="1",
                    variant="surface",
                    cursor="pointer",
                    style={
                        "background": "#1E293B",
                        "border": "1px solid #334155",
                        "color": "#F8FAFC",
                        "font_size": "11px",
                        "font_weight": "600",
                        "padding": "0 10px",
                        "height": "24px",
                        "border_radius": "6px",
                        "transition": "all 0.15s ease",
                        "_hover": {
                            "background": "#334155",
                            "border_color": "#6366F1",
                            "color": "#FFFFFF",
                        },
                    },
                    on_click=UnderwritingState.apply_optimization_option(opt),
                ),
                width="100%",
                justify="between",
                align="center",
            ),
            # Hàng 2: Grid 4 thông số: Credit, Term, Annuity, DTI
            rx.box(
                # Ô 1: Credit
                rx.hstack(
                    rx.text("Credit:", size="1", color="#64748B", style={"font_size": "11px"}),
                    rx.text(
                        opt["credit_display"],
                        size="1",
                        weight="bold",
                        color="#38BDF8",
                        font_family="monospace",
                    ),
                    rx.cond(
                        opt["credit_delta_text"] != "",
                        rx.text(
                            opt["credit_delta_text"],
                            size="1",
                            color=opt["credit_delta_color"],
                            font_family="monospace",
                            style={"font_size": "10px"},
                        ),
                        rx.fragment(),
                    ),
                    spacing="1",
                    align="baseline",
                ),
                # Ô 2: Tenure
                rx.hstack(
                    rx.text("Term:", size="1", color="#64748B", style={"font_size": "11px"}),
                    rx.text(
                        opt["term_display"],
                        size="1",
                        weight="bold",
                        color="#F8FAFC",
                        font_family="monospace",
                    ),
                    rx.cond(
                        opt["term_delta_text"] != "",
                        rx.text(
                            opt["term_delta_text"],
                            size="1",
                            color=opt["term_delta_color"],
                            font_family="monospace",
                            style={"font_size": "10px"},
                        ),
                        rx.fragment(),
                    ),
                    spacing="1",
                    align="baseline",
                ),
                # Ô 3: Annuity
                rx.hstack(
                    rx.text("Annuity:", size="1", color="#64748B", style={"font_size": "11px"}),
                    rx.text(
                        opt["annuity_display"],
                        size="1",
                        weight="bold",
                        color=opt["annuity_val_color"],
                        font_family="monospace",
                    ),
                    rx.cond(
                        opt["annuity_delta_text"] != "",
                        rx.text(
                            opt["annuity_delta_text"],
                            size="1",
                            color=opt["annuity_delta_color"],
                            font_family="monospace",
                            style={"font_size": "10px"},
                        ),
                        rx.fragment(),
                    ),
                    spacing="1",
                    align="baseline",
                ),
                # Ô 4: DTI
                rx.hstack(
                    rx.text("DTI:", size="1", color="#64748B", style={"font_size": "11px"}),
                    rx.text(
                        opt["dti_display"],
                        size="1",
                        weight="bold",
                        color=opt["dti_val_color"],
                        font_family="monospace",
                    ),
                    rx.cond(
                        opt["dti_delta_text"] != "",
                        rx.text(
                            opt["dti_delta_text"],
                            size="1",
                            color=opt["dti_delta_color"],
                            font_family="monospace",
                            style={"font_size": "10px"},
                        ),
                        rx.fragment(),
                    ),
                    spacing="1",
                    align="baseline",
                ),
                display="grid",
                grid_template_columns="repeat(2, 1fr)",
                gap="6px",
                width="100%",
                padding_top="1",
            ),
            spacing="1",
            width="100%",
        ),
        padding="2.5",
        background="#0A0F1D",
        border="1px solid #1E293B",
        border_radius="8px",
        width="100%",
        box_shadow="0 1px 3px rgba(0, 0, 0, 0.2)",
    )


def optimal_baseline_alert() -> rx.Component:
    """Card thông báo khi hồ sơ ban đầu đã đạt chuẩn phê duyệt (Approved) - Không yêu cầu tái cơ cấu."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("circle-check", size=18, color="#10B981"),
                    rx.text(
                        "Hồ sơ đạt chuẩn phê duyệt",
                        size="2",
                        weight="bold",
                        color="#10B981",
                        style={"font_size": "13px"},
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon("x", size=12),
                    variant="ghost",
                    size="1",
                    color_scheme="gray",
                    on_click=UnderwritingState.close_optimization_results,
                    cursor="pointer",
                    style={"color": "#64748B", "_hover": {"color": "#F8FAFC"}},
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                "✓ Hồ sơ đạt chuẩn: Các chỉ số rủi ro (PD, DTI) của khách hàng đang nằm hoàn toàn trong ngưỡng an toàn. "
                "Khuyến nghị giữ nguyên điều kiện hợp đồng ban đầu, không yêu cầu tái cơ cấu.",
                size="1",
                color="#94A3B8",
                style={"font_size": "12px", "line_height": "1.5"},
            ),
            spacing="2",
            width="100%",
        ),
        padding="3.5",
        background="rgba(16, 185, 129, 0.08)",
        border="1px solid rgba(16, 185, 129, 0.25)",
        border_radius="8px",
        width="100%",
        margin_top="1",
    )


def action_footer_controls() -> rx.Component:
    """Khối tác vụ chân bảng: [ Reset to Baseline ] và [ AI Auto-Optimize ]."""
    return rx.hstack(
        rx.spacer(min_width="0", flex="1"),
        # [ Reset to Baseline ] (Ghost/Outline style với icon ↺)
        rx.button(
            rx.hstack(
                rx.icon("rotate-ccw", size=14),
                rx.text("Reset to Baseline", size="2", weight="medium"),
                spacing="2",
                align="center",
            ),
            size="2",
            variant="outline",
            color_scheme="gray",
            cursor="pointer",
            style={
                "border": "1px solid #334155",
                "color": "#CBD5E1",
                "background": "transparent",
                "transition": "all 0.15s ease",
                "_hover": {
                    "background": "rgba(30, 41, 59, 0.7)",
                    "border-color": "#475569",
                    "color": "#F8FAFC",
                },
            },
            on_click=UnderwritingState.reset_simulation_to_baseline,
        ),
        # [ AI Auto-Optimize ] (Primary Accent Gradient style với icon ✦ kèm loading spinner)
        rx.button(
            rx.cond(
                UnderwritingState.is_optimizing,
                rx.hstack(
                    rx.spinner(size="1", color="white"),
                    rx.text("Optimizing...", size="2", weight="bold"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.icon("sparkles", size=14),
                    rx.text("AI Auto-Optimize", size="2", weight="bold"),
                    spacing="2",
                    align="center",
                ),
            ),
            size="2",
            variant="solid",
            cursor="pointer",
            disabled=UnderwritingState.is_optimizing,
            style={
                "background": "linear-gradient(135deg, #7C3AED 0%, #2563EB 100%)",
                "color": "white",
                "box_shadow": "0 2px 10px rgba(124, 58, 237, 0.4)",
                "transition": "all 0.15s ease",
                "_hover": {
                    "box_shadow": "0 4px 16px rgba(124, 58, 237, 0.6)",
                    "filter": "brightness(1.08)",
                },
            },
            id="ai_auto_optimize_btn",
            on_click=UnderwritingState.ai_auto_optimize,
        ),
        width="100%",
        min_width="0",
        align="center",
        spacing="3",
    )


def ai_optimization_section() -> rx.Component:
    """Toàn bộ vùng hiển thị kết quả tái cơ cấu AI:
    - Khi hồ sơ đã Approved: Hiện Optimal Baseline Alert.
    - Khi hồ sơ Declined được cứu: Hiện Recommended Proposal (Top 1) + Danh sách phẳng Alternatives + Nút Show more.
    - Khi không thể cứu: Hiện thông báo No restructuring terms meet risk criteria.
    """
    return rx.cond(
        UnderwritingState.show_optimization_results,
        rx.cond(
            UnderwritingState.is_baseline_optimal,
            optimal_baseline_alert(),
            rx.cond(
                UnderwritingState.optimization_options.length() > 0,
                rx.vstack(
                    # 1. Thẻ chính: Recommended Proposal (Top 1)
                    recommended_proposal_card(UnderwritingState.recommended_option),

                    # 2. Danh sách phương án thay thế (Top 2, Top 3...) dạng phẳng không lồng scroll container
                    rx.cond(
                        UnderwritingState.alternative_options.length() > 0,
                        rx.vstack(
                            rx.hstack(
                                rx.text(
                                    "ALTERNATIVE FEASIBLE OPTIONS",
                                    size="1",
                                    weight="bold",
                                    color="#64748B",
                                    style={"font_size": "10px", "letter_spacing": "0.05em", "font_weight": "600"},
                                ),
                                rx.spacer(),
                                rx.badge(
                                    UnderwritingState.visible_proposals_count_display,
                                    size="1",
                                    variant="surface",
                                    color_scheme="gray",
                                    style={"font_size": "10px"},
                                ),
                                width="100%",
                                align="center",
                                padding_top="1",
                            ),
                            rx.foreach(
                                UnderwritingState.visible_alternative_options,
                                compact_alternative_card,
                            ),
                            # 3. Nút Show more alternatives
                            rx.cond(
                                UnderwritingState.has_more_proposals,
                                rx.button(
                                    rx.hstack(
                                        rx.icon("chevron-down", size=14),
                                        rx.text("Show more alternatives", size="1", weight="medium"),
                                        spacing="1",
                                        align="center",
                                    ),
                                    on_click=UnderwritingState.show_more_proposals,
                                    variant="ghost",
                                    color_scheme="gray",
                                    size="1",
                                    cursor="pointer",
                                    width="100%",
                                    style={
                                        "color": "#94A3B8",
                                        "border": "1px dashed #334155",
                                        "border_radius": "6px",
                                        "height": "28px",
                                        "margin_top": "2px",
                                        "transition": "all 0.15s ease",
                                        "_hover": {
                                            "background": "#1E293B",
                                            "color": "#F8FAFC",
                                            "border_color": "#6366F1",
                                        },
                                    },
                                ),
                                rx.fragment(),
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    spacing="3",
                    width="100%",
                    margin_top="1",
                ),
                # Khi không có phương án nào thỏa mãn
                rx.box(
                    rx.hstack(
                        rx.icon("info", size=16, color="#F59E0B"),
                        rx.text(
                            "No restructuring terms meet the risk appetite criteria for this client within standard loan bounds.",
                            size="1",
                            color="#F59E0B",
                            weight="medium",
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.icon("x", size=12),
                            variant="ghost",
                            size="1",
                            color_scheme="gray",
                            on_click=UnderwritingState.close_optimization_results,
                            cursor="pointer",
                        ),
                        spacing="2",
                        align="center",
                        width="100%",
                    ),
                    padding="3",
                    background="rgba(245, 158, 11, 0.08)",
                    border="1px solid rgba(245, 158, 11, 0.25)",
                    border_radius="8px",
                    width="100%",
                    margin_top="2",
                ),
            ),
        ),
        rx.fragment(),
    )

