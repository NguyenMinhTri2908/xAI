"""
UI COMPONENT CONTAINER: TERMS & WHAT-IF SIMULATOR
=================================================
Risk Mitigation & Terms Simulator theo phong cách Notion/Linear tối giản.
Đóng vai trò Container kết hợp 3 sub-components chuyên trách:
1. what_if_metrics: Header & Thẻ hiển thị Metrics (PD, Offered Rate, DTI)
2. what_if_controls: 4 bộ điều khiển Slider & Input đòn bẩy tài chính (Credit, Term, Annuity, Income)
3. what_if_proposals: Thẻ kịch bản cơ cấu nợ AI (Recommended & Alternatives) & Nút tác vụ
"""

import reflex as rx
from src.ui.components.what_if_metrics import (
    simulator_header_badge,
    simulator_metrics_card,
)
from src.ui.components.what_if_controls import (
    simulator_levers_container,
    term_preset_pill,
    credit_lever_control,
    term_lever_control,
    annuity_lever_control,
    income_lever_control,
)
from src.ui.components.what_if_proposals import (
    action_footer_controls,
    ai_optimization_section,
    scenario_metrics_grid,
    recommended_proposal_card,
    alternative_options_trigger,
    secondary_scenario_card,
    optimization_scenario_card,
    optimal_baseline_alert,
    compact_alternative_card,
)


def what_if_view() -> rx.Component:
    """Component Risk Mitigation & Terms Simulator chính."""
    return rx.card(
        rx.vstack(
            # 1. Header: Tiêu đề Simulator & Badge Quyết định mô phỏng
            simulator_header_badge(),

            # 2. Thẻ hiển thị Metrics: PD, Offered Rate, DTI kèm Guardrail
            simulator_metrics_card(),

            # 3. 4 Bộ điều khiển Sliders & Inputs (Levers)
            simulator_levers_container(),

            # Phân cách giao diện
            rx.divider(border_color="#1E293B", margin_y="1"),

            # 4. Action Footer: [ Reset to Baseline ] & [ AI Auto-Optimize ]
            action_footer_controls(),

            # 5. Khung hiển thị gợi ý tái cơ cấu AI (Recommended & Alternatives)
            ai_optimization_section(),

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


# Bí danh tương thích ngược (Backward Compatibility Aliases)
terms_simulator_view = what_if_view

__all__ = [
    "what_if_view",
    "terms_simulator_view",
    "term_preset_pill",
    "scenario_metrics_grid",
    "recommended_proposal_card",
    "alternative_options_trigger",
    "secondary_scenario_card",
    "optimization_scenario_card",
    "simulator_header_badge",
    "simulator_metrics_card",
    "simulator_levers_container",
    "credit_lever_control",
    "term_lever_control",
    "annuity_lever_control",
    "income_lever_control",
    "action_footer_controls",
    "ai_optimization_section",
    "optimal_baseline_alert",
    "compact_alternative_card",
]