import reflex as rx
from src.ui.state import UnderwritingState


def data_ingestion_toolbar() -> rx.Component:
    """Thanh công cụ Data Ingestion & Multi-Client Selection chuẩn Notion-style."""
    return rx.box(
        rx.hstack(
            # CLUSTER 1: NGUỒN DỮ LIỆU & PIPELINE INGESTION
            rx.hstack(
                rx.hstack(
                    rx.icon("database", size=14, color="#38BDF8"),
                    rx.text("DATASET:", size="1", weight="bold", color="#94A3B8"),
                    spacing="1",
                    align="center",
                ),
                rx.select(
                    UnderwritingState.dataset_source_options,
                    value=UnderwritingState.selected_dataset_source_label,
                    on_change=UnderwritingState.handle_source_select,
                    size="1",
                    variant="surface",
                ),
                # Modal Upload File
                rx.dialog.root(
                    rx.dialog.trigger(
                        rx.button(
                            rx.icon("upload", size=13),
                            rx.text("Upload", size="1"),
                            size="1",
                            variant="outline",
                            color_scheme="gray",
                            cursor="pointer",
                        )
                    ),
                    rx.dialog.content(
                        rx.vstack(
                            rx.hstack(
                                rx.vstack(
                                    rx.heading("Custom Dataset Ingestion", size="3", color="white"),
                                    rx.text(
                                        "Upload CSV or Parquet file (single applicant profile or batch dataset)",
                                        size="1",
                                        color="#9CA3AF",
                                    ),
                                    spacing="0",
                                ),
                                rx.spacer(),
                                rx.dialog.close(
                                    rx.button(rx.icon("x", size=15), variant="ghost", color_scheme="gray", size="1")
                                ),
                                width="100%",
                                align="center",
                            ),
                            rx.divider(border_color="#1F2937", margin_y="1"),
                            rx.upload(
                                rx.vstack(
                                    rx.icon("file-up", size=32, color="#60A5FA"),
                                    rx.text("Click to browse or drag & drop file here", size="2", weight="bold", color="#F3F4F6"),
                                    rx.text("Supports .csv and .parquet format", size="1", color="#9CA3AF"),
                                    align="center",
                                    spacing="2",
                                    padding="6",
                                ),
                                id="custom_dataset_upload",
                                border="1px dashed #374151",
                                border_radius="8px",
                                background="#0D1117",
                                cursor="pointer",
                                width="100%",
                            ),
                            rx.hstack(
                                rx.foreach(
                                    rx.selected_files("custom_dataset_upload"),
                                    lambda f: rx.badge(rx.icon("file", size=12), f, color_scheme="blue", variant="surface", size="1"),
                                ),
                                width="100%",
                                wrap="wrap",
                                spacing="1",
                            ),
                            rx.hstack(
                                rx.dialog.close(
                                    rx.button("Cancel", variant="soft", color_scheme="gray", size="2")
                                ),
                                rx.spacer(),
                                rx.dialog.close(
                                    rx.button(
                                        rx.icon("arrow-up-right", size=15),
                                        "Ingest & Evaluate",
                                        size="2",
                                        variant="solid",
                                        color_scheme="blue",
                                        on_click=UnderwritingState.handle_file_upload(
                                            rx.upload_files(upload_id="custom_dataset_upload")
                                        ),
                                    )
                                ),
                                width="100%",
                                padding_top="2",
                            ),
                            spacing="3",
                            padding="4",
                            background="#111827",
                            border="1px solid #1F2937",
                            border_radius="10px",
                        ),
                        max_width="480px",
                    ),
                ),
                # Nút Run Pipeline
                rx.button(
                    rx.cond(
                        UnderwritingState.is_ingesting,
                        rx.hstack(rx.spinner(size="1"), rx.text("Running...", size="1"), spacing="1"),
                        rx.hstack(rx.icon("play", size=13), rx.text("Load / Run Pipeline", size="1", weight="bold"), spacing="1"),
                    ),
                    size="1",
                    variant="solid",
                    color_scheme="blue",
                    cursor="pointer",
                    on_click=UnderwritingState.run_pipeline,
                    disabled=UnderwritingState.is_ingesting,
                ),
                spacing="2",
                align="center",
            ),

            rx.divider(orientation="vertical", height="18px", border_color="#1E293B"),

            # CLUSTER 2: MULTI-CLIENT SELECTION & NAVIGATION
            rx.hstack(
                rx.hstack(
                    rx.icon("users", size=13, color="#A78BFA"),
                    rx.text("CLIENT ID:", size="1", weight="bold", color="#94A3B8"),
                    spacing="1",
                    align="center",
                ),
                rx.select(
                    UnderwritingState.client_id_options,
                    value=UnderwritingState.selected_client_id,
                    on_change=UnderwritingState.select_and_evaluate_client,
                    size="1",
                    variant="surface",
                    width="125px",
                ),
                rx.button(
                    rx.icon("chevron-left", size=13),
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                    cursor="pointer",
                    on_click=UnderwritingState.select_previous_client,
                    disabled=UnderwritingState.is_first_client,
                ),
                rx.button(
                    rx.icon("chevron-right", size=13),
                    size="1",
                    variant="ghost",
                    color_scheme="gray",
                    cursor="pointer",
                    on_click=UnderwritingState.select_next_client,
                    disabled=UnderwritingState.is_last_client,
                ),
                rx.badge(
                    rx.cond(
                        UnderwritingState.total_clients_count == 1,
                        "Single Record (1/1)",
                        f"{UnderwritingState.current_client_index_display} of {UnderwritingState.total_clients_count:,}",
                    ),
                    variant="surface",
                    color_scheme="gray",
                    size="1",
                ),
                spacing="2",
                align="center",
            ),

            rx.spacer(),

            # CLUSTER 3: TRẠNG THÁI ACTIVE DATASET / PIPELINE
            rx.hstack(
                rx.box(
                    width="6px",
                    height="6px",
                    border_radius="50%",
                    background=rx.cond(
                        UnderwritingState.is_loading,
                        "#F59E0B",
                        "#10B981",
                    ),
                ),
                rx.text(
                    rx.cond(
                        UnderwritingState.is_loading,
                        "Evaluating Risk Profile...",
                        UnderwritingState.active_source_label,
                    ),
                    size="1",
                    color="#94A3B8",
                    weight="medium",
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
            align="center",
            padding_x="6",
            padding_y="2",
            max_width="1600px",
            margin="0 auto",
        ),
        width="100%",
        background="#0B0F19",
        border_bottom="1px solid #1E293B",
    )
