import reflex as rx
from src.ui.state import UnderwritingState


def term_preset_pill(months: int) -> rx.Component:
    """Nút Quick Preset Pill chọn nhanh thời hạn vay (3m, 6m, 12m, 24m, 36m, 48m, 60m)."""
    return rx.button(
        f"{months}m",
        size="1",
        variant=rx.cond(UnderwritingState.sim_term_months == months, "solid", "outline"),
        color_scheme=rx.cond(UnderwritingState.sim_term_months == months, "cyan", "gray"),
        on_click=UnderwritingState.set_sim_term_preset(months),
        cursor="pointer",
        style={
            "font_size": "11px",
            "padding": "0 9px",
            "height": "22px",
            "border_radius": "5px",
            "font_family": "monospace",
            "font_weight": "bold",
        },
    )


def scenario_metrics_grid(opt: rx.Var[dict], is_primary: bool = False) -> rx.Component:
    """Lưới thông số 2 cột độc lập chuẩn CSS Grid, tách biệt giá trị và delta theo chiều dọc chống chồng chữ."""
    val_size = "4" if is_primary else "3"

    return rx.box(
        # Ô 1: PROPOSED CREDIT
        rx.vstack(
            # Dòng 1: Nhãn in hoa nhỏ
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
            # Dòng 2: Giá trị chính (font monospace, in đậm, white_space="nowrap")
            rx.text(
                opt["credit_display"],
                size=val_size,
                weight="bold",
                color="#38BDF8",
                font_family="monospace",
                style={"white_space": "nowrap"},
            ),
            # Dòng 3: Nhãn delta chênh lệch nằm ngay phía dưới giá trị chính
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
        # Ô 2: TENURE
        rx.vstack(
            # Dòng 1: Nhãn in hoa nhỏ
            rx.text(
                "TENURE",
                size="1",
                color="#64748B",
                style={
                    "font_size": "10px",
                    "font_weight": "600",
                    "letter_spacing": "0.05em",
                    "white_space": "nowrap",
                },
            ),
            # Dòng 2: Giá trị chính
            rx.text(
                opt["term_display"],
                size=val_size,
                weight="bold",
                color="#F8FAFC",
                font_family="monospace",
                style={"white_space": "nowrap"},
            ),
            # Dòng 3: Nhãn delta chênh lệch
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
        # Ô 3: MONTHLY ANNUITY
        rx.vstack(
            # Dòng 1: Nhãn in hoa nhỏ
            rx.text(
                "MONTHLY ANNUITY",
                size="1",
                color="#64748B",
                style={
                    "font_size": "10px",
                    "font_weight": "600",
                    "letter_spacing": "0.05em",
                    "white_space": "nowrap",
                },
            ),
            # Dòng 2: Giá trị chính
            rx.text(
                opt["annuity_display"],
                size=val_size,
                weight="bold",
                color=opt["annuity_val_color"],
                font_family="monospace",
                style={"white_space": "nowrap"},
            ),
            # Dòng 3: Nhãn delta chênh lệch
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
        # Ô 4: DTI RATIO
        rx.vstack(
            # Dòng 1: Nhãn in hoa nhỏ
            rx.text(
                "DTI RATIO",
                size="1",
                color="#64748B",
                style={
                    "font_size": "10px",
                    "font_weight": "600",
                    "letter_spacing": "0.05em",
                    "white_space": "nowrap",
                },
            ),
            # Dòng 2: Giá trị chính
            rx.text(
                opt["dti_display"],
                size=val_size,
                weight="bold",
                color=opt["dti_val_color"],
                font_family="monospace",
                style={"white_space": "nowrap"},
            ),
            # Dòng 3: Nhãn delta chênh lệch
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
            # Khối Predicted PD
            rx.vstack(
                rx.text(
                    "Predicted PD",
                    size="2",
                    weight="bold",
                    color="#F8FAFC",
                    style={"font_size": "14px", "font_weight": "600"},
                ),
                rx.hstack(
                    rx.text(
                        opt["pd_display"],
                        size="6",
                        weight="bold",
                        color="#34D399",
                        font_family="monospace",
                        style={"white_space": "nowrap", "letter_spacing": "-0.02em", "font_size": "24px"},
                    ),
                    rx.cond(
                        opt["pd_delta_text"] != "",
                        rx.text(
                            opt["pd_delta_text"],
                            size="2",
                            weight="bold",
                            color=opt["pd_delta_color"],
                            font_family="monospace",
                            style={"white_space": "nowrap", "font_size": "14px"},
                        ),
                        rx.fragment(),
                    ),
                    align="baseline",
                    spacing="2",
                    style={"white_space": "nowrap"},
                ),
                spacing="1",
                align_items="flex-start",
                width="100%",
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
            # 3. Chân thẻ hiển thị rủi ro (PREDICTED PD)
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
                spacing="2",
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


def what_if_view() -> rx.Component:
    """Component Risk Mitigation & Terms Simulator theo phong cách Notion/Linear tối giản.
    Tập trung vào clean typography, low clutter, hiển thị 2 chỉ số cốt lõi và delta chênh lệch.
    """
    return rx.card(
        rx.vstack(
            # 1. HEADER KHỐI SIMULATOR ĐỒNG BỘ: Tiêu đề "Simulator" bên trái & Badge Quyết định mô phỏng bên phải
            rx.hstack(
                rx.text(
                    "Simulator",
                    size="3",
                    weight="bold",
                    color="#F8FAFC",
                    line_height="1.2",
                ),
                rx.badge(
                    UnderwritingState.sim_decision_status,
                    variant="surface",
                    color_scheme=rx.cond(
                        UnderwritingState.sim_decision_status == "APPROVED",
                        "green",
                        "red",
                    ),
                    size="2",
                    style={
                        "color": UnderwritingState.sim_decision_color,
                        "font_weight": "bold",
                        "font_family": "monospace",
                        "letter_spacing": "0.05em",
                    },
                ),
                justify="between",
                align="center",
                width="100%",
            ),

            # 2. METRICS CARD TÍCH HỢP DEFERRED CALCULATION & FEASIBILITY GUARDRAIL
            rx.box(
                rx.cond(
                    UnderwritingState.is_sim_calculating,
                    # Trạng thái chờ: Khi người dùng đang kéo slider
                    rx.hstack(
                        rx.spinner(size="2", color="#38BDF8"),
                        rx.text(
                            "Calculating terms & pricing...",
                            size="2",
                            color="#94A3B8",
                            font_family="monospace",
                            weight="medium",
                        ),
                        spacing="3",
                        align="center",
                        justify="center",
                        width="100%",
                        height="44px",
                    ),
                    # Trạng thái hiển thị 3 cột thông số cân đối
                    rx.vstack(
                        rx.hstack(
                            # Cột 1: Probability of Default (PD)
                            rx.vstack(
                                rx.text(
                                    "Probability of Default (PD)",
                                    size="1",
                                    color="#94A3B8",
                                    weight="medium",
                                ),
                                rx.cond(
                                    UnderwritingState.is_simulated_changed,
                                    # Trạng thái điều chỉnh (Simulated): hiển thị PD mới kèm delta
                                    rx.hstack(
                                        rx.text(
                                            UnderwritingState.pd_display_value,
                                            size="3",
                                            weight="bold",
                                            color="#F8FAFC",
                                            font_family="monospace",
                                        ),
                                        rx.cond(
                                            UnderwritingState.pd_delta_badge_text != "",
                                            rx.text(
                                                UnderwritingState.pd_delta_badge_text,
                                                size="1",
                                                weight="bold",
                                                color=UnderwritingState.pd_delta_color,
                                                font_family="monospace",
                                            ),
                                            rx.fragment(),
                                        ),
                                        spacing="2",
                                        align="center",
                                    ),
                                    # Trạng thái ban đầu: hiển thị baseline
                                    rx.hstack(
                                        rx.text(
                                            f"{UnderwritingState.baseline_score_percent:.2f}%",
                                            size="3",
                                            weight="bold",
                                            color="#F8FAFC",
                                            font_family="monospace",
                                        ),
                                        rx.text(
                                            "(Baseline)",
                                            size="1",
                                            color="#64748B",
                                            font_family="monospace",
                                        ),
                                        spacing="2",
                                        align="center",
                                    ),
                                ),
                                spacing="1",
                                align_items="flex-start",
                                flex="1",
                            ),
                            rx.box(width="1px", height="28px", background="#1E293B"),

                            # Cột 2: Offered Rate (RBP)
                            rx.vstack(
                                rx.text(
                                    "Offered Rate (RBP)",
                                    size="1",
                                    color="#94A3B8",
                                    weight="medium",
                                ),
                                rx.hstack(
                                    rx.text(
                                        UnderwritingState.sim_rate_display,
                                        size="3",
                                        weight="bold",
                                        color="#38BDF8",
                                        font_family="monospace",
                                    ),
                                    rx.cond(
                                        UnderwritingState.sim_rate_delta_text != "",
                                        rx.text(
                                            UnderwritingState.sim_rate_delta_text,
                                            size="1",
                                            weight="bold",
                                            color=UnderwritingState.sim_rate_delta_color,
                                            font_family="monospace",
                                        ),
                                        rx.fragment(),
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                spacing="1",
                                align_items="flex-start",
                                flex="1",
                                padding_left="4",
                            ),
                            rx.box(width="1px", height="28px", background="#1E293B"),

                            # Cột 3: DTI Ratio
                            rx.vstack(
                                rx.text(
                                    "DTI Ratio",
                                    size="1",
                                    color="#94A3B8",
                                    weight="medium",
                                ),
                                rx.text(
                                    UnderwritingState.sim_dti_display,
                                    size="3",
                                    weight="bold",
                                    color=rx.cond(UnderwritingState.sim_dti > 50.0, "#F59E0B", "#F8FAFC"),
                                    font_family="monospace",
                                ),
                                spacing="1",
                                align_items="flex-start",
                                flex="1",
                                padding_left="4",
                            ),
                            width="100%",
                            align="center",
                        ),
                        # Cảnh báo Feasibility Guardrail nếu DTI > 50%
                        rx.cond(
                            UnderwritingState.sim_dti > 50.0,
                            rx.hstack(
                                rx.icon("triangle-alert", size=13, color="#F59E0B"),
                                rx.text(
                                    "Warning: Monthly payment exceeds 50% DTI threshold",
                                    size="1",
                                    color="#F59E0B",
                                    font_family="monospace",
                                    weight="medium",
                                ),
                                spacing="1",
                                align="center",
                                padding_top="1",
                            ),
                            rx.fragment(),
                        ),
                        width="100%",
                        spacing="1",
                        align_items="flex-start",
                    ),
                ),
                width="100%",
                background="#0B0F19",
                border=rx.cond(
                    UnderwritingState.is_scenario_viable,
                    "1px solid #1E293B",
                    "1px solid #F59E0B",
                ),
                border_radius="8px",
                padding_x="4",
                padding_y="3",
                min_height="62px",
                display="flex",
                align_items="center",
            ),

            # 3. HYBRID CONTROLS: 4 BỘ ĐIỀU KHIỂN KÈM NHÃN DELTA CHÊNH LỆCH
            rx.vstack(
                # Lever 1: AMT_CREDIT (Số tiền vay)
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            # Khối nhãn bên trái (Tên biến + nhãn phụ) - flex_shrink="0"
                            rx.hstack(
                                rx.badge("AMT_CREDIT", color_scheme="blue", variant="surface", size="1", font_family="monospace"),
                                rx.text("Loan Amount", size="1", color="#9CA3AF", white_space="nowrap"),
                                spacing="2",
                                align="center",
                                flex_shrink="0",
                            ),
                            rx.spacer(min_width="0", flex="1"),
                            # Khối delta & input bên phải: Fixed Width - flex_shrink="0"
                            rx.hstack(
                                # Vùng chứa nhãn delta cố định width="70px" (Zero Layout Shift)
                                rx.box(
                                    rx.cond(
                                        UnderwritingState.diff_credit_text != "",
                                        rx.text(
                                            UnderwritingState.diff_credit_text,
                                            size="1",
                                            weight="bold",
                                            color=UnderwritingState.diff_credit_color,
                                            font_family="monospace",
                                            style={"font_size": "10px", "white_space": "nowrap"},
                                        ),
                                        rx.fragment(),
                                    ),
                                    width="70px",
                                    min_width="70px",
                                    max_width="70px",
                                    flex_shrink="0",
                                    style={"display": "flex", "justify_content": "flex-end", "align_items": "center"},
                                ),
                                # Ô nhập liệu số học cố định width="110px"
                                rx.input(
                                    id="sim_credit_input",
                                    value=UnderwritingState.sim_amt_credit_str,
                                    on_change=UnderwritingState.set_sim_credit_from_input,
                                    size="1",
                                    width="110px",
                                    min_width="110px",
                                    max_width="110px",
                                    flex_shrink="0",
                                    style={
                                        "text_align": "right",
                                        "font_family": "monospace",
                                        "font_weight": "bold",
                                        "color": "#F8FAFC",
                                        "background": "#0B0F19",
                                        "border": "1px solid #334155",
                                        "border_radius": "6px",
                                        "height": "26px",
                                        "padding_right": "8px",
                                    },
                                ),
                                spacing="1",
                                align="center",
                                flex_shrink="0",
                            ),
                            width="100%",
                            min_width="0",
                            max_width="100%",
                            align="center",
                            style={"flex_wrap": "nowrap", "overflow": "hidden"},
                        ),
                        # Slider drag-on-the-fly (on_change) + ML inference on release (on_value_commit)
                        rx.slider(
                            value=UnderwritingState.sim_amt_credit_slider,
                            min=UnderwritingState.sim_credit_slider_min,
                            max=UnderwritingState.sim_credit_slider_max,
                            step=1000,
                            on_change=UnderwritingState.set_sim_credit_from_slider,
                            on_value_commit=UnderwritingState.commit_sim_slider,
                            color_scheme="blue",
                            width="100%",
                            flex="1",
                            min_width="0",
                            max_width="100%",
                            box_sizing="border-box",
                            style={
                                "transition": "none !important",
                                "touch_action": "none",
                                "user_select": "none",
                                "min_width": "0",
                                "max_width": "100%",
                                "width": "100%",
                                "& *": {
                                    "transition": "none !important",
                                    "animation": "none !important",
                                },
                            },
                        ),
                        rx.hstack(
                            rx.text(UnderwritingState.sim_credit_min_display, size="1", color="#64748B", style={"font_size": "10px", "font_family": "monospace"}),
                            rx.spacer(min_width="0", flex="1"),
                            rx.text(UnderwritingState.sim_credit_max_display, size="1", color="#64748B", style={"font_size": "10px", "font_family": "monospace"}),
                            width="100%",
                            min_width="0",
                            padding_x="1",
                        ),
                        spacing="1",
                        width="100%",
                        min_width="0",
                    ),
                    width="100%",
                    min_width="0",
                    max_width="100%",
                    background="rgba(15, 23, 42, 0.5)",
                    border="1px solid #1E293B",
                    border_radius="8px",
                    padding="2.5",
                    box_sizing="border-box",
                    overflow_x="hidden",
                    overflow_y="hidden",
                ),

                # Lever 2: TERM_MONTHS (Thời hạn vay) với Snapped Steps & Preset Pills
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            # Khối nhãn bên trái: Tên biến + nhãn phụ - flex_shrink="0"
                            rx.hstack(
                                rx.badge("TERM_MONTHS", color_scheme="cyan", variant="surface", size="1", font_family="monospace"),
                                rx.text("Tenure", size="1", color="#9CA3AF", white_space="nowrap"),
                                spacing="2",
                                align="center",
                                flex_shrink="0",
                            ),
                            rx.spacer(min_width="0", flex="1"),
                            # Khối delta & input bên phải: Fixed Width - flex_shrink="0"
                            rx.hstack(
                                # Vùng chứa nhãn delta cố định width="50px" (Zero Layout Shift)
                                rx.box(
                                    rx.cond(
                                        UnderwritingState.diff_term_text != "",
                                        rx.text(
                                            UnderwritingState.diff_term_text,
                                            size="1",
                                            weight="bold",
                                            color=UnderwritingState.diff_term_color,
                                            font_family="monospace",
                                            style={"font_size": "10px", "white_space": "nowrap"},
                                        ),
                                        rx.fragment(),
                                    ),
                                    width="50px",
                                    min_width="50px",
                                    max_width="50px",
                                    flex_shrink="0",
                                    style={"display": "flex", "justify_content": "flex-end", "align_items": "center"},
                                ),
                                rx.hstack(
                                    rx.input(
                                        id="sim_term_input",
                                        value=UnderwritingState.sim_term_months_str,
                                        on_change=UnderwritingState.set_sim_term_from_input,
                                        size="1",
                                        width="55px",
                                        min_width="55px",
                                        max_width="55px",
                                        flex_shrink="0",
                                        style={
                                            "text_align": "right",
                                            "font_family": "monospace",
                                            "font_weight": "bold",
                                            "color": "#38BDF8",
                                            "background": "#0B0F19",
                                            "border": "1px solid #334155",
                                            "border_radius": "6px",
                                            "height": "26px",
                                            "padding_right": "6px",
                                        },
                                    ),
                                    rx.text("mo", size="1", color="#94A3B8", font_family="monospace"),
                                    spacing="1",
                                    align="center",
                                    flex_shrink="0",
                                ),
                                spacing="1",
                                align="center",
                                flex_shrink="0",
                            ),
                            width="100%",
                            min_width="0",
                            max_width="100%",
                            align="center",
                            style={"flex_wrap": "nowrap", "overflow": "hidden"},
                        ),
                        # Slider drag-on-the-fly (on_change) + commit on release (on_value_commit)
                        rx.slider(
                            value=UnderwritingState.sim_term_months_slider,
                            min=3,
                            max=60,
                            step=3,
                            on_change=UnderwritingState.set_sim_term_from_slider,
                            on_value_commit=UnderwritingState.commit_sim_slider,
                            color_scheme="cyan",
                            width="100%",
                            flex="1",
                            min_width="0",
                            max_width="100%",
                            box_sizing="border-box",
                            style={
                                "transition": "none !important",
                                "touch_action": "none",
                                "user_select": "none",
                                "min_width": "0",
                                "max_width": "100%",
                                "width": "100%",
                                "& *": {
                                    "transition": "none !important",
                                    "animation": "none !important",
                                },
                            },
                        ),
                        # Quick Preset Pills (3m, 6m, 12m, 24m, 36m, 48m, 60m)
                        rx.hstack(
                            rx.text("Presets:", size="1", color="#64748B", style={"font_size": "10px", "flex_shrink": "0"}),
                            term_preset_pill(3),
                            term_preset_pill(6),
                            term_preset_pill(12),
                            term_preset_pill(24),
                            term_preset_pill(36),
                            term_preset_pill(48),
                            term_preset_pill(60),
                            spacing="1",
                            align="center",
                            width="100%",
                            min_width="0",
                            padding_top="1",
                            style={"flex_wrap": "wrap"},
                        ),
                        spacing="1",
                        width="100%",
                        min_width="0",
                    ),
                    width="100%",
                    min_width="0",
                    max_width="100%",
                    background="rgba(15, 23, 42, 0.5)",
                    border="1px solid #1E293B",
                    border_radius="8px",
                    padding="2.5",
                    box_sizing="border-box",
                    overflow_x="hidden",
                    overflow_y="hidden",
                ),

                # Lever 3: AMT_ANNUITY (Trả góp tháng)
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            # Khối nhãn bên trái: Tên biến + nhãn phụ - flex_shrink="0"
                            rx.hstack(
                                rx.badge("AMT_ANNUITY", color_scheme="purple", variant="surface", size="1", font_family="monospace"),
                                rx.text("Annuity", size="1", color="#9CA3AF", white_space="nowrap"),
                                spacing="2",
                                align="center",
                                flex_shrink="0",
                            ),
                            rx.spacer(min_width="0", flex="1"),
                            # Khối delta & input bên phải: Fixed Width - flex_shrink="0"
                            rx.hstack(
                                # Vùng chứa nhãn delta cố định width="70px" (Zero Layout Shift)
                                rx.box(
                                    rx.cond(
                                        UnderwritingState.diff_annuity_text != "",
                                        rx.text(
                                            UnderwritingState.diff_annuity_text,
                                            size="1",
                                            weight="bold",
                                            color=UnderwritingState.diff_annuity_color,
                                            font_family="monospace",
                                            style={"font_size": "10px", "white_space": "nowrap"},
                                        ),
                                        rx.fragment(),
                                    ),
                                    width="70px",
                                    min_width="70px",
                                    max_width="70px",
                                    flex_shrink="0",
                                    style={"display": "flex", "justify_content": "flex-end", "align_items": "center"},
                                ),
                                rx.hstack(
                                    rx.input(
                                        id="sim_annuity_input",
                                        value=UnderwritingState.sim_amt_annuity_str,
                                        on_change=UnderwritingState.set_sim_annuity_from_input,
                                        size="1",
                                        width="95px",
                                        min_width="95px",
                                        max_width="95px",
                                        flex_shrink="0",
                                        style={
                                            "text_align": "right",
                                            "font_family": "monospace",
                                            "font_weight": "bold",
                                            "color": "#C084FC",
                                            "background": "#0B0F19",
                                            "border": "1px solid #334155",
                                            "border_radius": "6px",
                                            "height": "26px",
                                            "padding_right": "8px",
                                        },
                                    ),
                                    rx.text("/ mo", size="1", color="#94A3B8", font_family="monospace"),
                                    spacing="1",
                                    align="center",
                                    flex_shrink="0",
                                ),
                                spacing="1",
                                align="center",
                                flex_shrink="0",
                            ),
                            width="100%",
                            min_width="0",
                            max_width="100%",
                            align="center",
                            style={"flex_wrap": "nowrap", "overflow": "hidden"},
                        ),
                        # Slider drag-on-the-fly (on_change) + commit on release (on_value_commit)
                        rx.slider(
                            value=UnderwritingState.sim_amt_annuity_slider,
                            min=UnderwritingState.sim_annuity_slider_min,
                            max=UnderwritingState.sim_annuity_slider_max,
                            step=250,
                            on_change=UnderwritingState.set_sim_annuity_from_slider,
                            on_value_commit=UnderwritingState.commit_sim_slider,
                            color_scheme="purple",
                            width="100%",
                            flex="1",
                            min_width="0",
                            max_width="100%",
                            box_sizing="border-box",
                            style={
                                "transition": "none !important",
                                "touch_action": "none",
                                "user_select": "none",
                                "min_width": "0",
                                "max_width": "100%",
                                "width": "100%",
                                "& *": {
                                    "transition": "none !important",
                                    "animation": "none !important",
                                },
                            },
                        ),
                        rx.hstack(
                            rx.text(UnderwritingState.sim_annuity_min_display, size="1", color="#64748B", style={"font_size": "10px", "font_family": "monospace"}),
                            rx.spacer(min_width="0", flex="1"),
                            rx.text(UnderwritingState.sim_annuity_max_display, size="1", color="#64748B", style={"font_size": "10px", "font_family": "monospace"}),
                            width="100%",
                            min_width="0",
                            padding_x="1",
                        ),
                        spacing="1",
                        width="100%",
                        min_width="0",
                    ),
                    width="100%",
                    min_width="0",
                    max_width="100%",
                    background="rgba(15, 23, 42, 0.5)",
                    border="1px solid #1E293B",
                    border_radius="8px",
                    padding="2.5",
                    box_sizing="border-box",
                    overflow_x="hidden",
                    overflow_y="hidden",
                ),

                # Lever 4: AMT_INCOME_TOTAL (Tổng thu nhập)
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            # Khối nhãn bên trái: Tên biến + nhãn phụ - flex_shrink="0"
                            rx.hstack(
                                rx.badge("AMT_INCOME_TOTAL", color_scheme="indigo", variant="surface", size="1", font_family="monospace"),
                                rx.text("Income", size="1", color="#9CA3AF", white_space="nowrap"),
                                spacing="2",
                                align="center",
                                flex_shrink="0",
                            ),
                            rx.spacer(min_width="0", flex="1"),
                            # Khối delta & input bên phải: Fixed Width - flex_shrink="0"
                            rx.hstack(
                                # Vùng chứa nhãn delta cố định width="70px" (Zero Layout Shift)
                                rx.box(
                                    rx.cond(
                                        UnderwritingState.diff_income_text != "",
                                        rx.text(
                                            UnderwritingState.diff_income_text,
                                            size="1",
                                            weight="bold",
                                            color=UnderwritingState.diff_income_color,
                                            font_family="monospace",
                                            style={"font_size": "10px", "white_space": "nowrap"},
                                        ),
                                        rx.fragment(),
                                    ),
                                    width="70px",
                                    min_width="70px",
                                    max_width="70px",
                                    flex_shrink="0",
                                    style={"display": "flex", "justify_content": "flex-end", "align_items": "center"},
                                ),
                                # Ô nhập liệu số học cố định width="110px"
                                rx.input(
                                    id="sim_income_input",
                                    value=UnderwritingState.sim_amt_income_str,
                                    on_change=UnderwritingState.set_sim_income_from_input,
                                    size="1",
                                    width="110px",
                                    min_width="110px",
                                    max_width="110px",
                                    flex_shrink="0",
                                    style={
                                        "text_align": "right",
                                        "font_family": "monospace",
                                        "font_weight": "bold",
                                        "color": "#818CF8",
                                        "background": "#0B0F19",
                                        "border": "1px solid #334155",
                                        "border_radius": "6px",
                                        "height": "26px",
                                        "padding_right": "8px",
                                    },
                                ),
                                spacing="1",
                                align="center",
                                flex_shrink="0",
                            ),
                            width="100%",
                            min_width="0",
                            max_width="100%",
                            align="center",
                            style={"flex_wrap": "nowrap", "overflow": "hidden"},
                        ),
                        # Slider drag-on-the-fly (on_change) + commit on release (on_value_commit)
                        rx.slider(
                            value=UnderwritingState.sim_amt_income_slider,
                            min=UnderwritingState.sim_income_slider_min,
                            max=UnderwritingState.sim_income_slider_max,
                            step=1000,
                            on_change=UnderwritingState.set_sim_income_from_slider,
                            on_value_commit=UnderwritingState.commit_sim_slider,
                            color_scheme="indigo",
                            width="100%",
                            flex="1",
                            min_width="0",
                            max_width="100%",
                            box_sizing="border-box",
                            style={
                                "transition": "none !important",
                                "touch_action": "none",
                                "user_select": "none",
                                "min_width": "0",
                                "max_width": "100%",
                                "width": "100%",
                                "& *": {
                                    "transition": "none !important",
                                    "animation": "none !important",
                                },
                            },
                        ),
                        rx.hstack(
                            rx.text(UnderwritingState.sim_income_min_display, size="1", color="#64748B", style={"font_size": "10px", "font_family": "monospace"}),
                            rx.spacer(min_width="0", flex="1"),
                            rx.text(UnderwritingState.sim_income_max_display, size="1", color="#64748B", style={"font_size": "10px", "font_family": "monospace"}),
                            width="100%",
                            min_width="0",
                            padding_x="1",
                        ),
                        spacing="1",
                        width="100%",
                        min_width="0",
                    ),
                    width="100%",
                    min_width="0",
                    max_width="100%",
                    background="rgba(15, 23, 42, 0.5)",
                    border="1px solid #1E293B",
                    border_radius="8px",
                    padding="2.5",
                    box_sizing="border-box",
                    overflow_x="hidden",
                    overflow_y="hidden",
                ),
                spacing="2",
                width="100%",
                min_width="0",
            ),

            rx.divider(border_color="#1E293B", margin_y="1"),

            # 4. ACTION FOOTER: [ Reset to Baseline ] (Ghost/Outline) & [ AI Auto-Optimize ] (Gradient)
            rx.hstack(
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
            ),

            # 5. KHUNG GỢI Ý TÁI CƠ CẤU (AI OPTIMIZATION PROPOSALS)
            rx.cond(
                UnderwritingState.show_optimization_results & (UnderwritingState.optimization_options.length() > 0),
                rx.vstack(
                    # 1. Thẻ chính: Recommended Proposal
                    recommended_proposal_card(UnderwritingState.recommended_option),
                    # 2. Nút đóng/mở kịch bản phụ (Collapsible Trigger)
                    alternative_options_trigger(),
                    # 3. Danh sách kịch bản phụ: Shortest Tenure & Balanced Compromise
                    rx.cond(
                        UnderwritingState.show_alternative_options,
                        rx.cond(
                            UnderwritingState.is_loading_alternatives,
                            rx.box(
                                rx.hstack(
                                    rx.spinner(size="2", color="cyan"),
                                    rx.text(
                                        "Calculating alternative suggestions...",
                                        size="2",
                                        color="#94A3B8",
                                        weight="medium",
                                    ),
                                    spacing="3",
                                    align="center",
                                    justify="center",
                                ),
                                padding="6",
                                background="#0D1322",
                                border="1px dashed #1E293B",
                                border_radius="10px",
                                width="100%",
                            ),
                            rx.vstack(
                                rx.foreach(
                                    UnderwritingState.alternative_options,
                                    secondary_scenario_card,
                                ),
                                spacing="3",
                                width="100%",
                            ),
                        ),
                        rx.fragment(),
                    ),
                    spacing="3",
                    width="100%",
                    margin_top="1",
                ),
                rx.fragment(),
            ),
            spacing="3",
            width="100%",
            min_width="0",
        ),
        background="#111827",
        border="1px solid #1F2937",
        border_radius="12px",
        padding="4",
        box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.3)",
        width="100%",
        min_width="0",
        max_width="100%",
        overflow_x="hidden",
        box_sizing="border-box",
    )


# Alias tương thích ngược
terms_simulator_view = what_if_view