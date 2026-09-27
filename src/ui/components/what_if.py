import reflex as rx

def what_if_view() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.text("What-If Scenario Simulator", font_weight="bold", size="2", color="white"),
            rx.divider(color_scheme="gray", opacity="0.3"),
            rx.text("Loan Amount ($): 20,000", size="1", color="#9CA3AF"),
            rx.slider(default_value=[20000], min=5000, max=50000, step=1000, width="100%"),
            rx.text("Tenure: 18 Months", size="1", color="#9CA3AF"),
            rx.slider(default_value=[18], min=6, max=48, step=6, width="100%"),
            rx.hstack(
                rx.text("Simulated PD:", size="1", color="#9CA3AF"),
                rx.text("3.8% (-1.0%)", font_weight="bold", color="#10B981", size="2"),
                justify="between",
                width="100%",
            ),
            rx.button("Apply What-If to Conditions", size="1", color_scheme="blue", width="100%"),
            spacing="2",
            width="100%",
        ),
        background="#111827",
        border="1px solid #1F2937",
        width="100%",
    )