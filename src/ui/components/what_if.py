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


def what_if_view() -> rx.Component:
    """Component Risk Mitigation & Terms Simulator theo phong cách Notion/Linear tối giản.
    Tập trung vào clean typography, low clutter, hiển thị 2 chỉ số cốt lõi và delta chênh lệch.
    """
    return rx.card(
        rx.vstack(
            # 1. HEADER TỐI GIẢN (Đưa về 1 hàng duy nhất, loại bỏ icon thừa và status badge)
            rx.vstack(
                rx.text(
                    "Risk Mitigation & Terms Simulator",
                    size="3",
                    weight="bold",
                    color="#F8FAFC",
                    line_height="1.2",
                ),
                rx.text(
                    "Restructure loan terms and evaluate real-time credit risk impact.",
                    size="1",
                    color="#64748B",
                    line_height="1.2",
                    white_space="nowrap",
                    overflow="hidden",
                    text_overflow="ellipsis",
                ),
                spacing="1",
                align_items="flex-start",
                width="100%",
            ),

            # 2. METRICS CARD TINH GỌN (2 chỉ số cốt lõi: Probability of Default & DTI Ratio)
            rx.box(
                rx.hstack(
                    # Metric 1: Probability of Default (PD)
                    rx.vstack(
                        rx.text(
                            "Probability of Default (PD)",
                            size="1",
                            color="#94A3B8",
                            weight="medium",
                        ),
                        rx.cond(
                            UnderwritingState.is_simulated_changed,
                            # Trạng thái điều chỉnh (Simulated): hiển thị PD mới kèm delta (+/-...% pts)
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
                            # Trạng thái ban đầu: hiển thị baseline kèm nhãn nhỏ mờ (Baseline)
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
                    ),
                    rx.spacer(),
                    # Đường phân tách dọc tinh tế
                    rx.box(width="1px", height="28px", background="#1E293B"),
                    rx.spacer(),
                    # Metric 2: DTI Ratio (Chỉ giữ lại tỷ lệ %, bỏ các badge Tier / Safe)
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
                            color="#F8FAFC",
                            font_family="monospace",
                        ),
                        spacing="1",
                        align_items="flex-start",
                    ),
                    width="100%",
                    align="center",
                    padding_x="4",
                    padding_y="3",
                ),
                width="100%",
                background="#0B0F19",
                border="1px solid #1E293B",
                border_radius="8px",
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
                    on_click=UnderwritingState.ai_auto_optimize,
                ),
                width="100%",
                min_width="0",
                align="center",
                spacing="3",
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