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


def production_dataset_row(item: dict) -> rx.Component:
    """Hàng dataset trong danh sách Thẻ 1 với Radio Check và validation badge."""
    is_selected = UnderwritingState.selected_production_file == item["filename"]
    return rx.box(
        rx.hstack(
            # Radio check icon (Active: Cyan ring with cyan dot; Inactive: Gray ring)
            rx.cond(
                is_selected,
                rx.box(
                    rx.box(
                        width="8px",
                        height="8px",
                        border_radius="50%",
                        background="#06B6D4",
                    ),
                    width="18px",
                    height="18px",
                    border_radius="50%",
                    border="2px solid #06B6D4",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    flex_shrink=0,
                ),
                rx.box(
                    width="18px",
                    height="18px",
                    border_radius="50%",
                    border="2px solid #475569",
                    flex_shrink=0,
                ),
            ),
            # Metadata cột & dòng
            rx.vstack(
                rx.hstack(
                    rx.text(
                        item["filename"],
                        size="2",
                        weight="bold",
                        color=rx.cond(is_selected, "#FFFFFF", "#E2E8F0"),
                        font_family="monospace",
                    ),
                    rx.badge(
                        item["format_tag"],
                        color_scheme="cyan",
                        variant="soft",
                        size="1",
                    ),
                    rx.badge(
                        item["status_badge"],
                        color_scheme=item["status_badge_color"],
                        variant="surface",
                        size="1",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    item["features_rows_label"],
                    size="1",
                    color=rx.cond(is_selected, "#94A3B8", "#64748B"),
                ),
                spacing="1",
                align_items="flex-start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        padding="3",
        border_radius="8px",
        cursor="pointer",
        border=rx.cond(
            is_selected,
            "1px solid #06B6D4",
            "1px solid #1E293B",
        ),
        background=rx.cond(
            is_selected,
            "rgba(6, 182, 212, 0.08)",
            "#0B0F17",
        ),
        _hover={
            "background": rx.cond(
                is_selected,
                "rgba(6, 182, 212, 0.12)",
                "rgba(255, 255, 255, 0.03)",
            ),
            "border_color": rx.cond(
                is_selected,
                "#06B6D4",
                "#334155",
            ),
        },
        transition="all 0.15s ease",
        on_click=UnderwritingState.set_selected_production_file(item["filename"]),
        width="100%",
    )


def preset_dataset_card() -> rx.Component:
    """Card 1 (Trái): 1. Preprocessed Datasets (Auto-scanned & Validated)."""
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
                    rx.text("1. Preprocessed Datasets", size="3", weight="bold", color="#F8FAFC"),
                    rx.text("Select a pre-computed dataset ready for instant risk scoring & xAI inspection.", size="1", color="#9CA3AF"),
                    spacing="0",
                    align_items="flex-start",
                ),
                spacing="3",
                align="center",
            ),
            rx.divider(border_color="#1E293B", margin_y="1"),

            # Danh sách Selectable List Cards
            rx.cond(
                UnderwritingState.has_production_datasets,
                rx.vstack(
                    rx.foreach(
                        UnderwritingState.production_datasets,
                        lambda item: production_dataset_row(item),
                    ),
                    spacing="2",
                    width="100%",
                ),
                # Empty State khi thư mục không có file
                rx.center(
                    rx.vstack(
                        rx.icon("folder-x", size=26, color="#64748B"),
                        rx.text(
                            "No processed datasets found in data/production directory.",
                            size="2",
                            color="#94A3B8",
                            text_align="center",
                        ),
                        spacing="2",
                        align="center",
                        padding_y="6",
                    ),
                    width="100%",
                    background="#0B0F17",
                    border="1px dashed #1E293B",
                    border_radius="8px",
                ),
            ),

            rx.spacer(),
            # Nút Load Selected Dataset (Xanh dương gradient kèm icon Play)
            rx.button(
                rx.cond(
                    UnderwritingState.is_ingesting,
                    rx.hstack(rx.spinner(size="2"), rx.text("Loading Dataset...", size="2"), spacing="2"),
                    rx.hstack(rx.icon("play", size=15), rx.text("Load Selected Dataset", size="2", weight="bold"), spacing="2"),
                ),
                size="2",
                variant="solid",
                style={
                    "background": "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
                    "color": "white",
                    "box_shadow": "0 2px 8px rgba(37, 99, 235, 0.35)",
                },
                cursor="pointer",
                width="100%",
                on_click=UnderwritingState.load_selected_production_dataset,
                disabled=UnderwritingState.is_ingesting | (~UnderwritingState.has_production_datasets),
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
    """Card 2 (Phải): 2. Custom File Ingestion (Dropzone + Size/Format Validation)."""
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
                    rx.text("Register an external CSV or Parquet dataset.", size="1", color="#9CA3AF"),
                    spacing="0",
                    align_items="flex-start",
                ),
                spacing="3",
                align="center",
            ),
            rx.divider(border_color="#1E293B", margin_y="1"),

            # Dropzone viền nét đứt
            rx.upload(
                rx.vstack(
                    rx.box(
                        rx.icon("cloud-upload", size=30, color="#818CF8"),
                        background="rgba(129, 140, 248, 0.1)",
                        border_radius="50%",
                        padding="2.5",
                    ),
                    rx.text("Drop your dataset here", size="3", weight="bold", color="#F3F4F6"),
                    rx.text("Drag & drop CSV or Parquet file here (Max 500MB)", size="1", color="#9CA3AF"),
                    align="center",
                    spacing="1",
                    padding_y="4",
                    padding_x="3",
                ),
                id="main_dataset_upload",
                accept={"text/csv": [".csv"], "application/octet-stream": [".parquet"]},
                max_files=1,
                border="1px dashed #4F46E5",
                border_radius="8px",
                background="#0B0F19",
                cursor="pointer",
                width="100%",
            ),

            # Chú thích kỹ thuật thực tế
            rx.text(
                "Supported Formats: .CSV, .PARQUET | Max File Size Enforced: 500MB",
                size="1",
                color="#64748B",
            ),

            # Chip hiển thị file upload đã chọn
            rx.foreach(
                rx.selected_files("main_dataset_upload"),
                lambda f: rx.box(
                    rx.hstack(
                        rx.hstack(
                            rx.icon("file-spreadsheet", size=14, color="#A78BFA"),
                            rx.text(f, size="2", weight="medium", color="#F1F5F9", font_family="monospace"),
                            spacing="2",
                            align="center",
                        ),
                        rx.spacer(),
                        rx.badge("READY", color_scheme="green", variant="solid", size="1"),
                        width="100%",
                        align="center",
                    ),
                    width="100%",
                    padding="2.5",
                    border_radius="6px",
                    background="#1E1B4B",
                    border="1px solid #4338CA",
                ),
            ),

            rx.spacer(),
            # Nút Upload & Ingest Dataset (Màu tím)
            rx.button(
                rx.cond(
                    UnderwritingState.is_ingesting,
                    rx.hstack(rx.spinner(size="2"), rx.text("Ingesting & Scoring...", size="2"), spacing="2"),
                    rx.hstack(rx.icon("cloud-upload", size=15), rx.text("Upload & Ingest Dataset →", size="2", weight="bold"), spacing="2"),
                ),
                size="2",
                variant="solid",
                style={
                    "background": "linear-gradient(135deg, #7C3AED 0%, #6D28D9 100%)",
                    "color": "white",
                    "box_shadow": "0 2px 8px rgba(124, 58, 237, 0.35)",
                },
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


def client_registry_table() -> rx.Component:
    """Bảng danh sách Client Registry hỗ trợ real-time filter và lazy loading (Feature Search Style).
    Khi chưa nạp dataset, hiển thị empty state gọn gàng nhẹ nhàng."""
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
                        disabled=~UnderwritingState.is_dataset_loaded,
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
                            UnderwritingState.is_dataset_loaded,
                            rx.cond(
                                UnderwritingState.total_clients_count == 1,
                                "1 Client",
                                f"{UnderwritingState.total_clients_count:,} Clients",
                            ),
                            "0 Clients",
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
                rx.cond(
                    UnderwritingState.is_dataset_loaded,
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
                    # Empty state gọn gàng nhẹ nhàng khi chưa nạp dataset
                    rx.center(
                        rx.hstack(
                            rx.icon("layers", size=18, color="#64748B"),
                            rx.text(
                                "No dataset loaded. Select a preprocessed dataset above or upload a custom file to view client records.",
                                size="2",
                                color="#94A3B8",
                            ),
                            spacing="2",
                            align="center",
                            padding_y="12",
                        ),
                        width="100%",
                    ),
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


def top_alert_banner() -> rx.Component:
    """Thanh Alert màu xanh lục đậm trên cùng: Icon chuông + Thông báo nạp thành công kèm nút đóng [x]."""
    return rx.cond(
        UnderwritingState.show_alert,
        rx.box(
            rx.hstack(
                rx.cond(
                    UnderwritingState.alert_type == "success",
                    rx.icon("bell", size=18, color="#34D399"),
                    rx.icon("circle_alert", size=18, color="#F87171"),
                ),
                rx.text(
                    UnderwritingState.alert_message,
                    size="2",
                    weight="medium",
                    color=rx.cond(
                        UnderwritingState.alert_type == "success",
                        "#A7F3D0",
                        "#FECACA",
                    ),
                ),
                rx.spacer(),
                rx.icon_button(
                    rx.icon("x", size=14, color=rx.cond(
                        UnderwritingState.alert_type == "success",
                        "#6EE7B7",
                        "#FCA5A5",
                    )),
                    size="1",
                    variant="ghost",
                    color_scheme=rx.cond(
                        UnderwritingState.alert_type == "success",
                        "green",
                        "red",
                    ),
                    cursor="pointer",
                    on_click=UnderwritingState.dismiss_alert,
                ),
                width="100%",
                align="center",
                spacing="3",
            ),
            background=rx.cond(
                UnderwritingState.alert_type == "success",
                "rgba(6, 78, 59, 0.65)",
                "rgba(127, 29, 29, 0.65)",
            ),
            border=rx.cond(
                UnderwritingState.alert_type == "success",
                "1px solid #059669",
                "1px solid #DC2626",
            ),
            border_radius="8px",
            padding_x="4",
            padding_y="2.5",
            width="100%",
            box_shadow="0 2px 10px rgba(0, 0, 0, 0.3)",
        ),
        rx.fragment(),
    )


def data_management_page() -> rx.Component:
    """Giao diện chính Trang 1: Data Ingestion & Dataset Management."""
    return rx.box(
        data_management_navbar(),
        rx.box(
            rx.vstack(
                # Thanh cảnh báo Alert trên cùng
                top_alert_banner(),

                # Phía trên: 2 Thẻ song song gọn gàng (Preset bên trái, Upload bên phải)
                rx.hstack(
                    preset_dataset_card(),
                    custom_upload_card(),
                    spacing="4",
                    width="100%",
                    align_items="stretch",
                ),

                # Phía dưới: Bảng Client Registry & Risk Overview (tự động hiển thị Empty State khi chưa nạp)
                client_registry_table(),

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
        on_mount=UnderwritingState.scan_production_dir,
    )
