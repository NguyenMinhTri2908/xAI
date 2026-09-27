import reflex as rx
from src.ui.state import UnderwritingState
from src.ui.components.header import header_view

# Policy Cut-off Threshold (5.0% PD)
CUTOFF_THRESHOLD = 5.0


def recommendation_badge(pd_score: float) -> rx.Component:
    """Renders binary underwriting decision support badge."""
    return rx.cond(
        pd_score < CUTOFF_THRESHOLD,
        rx.badge("RECOMMEND APPROVE", color_scheme="green", size="3", variant="surface"),
        rx.badge("RECOMMEND REJECT", color_scheme="red", size="3", variant="surface"),
    )


def factor_row(factor: dict, is_risk: bool = True) -> rx.Component:
    """Renders a single SHAP attribution factor row safely using Reflex Var operations."""
    color = "red" if is_risk else "green"
    sign = "+" if is_risk else ""
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(factor["feature"], weight="bold", size="2"),
                rx.hstack(
                    rx.text("Observed Value:", size="1", color_scheme="gray"),
                    rx.text(factor["display_value"].to_string(), size="1", color_scheme="gray"),
                    spacing="1",
                ),
                align_items="start",
                spacing="1",
            ),
            rx.spacer(),
            rx.badge(
                rx.hstack(
                    rx.text(sign),
                    rx.text(factor["shap_value"].to_string()),
                    spacing="0",
                ),
                color_scheme=color,
                variant="surface",
                size="2",
            ),
            align="center",
            width="100%",
            padding_y="2",
        ),
        rx.divider(color_scheme="gray", opacity="0.3"),
    )


def index() -> rx.Component:
    return rx.container(
        # Top Navigation Bar
        header_view(),



        # Main Dashboard Layout: 2 Columns
        rx.grid(
            # Left Column: Client Queue
            rx.vstack(
                rx.heading("Loan Applications Queue", size="4"),
                rx.text("Select a client to run automated risk assessment", size="2", color_scheme="gray"),

                rx.box(
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
                                            variant=rx.cond(
                                                UnderwritingState.selected_client_id == row["SK_ID_CURR"].to_string(),
                                                "solid",
                                                "soft",
                                            ),
                                            on_click=lambda: UnderwritingState.select_and_evaluate_client(
                                                row["SK_ID_CURR"].to_string()
                                            ),
                                        )
                                    ),
                                    style={
                                        "background_color": rx.cond(
                                            UnderwritingState.selected_client_id == row["SK_ID_CURR"].to_string(),
                                            "#18181b",
                                            "transparent",
                                        )
                                    },
                                )
                            )
                        ),
                        width="100%",
                        variant="surface",
                    ),
                    max_height="640px",
                    overflow_y="auto",
                    width="100%",
                    border="1px solid #27272a",
                    border_radius="8px",
                ),
                align_items="start",
                spacing="3",
                width="100%",
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
                                    rx.hstack(
                                        rx.text("Application: #", size="3", weight="bold"),
                                        rx.text(UnderwritingState.selected_client_id, size="3", weight="bold"),
                                        spacing="0",
                                    ),
                                    rx.spacer(),
                                    recommendation_badge(UnderwritingState.current_score_percent),
                                    width="100%",
                                    align="center",
                                ),
                                rx.hstack(
                                    rx.vstack(
                                        rx.text("Probability of Default (PD)", size="2", color_scheme="gray"),
                                        rx.text(
                                            UnderwritingState.current_score_percent.to_string() + "%",
                                            size="7",
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
                                        rx.text("Recommended Action", size="2", color_scheme="gray"),
                                        rx.text(
                                            rx.cond(
                                                UnderwritingState.current_score_percent < CUTOFF_THRESHOLD,
                                                "APPROVE",
                                                "REJECT",
                                            ),
                                            size="5",
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
                                spacing="2",
                            ),
                            width="100%",
                        ),

                        # SHAP Drivers
                        rx.card(
                            rx.vstack(
                                rx.heading("Key Risk Drivers (Top Negative Factors)", size="3", color_scheme="red"),
                                rx.foreach(
                                    UnderwritingState.top_risk_factors,
                                    lambda f: factor_row(f, is_risk=True),
                                ),
                                rx.heading(
                                    "Key Trust Factors (Top Positive Factors)",
                                    size="3",
                                    color_scheme="green",
                                    padding_top="3",
                                ),
                                rx.foreach(
                                    UnderwritingState.top_positive_factors,
                                    lambda f: factor_row(f, is_risk=False),
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    rx.card(
                        rx.text(
                            "Please select an application record from the queue to view assessment.",
                            color_scheme="gray",
                        ),
                        width="100%",
                    ),
                ),
                align_items="start",
                spacing="3",
                width="100%",
            ),
            columns="2",
            spacing="6",
            width="100%",
            padding_top="4",
        ),
        on_mount=UnderwritingState.load_demo_clients,
        max_width="1280px",
    )


app = rx.App()
app.add_page(index, title="Credit Underwriting Dashboard")