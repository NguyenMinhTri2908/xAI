import reflex as rx

def header_view() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Khối thông tin định danh hồ sơ
            rx.vstack(
                rx.hstack(
                    rx.badge("#LN-2026-8891", color_scheme="blue", variant="surface", size="2"),
                    rx.text("Trần Văn A", font_weight="bold", size="4", color="white"),
                    rx.badge("Age: 34", variant="soft", color_scheme="gray"),
                    align="center",
                    spacing="2",
                ),
                rx.text(
                    "Applied: Consumer Loan • Commercial Associate",
                    color="#9CA3AF",
                    size="2",
                ),
                spacing="1",
                align_items="flex-start",
            ),
            # Khối thông số khoản vay & Phân loại rủi ro
            rx.hstack(
                rx.vstack(
                    rx.text("LOAN TERMS", size="1", color="#9CA3AF", font_weight="bold"),
                    rx.text("$25,000 / 24 mos", font_weight="bold", size="3", color="white"),
                    rx.text("Suggested Rate: 11.2% APR (Tier B)", size="1", color="#9CA3AF"),
                    align_items="flex-end",
                    spacing="0",
                ),
                rx.divider(orientation="vertical", size="2", color_scheme="gray"),
                rx.vstack(
                    rx.badge("PD: 4.8%", color_scheme="amber", size="3", variant="solid"),
                    rx.text("Cut-off: 5.5%", size="1", color="#9CA3AF"),
                    align_items="center",
                    spacing="0",
                ),
                spacing="4",
                align="center",
            ),
            justify="between",
            width="100%",
            padding_x="6",
            padding_y="4",
            background="#111827",
            border_bottom="1px solid #1F2937",
        ),
        width="100%",
    )