"""
UI SUB-COMPONENT: SIMULATOR SLIDER & INPUT CONTROLS
===================================================
Chứa 4 bộ điều khiển đòn bẩy tài chính (Levers) kết hợp Hybrid (Slider + Input số học + Nhãn Delta):
- Lever 1: AMT_CREDIT (Hạn mức vay)
- Lever 2: TERM_MONTHS (Thời hạn vay) kèm Quick Preset Pills (3m, 6m, 12m, 24m, 36m, 48m, 60m)
- Lever 3: AMT_ANNUITY (Số tiền trả góp hàng tháng)
- Lever 4: AMT_INCOME_TOTAL (Tổng thu nhập hàng tháng)
Áp dụng Fixed Width chống giật giao diện (Zero Layout Shift).
"""

import reflex as rx
from src.state import UnderwritingState


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


def credit_lever_control() -> rx.Component:
    """Bộ điều khiển đòn bẩy 1: AMT_CREDIT (Số tiền vay)."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                # Khối nhãn bên trái: Tên biến + nhãn phụ
                rx.hstack(
                    rx.badge("AMT_CREDIT", color_scheme="blue", variant="surface", size="1", font_family="monospace"),
                    rx.text("Loan Amount", size="1", color="#9CA3AF", white_space="nowrap"),
                    spacing="2",
                    align="center",
                    flex_shrink="0",
                ),
                rx.spacer(min_width="0", flex="1"),
                # Khối delta & input bên phải: Fixed Width
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
            # Slider drag-on-the-fly + ML inference on release
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
    )


def term_lever_control() -> rx.Component:
    """Bộ điều khiển đòn bẩy 2: TERM_MONTHS (Thời hạn vay) kèm Quick Preset Pills."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                # Khối nhãn bên trái: Tên biến + nhãn phụ
                rx.hstack(
                    rx.badge("TERM_MONTHS", color_scheme="cyan", variant="surface", size="1", font_family="monospace"),
                    rx.text("Tenure", size="1", color="#9CA3AF", white_space="nowrap"),
                    spacing="2",
                    align="center",
                    flex_shrink="0",
                ),
                rx.spacer(min_width="0", flex="1"),
                # Khối delta & input bên phải: Fixed Width
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
            # Slider drag-on-the-fly + commit on release
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
    )


def annuity_lever_control() -> rx.Component:
    """Bộ điều khiển đòn bẩy 3: AMT_ANNUITY (Trả góp tháng)."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                # Khối nhãn bên trái: Tên biến + nhãn phụ
                rx.hstack(
                    rx.badge("AMT_ANNUITY", color_scheme="purple", variant="surface", size="1", font_family="monospace"),
                    rx.text("Annuity", size="1", color="#9CA3AF", white_space="nowrap"),
                    spacing="2",
                    align="center",
                    flex_shrink="0",
                ),
                rx.spacer(min_width="0", flex="1"),
                # Khối delta & input bên phải: Fixed Width
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
            # Slider drag-on-the-fly + commit on release
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
    )


def income_lever_control() -> rx.Component:
    """Bộ điều khiển đòn bẩy 4: AMT_INCOME_TOTAL (Tổng thu nhập)."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                # Khối nhãn bên trái: Tên biến + nhãn phụ
                rx.hstack(
                    rx.badge("AMT_INCOME_TOTAL", color_scheme="indigo", variant="surface", size="1", font_family="monospace"),
                    rx.text("Income", size="1", color="#9CA3AF", white_space="nowrap"),
                    spacing="2",
                    align="center",
                    flex_shrink="0",
                ),
                rx.spacer(min_width="0", flex="1"),
                # Khối delta & input bên phải: Fixed Width
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
            # Slider drag-on-the-fly + commit on release
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
    )


def simulator_levers_container() -> rx.Component:
    """Nhóm gom cả 4 bộ điều khiển đòn bẩy tài chính."""
    return rx.vstack(
        credit_lever_control(),
        term_lever_control(),
        annuity_lever_control(),
        income_lever_control(),
        spacing="2",
        width="100%",
        min_width="0",
    )

