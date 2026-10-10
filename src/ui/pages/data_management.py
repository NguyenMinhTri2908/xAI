import reflex as rx
from src.ui.state import UnderwritingState


def data_management_navbar() -> rx.Component:
    """Navbar trên cùng của Trang Data Management."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon("landmark", size=16, color="#38BDF8"),
                rx.text(
                    "Credit Underwriting",
                    size="2",
                    weight="bold",
                    color="#F8FAFC",
                ),
                rx.text("/", size="2", color="#475569"),
                rx.text("Data Ingestion & Dataset Registry", size="2", color="#94A3B8"),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.hstack(
                rx.cond(
                    UnderwritingState.is_dataset_loaded,
                    rx.badge(
                        rx.hstack(
                            rx.box(width="6px", height="6px", border_radius="50%", background="#10B981"),
                            rx.text(UnderwritingState.active_source_label, size="1"),
                            spacing="1",
                            align="center",
                        ),
                        color_scheme="gray",
                        variant="surface",
                        size="1",
                    ),
                    rx.badge(
                        rx.hstack(
                            rx.box(width="6px", height="6px", border_radius="50%", background="#94A3B8"),
                            rx.text("No Dataset Loaded", size="1"),
                            spacing="1",
                            align="center",
                        ),
                        color_scheme="gray",
                        variant="surface",
                        size="1",
                    ),
                ),
                rx.button(
                    rx.hstack(
                        rx.text("Go to Inspection Workbench", size="2", weight="bold"),
                        rx.icon("arrow-right", size=15),
                        spacing="2",
                        align="center",
                    ),
                    variant="solid",
                    color_scheme="blue",
                    size="2",
                    cursor="pointer",
                    on_click=rx.redirect("/inspection"),
                ),
                spacing="3",
                align="center",
            ),
            justify="between",
            width="100%",
            align="center",
            max_width="1600px",
            margin="0 auto",
            padding_x="6",
            padding_y="3",
        ),
        width="100%",
        background="#0D1117",
        border_bottom="1px solid #1E293B",
    )


def preset_dataset_card() -> rx.Component:
    """Card 1 (Trái): Bộ chọn Preset Dataset có sẵn."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon("database", size=18, color="#38BDF8"),
                    background="rgba(56, 189, 248, 0.12)",
                    padding="2",
                    border_radius="8px",
                ),
                rx.vstack(
                    rx.text("1. Benchmark Preset Datasets", size="3", weight="bold", color="#F8FAFC"),
                    rx.text("Choose from pre-computed master or benchmark raw datasets", size="1", color="#9CA3AF"),
                    spacing="0",
                    align_items="flex-start",
                ),
                spacing="3",
                align="center",
            ),
            rx.divider(border_color="#1E293B", margin_y="1"),
            rx.vstack(
                rx.text("AVAILABLE PRESETS", size="1", weight="bold", color="#9CA3AF", letter_spacing="0.05em"),
                rx.select(
                    UnderwritingState.dataset_source_options,
                    value=UnderwritingState.selected_dataset_source_label,
                    on_change=UnderwritingState.handle_source_select,
                    size="2",
                    variant="surface",
                    width="100%",
                ),
                spacing="1",
                width="100%",
                align_items="flex-start",
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon("check", size=13, color="#10B981"),
                        rx.text("Demo 1,000 Clients: Pre-computed 891 features with full joins", size="1", color="#94A3B8"),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.icon("check", size=13, color="#10B981"),
                        rx.text("Full Test Master: Production scoring pool (48,744 applicant records)", size="1", color="#94A3B8"),
                        spacing="2",
                        align="center",
                    ),
                    rx.hstack(
                        rx.icon("check", size=13, color="#10B981"),
                        rx.text("Raw Application Test: Runs automatic zero-leakage pipeline transformations", size="1", color="#94A3B8"),
                        spacing="2",
                        align="center",
                    ),
                    spacing="1",
                    width="100%",
                ),
                background="#0B0F17",
                border="1px solid #1E293B",
                border_radius="8px",
                padding="3",
                width="100%",
            ),
            rx.spacer(),
            rx.button(
                rx.cond(
                    UnderwritingState.is_ingesting,
                    rx.hstack(rx.spinner(size="2"), rx.text("Processing Pipeline...", size="2"), spacing="2"),
                    rx.hstack(rx.icon("play", size=15), rx.text("Load & Run Pipeline", size="2", weight="bold"), spacing="2"),
                ),
                size="2",
                variant="solid",
                color_scheme="blue",
                cursor="pointer",
                width="100%",
                on_click=UnderwritingState.run_pipeline,
                disabled=UnderwritingState.is_ingesting,
            ),
            spacing="3",
            width="100%",
            height="100%",
        ),
        background="#111827",
        border="1px solid #1F2937",
        border_radius="10px",
        padding="5",
        flex="1",
        width="100%",
    )


def custom_upload_card() -> rx.Component:
    """Card 2 (Phải): Upload file CSV / Parquet tùy chỉnh."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon("cloud-upload", size=18, color="#A78BFA"),
                    background="rgba(167, 139, 250, 0.12)",
                    padding="2",
                    border_radius="8px",
                ),
                rx.vstack(
                    rx.text("2. Custom File Ingestion", size="3", weight="bold", color="#F8FAFC"),
                    rx.text("Upload CSV / Parquet file (Dataset auto-named after file)", size="1", color="#9CA3AF"),
                    spacing="0",
                    align_items="flex-start",
                ),
                spacing="3",
                align="center",
            ),
            rx.divider(border_color="#1E293B", margin_y="1"),
            # Dropzone
            rx.upload(
                rx.vstack(
                    rx.icon("file-up", size=30, color="#818CF8"),
                    rx.text("Browse or drag & drop CSV or Parquet file here", size="2", weight="bold", color="#F3F4F6"),
                    rx.text("Supports single loan application record or batch datasets", size="1", color="#9CA3AF"),
                    align="center",
                    spacing="1",
                    padding="4",
                ),
                id="main_dataset_upload",
                border="1px dashed #374151",
                border_radius="8px",
                background="#0B0F19",
                cursor="pointer",
                width="100%",
            ),
            # Danh sách file đã chọn
            rx.hstack(
                rx.foreach(
                    rx.selected_files("main_dataset_upload"),
                    lambda f: rx.badge(rx.icon("file", size=12), f, color_scheme="indigo", variant="surface", size="1"),
                ),
                width="100%",
                wrap="wrap",
                spacing="1",
            ),
            rx.spacer(),
            rx.button(
                rx.cond(
                    UnderwritingState.is_ingesting,
                    rx.hstack(rx.spinner(size="2"), rx.text("Ingesting & Scoring...", size="2"), spacing="2"),
                    rx.hstack(rx.icon("arrow-up-right", size=15), rx.text("Upload & Ingest Dataset", size="2", weight="bold"), spacing="2"),
                ),
                size="2",
                variant="solid",
                color_scheme="indigo",
                cursor="pointer",
                width="100%",
                on_click=UnderwritingState.handle_file_upload(
                    rx.upload_files(upload_id="main_dataset_upload")
                ),
                disabled=UnderwritingState.is_ingesting,
            ),
            spacing="3",
            width="100%",
            height="100%",
        ),
        background="#111827",
        border="1px solid #1F2937",
        border_radius="10px",
        padding="5",
        flex="1",
        width="100%",
    )


def empty_waiting_view() -> rx.Component:
    """Trạng thái chờ ban đầu khi chưa nạp Dataset."""
    return rx.center(
        rx.vstack(
            rx.box(
                rx.icon("layers", size=36, color="#64748B"),
                background="rgba(255, 255, 255, 0.03)",
                padding="4",
                border_radius="50%",
                border="1px dashed #334155",
            ),
            rx.text(
                "Select a dataset above to display client records",
                size="4",
                weight="bold",
                color="#F1F5F9",
            ),
            rx.text(
                "Choose a benchmark preset on the left or upload a custom CSV / Parquet file on the right, then click 'Load & Run Pipeline' to inspect client default risk.",
                size="2",
                color="#94A3B8",
                text_align="center",
                max_width="520px",
                line_height="1.6",
            ),
            rx.button(
                rx.hstack(
                    rx.icon("play", size=14),
                    rx.text("Quick Load Demo Preset (1,000 Clients)", size="2", weight="bold"),
                    spacing="2",
                    align="center",
                ),
                size="2",
                variant="soft",
                color_scheme="blue",
                cursor="pointer",
                on_click=UnderwritingState.run_pipeline,
                margin_top="2",
            ),
            align="center",
            spacing="2",
            padding_y="12",
        ),
        width="100%",
        border="1px dashed #1E293B",
        border_radius="12px",
        background="#0B0F19",
        padding="8",
    )


def client_registry_table() -> rx.Component:
    """Bảng danh sách Client Registry hỗ trợ real-time filter và lazy loading (Feature Search Style)."""
    return rx.box(
        rx.vstack(
            # Thanh công cụ bảng: Tiêu đề + Bộ tìm kiếm Real-time
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("users", size=16, color="#38BDF8"),
                        rx.heading("Client Registry & Risk Overview", size="3", color="#FFFFFF"),
                        spacing="2",
                        align="center",
                    ),
                    rx.text(
                        "Browse applicant profiles in current active dataset. Click 'Inspect Client' to examine credit scoring and SHAP attribution.",
                        size="1",
                        color="#9CA3AF",
                    ),
                    spacing="0",
                    align_items="flex-start",
                ),
                rx.spacer(),
                rx.hstack(
                    # Ô tìm kiếm Real-time theo Client ID
                    rx.input(
                        rx.input.slot(rx.icon("search", size=14, color="#9CA3AF")),
                        placeholder="Filter by Client ID (e.g. 100001)...",
                        value=UnderwritingState.registry_search_query,
                        on_change=UnderwritingState.set_registry_search_query,
                        size="2",
                        width="260px",
                    ),
                    rx.cond(
                        UnderwritingState.registry_search_query != "",
                        rx.button(
                            rx.icon("x", size=12),
                            size="1",
                            variant="ghost",
                            color_scheme="gray",
                            on_click=UnderwritingState.clear_registry_search,
                            cursor="pointer",
                        ),
                        rx.fragment(),
                    ),
                    rx.badge(
                        rx.cond(
                            UnderwritingState.total_clients_count == 1,
                            "1 Client",
                            f"{UnderwritingState.total_clients_count:,} Clients",
                        ),
                        variant="surface",
                        color_scheme="blue",
                        size="2",
                    ),
                    spacing="2",
                    align="center",
                ),
                width="100%",
                align="center",
                padding_y="2",
            ),

            # Khung bảng Container Scroll chuẩn Feature Search Style (max_height 500px, overflow_y auto)
            rx.box(
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("CLIENT ID", width="15%"),
                            rx.table.column_header_cell("DEFAULT RISK (PD)", width="15%"),
                            rx.table.column_header_cell("RATING TIER", width="11%"),
                            rx.table.column_header_cell("RECOMMENDATION", width="15%"),
                            rx.table.column_header_cell("TOTAL INCOME", width="14%"),
                            rx.table.column_header_cell("LOAN AMOUNT", width="14%"),
                            rx.table.column_header_cell("ANNUITY", width="11%"),
                            rx.table.column_header_cell("ACTION", width="10%"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            UnderwritingState.filtered_client_list,
                            lambda row: rx.table.row(
                                # CLIENT ID
                                rx.table.cell(
                                    rx.hstack(
                                        rx.icon("user", size=13, color="#9CA3AF"),
                                        rx.text(
                                            f"#{row['SK_ID_CURR']}",
                                            weight="bold",
                                            size="2",
                                            color="#FFFFFF",
                                            font_family="monospace",
                                        ),
                                        spacing="1",
                                        align="center",
                                    )
                                ),
                                # DEFAULT RISK (PD)
                                rx.table.cell(
                                    rx.badge(
                                        row["PD_DISPLAY"],
                                        color_scheme=rx.cond(
                                            row["PD_COLOR"] == "#10B981",
                                            "green",
                                            rx.cond(row["PD_COLOR"] == "#F59E0B", "amber", "red"),
                                        ),
                                        variant="surface",
                                        size="1",
                                    )
                                ),
                                # RATING TIER
                                rx.table.cell(
                                    rx.badge(row["TIER"], variant="soft", color_scheme="gray", size="1")
                                ),
                                # RECOMMENDATION
                                rx.table.cell(
                                    rx.text(row["DECISION"], size="1", weight="medium", color="#E2E8F0")
                                ),
                                # TOTAL INCOME
                                rx.table.cell(
                                    rx.text(row["INCOME_DISPLAY"], size="1", color="#CBD5E1")
                                ),
                                # LOAN AMOUNT
                                rx.table.cell(
                                    rx.text(row["CREDIT_DISPLAY"], size="1", weight="medium", color="#FFFFFF")
                                ),
                                # ANNUITY
                                rx.table.cell(
                                    rx.text(row["ANNUITY_DISPLAY"], size="1", color="#94A3B8")
                                ),
                                # ACTION (Inspect Client Button)
                                rx.table.cell(
                                    rx.button(
                                        rx.hstack(
                                            rx.text("Inspect", size="1", weight="bold"),
                                            rx.icon("arrow-right", size=12),
                                            spacing="1",
                                            align="center",
                                        ),
                                        size="1",
                                        variant="solid",
                                        color_scheme="blue",
                                        cursor="pointer",
                                        on_click=UnderwritingState.inspect_client(row["SK_ID_CURR"]),
                                    )
                                ),
                                style={
                                    "transition": "background 0.15s ease",
                                    "_hover": {"background": "rgba(56, 189, 248, 0.06)"},
                                },
                            ),
                        ),
                        # Dòng thông báo trạng thái cuộn nhẹ ở cuối danh sách (Lazy Scroll status)
                        rx.table.row(
                            rx.table.cell(
                                rx.center(
                                    rx.text(
                                        UnderwritingState.registry_scroll_status,
                                        size="1",
                                        color="#64748B",
                                    ),
                                    padding="2",
                                    width="100%",
                                ),
                                col_span=8,
                            )
                        ),
                    ),
                    width="100%",
                    variant="surface",
                    size="2",
                ),
                max_height="500px",
                overflow_y="auto",
                width="100%",
                border="1px solid #1E293B",
                border_radius="10px",
                background="#0B0F19",
                on_scroll=UnderwritingState.load_more_registry_clients,
            ),
            spacing="3",
            width="100%",
        ),
        background="#111827",
        border="1px solid #1F2937",
        border_radius="12px",
        padding="5",
        width="100%",
        box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.3)",
    )


def data_management_page() -> rx.Component:
    """Giao diện chính Trang 1: Data Ingestion & Dataset Management."""
    return rx.box(
        data_management_navbar(),
        rx.box(
            rx.vstack(
                # Thông báo status nếu có
                rx.cond(
                    UnderwritingState.status_message != "",
                    rx.box(
                        rx.hstack(
                            rx.icon("info", size=16, color="#60A5FA"),
                            rx.text(UnderwritingState.status_message, size="2", color="#93C5FD"),
                            spacing="2",
                            align="center",
                        ),
                        background="rgba(37, 99, 235, 0.12)",
                        border="1px solid rgba(59, 130, 246, 0.3)",
                        border_radius="8px",
                        padding="3",
                        width="100%",
                    ),
                    rx.fragment(),
                ),

                # Phía trên: 2 Thẻ song song gọn gàng (Preset bên trái, Upload bên phải)
                rx.hstack(
                    preset_dataset_card(),
                    custom_upload_card(),
                    spacing="4",
                    width="100%",
                    align_items="stretch",
                ),

                # Phía dưới: Trạng thái chờ ban đầu HOẶC Bảng Client Registry sau khi nạp
                rx.cond(
                    UnderwritingState.is_dataset_loaded,
                    client_registry_table(),
                    empty_waiting_view(),
                ),

                spacing="5",
                width="100%",
            ),
            max_width="1600px",
            margin="0 auto",
            padding_x="6",
            padding_y="5",
            width="100%",
        ),
        width="100%",
        min_height="100vh",
        background="#090D16",
    )
