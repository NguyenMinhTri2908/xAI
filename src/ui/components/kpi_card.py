import reflex as rx
from src.ui.state import UnderwritingState

CUTOFF_THRESHOLD = 16.0

def recommendation_badge(pd_score: float) -> rx.Component:
    return rx.cond(
        pd_score < CUTOFF_THRESHOLD,
        rx.badge("RECOMMEND APPROVE", color_scheme="green", size="3", variant="surface"),
        rx.badge("RECOMMEND REJECT", color_scheme="red", size="3", variant="surface"),
    )

def kpi_card_view() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.text("Application: #", size="2", weight="bold", color="gray"),
                    rx.text(UnderwritingState.selected_client_id, size="2", weight="bold", color="white"),
                    spacing="0",
                ),
                rx.spacer(),
                recommendation_badge(UnderwritingState.current_score_percent),
                width="100%",
                align="center",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("PD Score", size="1", color="#9CA3AF"),
                    rx.text(
                        UnderwritingState.current_score_percent.to_string() + "%",
                        size="6",
                        weight="bold",
                        color_scheme=rx.cond(
                            UnderwritingState.current_score_percent < CUTOFF_THRESHOLD,
                            "green",
                            "red",
                        ),
                    ),
                    align_items="start",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text("Recommended Action", size="1", color="#9CA3AF"),
                    rx.text(
                        rx.cond(
                            UnderwritingState.current_score_percent < CUTOFF_THRESHOLD,
                            "APPROVE",
                            "REJECT",
                        ),
                        size="4",
                        weight="bold",
                        color_scheme=rx.cond(
                            UnderwritingState.current_score_percent < CUTOFF_THRESHOLD,
                            "green",
                            "red",
                        ),
                    ),
                    align_items="end",
                ),
                width="100%",
                align="center",
                padding_top="2",
            ),
        ),
        background="#111827",
        border="1px solid #1F2937",
        width="100%",
    )