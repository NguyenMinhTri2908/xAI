import reflex as rx

def decision_notes_view() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text("Underwriter Decision & Notes", font_weight="bold", size="2", color="white"),
            rx.divider(color_scheme="gray", opacity="0.3"),
            rx.text_area(placeholder="Enter approval conditions or audit notes...", size="1", width="100%"),
            rx.hstack(
                rx.button("Approve with Conditions", color_scheme="green", size="1", width="60%"),
                rx.button("Decline", color_scheme="red", size="1", width="40%"),
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