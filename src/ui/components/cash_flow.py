import reflex as rx

def cash_flow_view() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text("Income & Cash Flow Verification", font_weight="bold", size="2", color="white"),
            rx.divider(color_scheme="gray", opacity="0.3"),
            rx.hstack(
                rx.box(rx.text("Net Income", size="1", color="#9CA3AF"), rx.text("$3,200", font_weight="bold", color="white")),
                rx.box(rx.text("Existing Debt", size="1", color="#9CA3AF"), rx.text("$950", font_weight="bold", color="white")),
                rx.box(rx.text("Surplus", size="1", color="#9CA3AF"), rx.text("$2,250", font_weight="bold", color="white")),
                justify="between",
                width="100%",
            ),
            rx.badge("DTI / DSR: 29.6% (Safe)", color_scheme="green", size="1", margin_top="1"),
            width="100%",
        ),
        background="#111827",
        border="1px solid #1F2937",
        width="100%",
    )