"""Component Slide-Over Queue Drawer bên trái cho màn hình Client Inspection Workbench.

Được thiết kế theo chuẩn Controlled Dialog Slide-Over (tương tự feature_detail_drawer),
loại bỏ hoàn toàn rx.drawer.root (Vaul) chống kẹt pointer-events và đóng tức thì khi chọn hồ sơ.
"""
import reflex as rx
from src.state import UnderwritingState


def render_queue_client_item(row: rx.Var[dict]) -> rx.Component:
    """Render một thẻ hồ sơ khách hàng trong danh sách Queue Drawer."""
    is_active = row["SK_ID_CURR"] == UnderwritingState.selected_client_id

    return rx.box(
        rx.hstack(
            # Cụm trái: Mã hồ sơ + Hạn mức & Kỳ hạn
            rx.vstack(
                rx.hstack(
                    rx.text(
                        f"#{row['SK_ID_CURR']}",
                        size="2",
                        weight="bold",
                        color=rx.cond(is_active, "#38BDF8", "#F8FAFC"),
                        font_family="monospace",
                    ),
                    rx.cond(
                        is_active,
                        rx.badge("Active", size="1", color_scheme="blue", variant="solid"),
                        rx.fragment(),
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.text(
                        row["AMT_CREDIT_DISPLAY"],
                        size="1",
                        color="#94A3B8",
                        font_family="monospace",
                    ),
                    rx.text("·", size="1", color="#475569"),
                    rx.text(
                        row["TERM_DISPLAY"],
                        size="1",
                        color="#94A3B8",
                    ),
                    spacing="1",
                    align="center",
                ),
                spacing="1",
                align_items="flex-start",
            ),
            rx.spacer(),
            # Cụm phải: Quyết định thẩm định + Xác suất vỡ nợ (PD)
            rx.vstack(
                rx.badge(
                    row["DECISION"],
                    color_scheme=rx.cond(
                        row["DECISION_COLOR"] == "green",
                        "green",
                        rx.cond(row["DECISION_COLOR"] == "amber", "amber", "red"),
                    ),
                    variant="surface",
                    size="1",
                ),
                rx.text(
                    f"PD: {row['PD_DISPLAY']}",
                    size="1",
                    color="#94A3B8",
                    font_family="monospace",
                ),
                spacing="1",
                align_items="flex-end",
            ),
            width="100%",
            align="center",
            padding_x="3",
            padding_y="2",
        ),
        width="100%",
        border_radius="8px",
        background=rx.cond(
            is_active,
            "rgba(56, 189, 248, 0.10)",
            "rgba(15, 23, 42, 0.6)",
        ),
        border=rx.cond(
            is_active,
            "1px solid #38BDF8",
            "1px solid #1E293B",
        ),
        cursor="pointer",
        transition="all 0.15s ease",
        _hover={
            "background": rx.cond(
                is_active,
                "rgba(56, 189, 248, 0.15)",
                "#1E293B",
            ),
            "border_color": rx.cond(
                is_active,
                "#38BDF8",
                "#334155",
            ),
        },
        on_click=UnderwritingState.select_client_from_queue(row["SK_ID_CURR"]),
    )


def queue_drawer() -> rx.Component:
    """Slide-over Queue Drawer neo cố định cạnh trái màn hình, điều khiển tường minh qua State."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # 1. Header Drawer: Tiêu đề + Số lượng + Nút đóng
                rx.hstack(
                    rx.hstack(
                        rx.box(
                            rx.icon("panel-left", size=16, color="#38BDF8"),
                            background="rgba(56, 189, 248, 0.12)",
                            padding="2",
                            border_radius="8px",
                        ),
                        rx.vstack(
                            rx.hstack(
                                rx.heading("Applications Queue", size="3", color="#F8FAFC", weight="bold"),
                                rx.badge(
                                    UnderwritingState.queue_count_display,
                                    color_scheme="blue",
                                    variant="surface",
                                    size="1",
                                ),
                                spacing="2",
                                align="center",
                            ),
                            rx.text("Click any client profile to inspect", size="1", color="#94A3B8"),
                            spacing="0",
                            align_items="flex-start",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon_button(
                            rx.icon("x", size=16, color="#94A3B8"),
                            variant="ghost",
                            color_scheme="gray",
                            size="1",
                            cursor="pointer",
                            border_radius="6px",
                            on_click=UnderwritingState.close_queue_drawer,
                        )
                    ),
                    width="100%",
                    align="center",
                    padding_bottom="2",
                ),

                # 2. Thanh tìm kiếm lọc nhanh theo Client ID
                rx.hstack(
                    rx.input(
                        rx.input.slot(rx.icon("search", size=14, color="#94A3B8")),
                        placeholder="Search Client ID (e.g. 100001)...",
                        value=UnderwritingState.queue_search_query,
                        on_change=UnderwritingState.set_queue_search_query,
                        size="2",
                        width="100%",
                    ),
                    rx.cond(
                        UnderwritingState.queue_search_query != "",
                        rx.icon_button(
                            rx.icon("x", size=14),
                            size="2",
                            variant="surface",
                            color_scheme="gray",
                            cursor="pointer",
                            on_click=UnderwritingState.clear_queue_search,
                        ),
                        rx.fragment(),
                    ),
                    width="100%",
                    spacing="2",
                    align="center",
                ),

                rx.divider(border_color="#1E293B"),

                # 3. Danh sách cuộn chứa các hồ sơ
                rx.box(
                    rx.vstack(
                        rx.foreach(
                            UnderwritingState.filtered_queue_list,
                            render_queue_client_item,
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    width="100%",
                    height="calc(100vh - 155px)",
                    overflow_y="auto",
                    overflow_x="hidden",
                    padding_right="1",
                ),

                spacing="3",
                width="100%",
                height="100%",
                padding="4",
                background="#0B0F19",
            ),
            position="fixed",
            top="0",
            left="0",
            bottom="0",
            right="auto",
            margin="0",
            width="380px",
            min_width="320px",
            max_width="90vw",
            height="100vh",
            max_height="100vh",
            background="#0B0F19",
            border_right="1px solid #1E293B",
            box_shadow="12px 0 36px rgba(0, 0, 0, 0.7)",
            border_radius="0",
            outline="none",
            padding="0",
            overflow="hidden",
        ),
        open=UnderwritingState.is_queue_open,
        on_open_change=UnderwritingState.close_queue_drawer,
    )

