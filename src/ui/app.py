import reflex as rx
from src.ui.state import UnderwritingState


def tier_badge(tier: str, decision: str) -> rx.Component:
    """Renders a color-coded decision badge based on credit tier."""
    return rx.match(
        decision,
        ("AUTO_APPROVE", rx.badge("Tier A - Auto Approve", color_scheme="green", size="3")),
        ("STANDARD_APPROVE", rx.badge("Tier B - Standard Approve", color_scheme="blue", size="3")),
        ("MANUAL_REVIEW", rx.badge("Tier C - Manual Review", color_scheme="amber", size="3")),
        ("REJECT", rx.badge("Tier D - Reject", color_scheme="red", size="3")),
        rx.badge("Pending", color_scheme="gray", size="3")
    )


def factor_row(factor: dict, is_risk: bool = True) -> rx.Component:
    """Renders a single SHAP attribution factor row."""
    color = "red" if is_risk else "green"
    sign = "+" if is_risk else ""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(factor["feature"], weight="bold", size="2"),
                rx.text(f"Observed Value: {factor['display_value']}", size="1", color_scheme="gray"),
                align_items="start",
                spacing="1"
            ),
            rx.spacer(),
            rx.badge(
                f"{sign}{factor['shap_value']:.4f}",
                color_scheme=color,
                variant="surface"
            ),
            align="center",
            width="100%",
            padding_y="2"
        ),
        rx.divider()
    )


def index() -> rx.Component:
    return rx.container(
        # Top Navigation Bar
        rx.hstack(
            rx.heading("Automated Credit Underwriting System", size="6"),
            rx.spacer(),
            rx.badge("Production Mode", color_scheme="teal", variant="solid"),
            align="center",
            padding_y="4",
            border_bottom="1px solid #e5e7eb"
        ),

        # Main Dashboard Layout: 2 Columns
        rx.grid(
            # Left Column: Client Queue
            rx.vstack(
                rx.heading("Loan Applications Queue", size="4"),
                rx.text("Select a client to run automated risk assessment", size="2", color_scheme="gray"),

                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Client ID"),
                            rx.table.column_header_cell("Income"),
                            rx.table.column_header_cell("Requested Loan"),
                            rx.table.column_header_cell("Action"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            UnderwritingState.client_list,
                            lambda row: rx.table.row(
                                rx.table.cell(rx.text(row["SK_ID_CURR"], weight="medium")),
                                rx.table.cell(row["INCOME_DISPLAY"]),
                                rx.table.cell(row["CREDIT_DISPLAY"]),
                                rx.table.cell(
                                    rx.button(
                                        "Evaluate",
                                        size="1",
                                        variant="soft",
                                        on_click=lambda: UnderwritingState.select_and_evaluate_client(
                                            row["SK_ID_CURR"].to_string())
                                    )
                                ),
                                style={
                                    "background_color": rx.cond(
                                        UnderwritingState.selected_client_id == row["SK_ID_CURR"].to_string(),
                                        "#f3f4f6",
                                        "transparent"
                                    )
                                }
                            )
                        )
                    ),
                    width="100%",
                    variant="surface"
                ),
                align_items="start",
                spacing="3",
                width="100%"
            ),

            # Right Column: Underwriting Decision & SHAP Attribution
            rx.vstack(
                rx.heading("Underwriting Assessment Report", size="4"),

                rx.cond(
                    UnderwritingState.selected_client_id != "",
                    rx.vstack(
                        # KPI Card
                        rx.card(
                            rx.vstack(
                                rx.hstack(
                                    rx.text(f"Application: #{UnderwritingState.selected_client_id}", size="3",
                                            weight="bold"),
                                    rx.spacer(),
                                    tier_badge(UnderwritingState.current_tier, UnderwritingState.current_decision),
                                    width="100%",
                                    align="center"
                                ),
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("Probability of Default (PD)", size="2", color_scheme="gray"),
                                        rx.text(f"{UnderwritingState.current_score_percent}%", size="7", weight="bold",
                                                color_scheme=rx.cond(UnderwritingState.current_pd > 0.08, "red",
                                                                     "green")),
                                        align_items="start"
                                    ),
                                    rx.spacer(),
                                    rx.vstack(
                                        rx.text("Recommended Action", size="2", color_scheme="gray"),
                                        rx.text(UnderwritingState.current_decision, size="5", weight="bold"),
                                        align_items="end"
                                    ),
                                    width="100%",
                                    align="center",
                                    padding_top="2"
                                ),
                                spacing="2"
                            ),
                            width="100%"
                        ),

                        # SHAP Drivers
                        rx.card(
                            rx.vstack(
                                rx.heading("Key Risk Drivers (Top Negative Factors)", size="3", color_scheme="red"),
                                rx.foreach(
                                    UnderwritingState.top_risk_factors,
                                    lambda f: factor_row(f, is_risk=True)
                                ),
                                rx.heading("Key Trust Factors (Top Positive Factors)", size="3", color_scheme="green",
                                           padding_top="3"),
                                rx.foreach(
                                    UnderwritingState.top_positive_factors,
                                    lambda f: factor_row(f, is_risk=False)
                                ),
                                spacing="2",
                                width="100%"
                            ),
                            width="100%"
                        ),
                        spacing="4",
                        width="100%"
                    ),
                    rx.card(
                        rx.text("Please select an application record from the queue to view assessment.",
                                color_scheme="gray"),
                        width="100%"
                    )
                ),
                align_items="start",
                spacing="3",
                width="100%"
            ),
            columns="2",
            spacing="6",
            width="100%",
            padding_top="4"
        ),
        on_mount=UnderwritingState.load_demo_clients,
        max_width="1280px"
    )


app = rx.App()
app.add_page(index, title="Credit Underwriting Dashboard")