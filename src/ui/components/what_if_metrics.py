"""
UI SUB-COMPONENT: SIMULATOR HEADER & METRICS
============================================
Chứa khối Header (Tiêu đề + Badge Quyết định mô phỏng) và Thẻ hiển thị Metrics cốt lõi:
- Probability of Default (PD) kèm Delta Badge
- Offered Rate (RBP) kèm Delta Badge
- DTI Ratio kèm Feasibility Guardrail cảnh báo vượt trần
- Trạng thái Deferred Calculation Spinner khi kéo slider
"""

import reflex as rx
from src.state import UnderwritingState
from src.config.pricing_config import retail_pricing_config


def simulator_header_badge() -> rx.Component:
    """Header của Simulator: Tiêu đề 'Simulator' và Badge Quyết định độc lập với Baseline."""
    return rx.hstack(
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
    )


def simulator_metrics_card() -> rx.Component:
    """Thẻ Metrics tích hợp tính toán trì hoãn (Deferred) & Cảnh báo trần DTI (Feasibility Guardrail)."""
    return rx.box(
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
                            color=rx.cond(UnderwritingState.is_sim_dti_exceeded, "#F59E0B", "#F8FAFC"),
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
                # Cảnh báo Feasibility Guardrail nếu DTI vượt max_dti_limit
                rx.cond(
                    UnderwritingState.is_sim_dti_exceeded,
                    rx.hstack(
                        rx.icon("triangle-alert", size=13, color="#F59E0B"),
                        rx.text(
                            f"Warning: Monthly payment exceeds {int(retail_pricing_config.max_dti_limit)}% DTI threshold",
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
    )

