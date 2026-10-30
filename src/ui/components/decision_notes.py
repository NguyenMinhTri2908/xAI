import reflex as rx
from src.state import UnderwritingState


def decision_notes_view() -> rx.Component:
    """Thẻ ghi chú và ra quyết định thẩm định cuối cùng của Underwriter."""
    return rx.card(
        rx.vstack(
            rx.text("Underwriter Decision & Notes", font_weight="bold", size="2", color="white"),
            rx.divider(color_scheme="gray", opacity="0.3"),
            rx.text_area(
                placeholder="Enter approval conditions or audit notes...",
                value=UnderwritingState.underwriter_notes,
                on_change=UnderwritingState.set_underwriter_notes,
                size="1",
                width="100%",
            ),
            rx.hstack(
                rx.button(
                    "Approve with Conditions",
                    color_scheme="green",
                    size="1",
                    width="60%",
                    cursor="pointer",
                    on_click=lambda: UnderwritingState.record_decision("CONDITIONAL"),
                ),
                rx.button(
                    "Decline",
                    color_scheme="red",
                    size="1",
                    width="40%",
                    cursor="pointer",
                    on_click=lambda: UnderwritingState.record_decision("DECLINE"),
                ),
                width="100%",
                spacing="2",
                margin_top="2",
            ),
            width="100%",
        ),
        background="#111827",
        border="1px solid #1F2937",
        width="100%",
    )
