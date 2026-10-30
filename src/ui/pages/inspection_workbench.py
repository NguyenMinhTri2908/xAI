"""Trang 2: Client Inspection Workbench."""
import reflex as rx
from src.state import UnderwritingState

# Import các components con
from src.ui.components.inspection_header import full_inspection_header
from src.ui.components.shap_card import shap_card_view
from src.ui.components.what_if import what_if_view
from src.ui.components.decision_notes import decision_notes_view
from src.ui.components.feature_search_view import feature_search_view
from src.ui.components.feature_drawer import feature_detail_drawer


def inspection_workbench_page() -> rx.Component:
    """Giao diện chính Trang 2: Client Inspection Workbench."""
    return rx.box(
        full_inspection_header(),

        # Khung nội dung chính 2 cột (Căn lề max_width 1600px đồng nhất)
        rx.box(
            rx.hstack(
                # CỘT TRÁI (70%): SHAP CHART + FEATURE IMPACT EXPLORER
                rx.vstack(
                    shap_card_view(),
                    rx.box(
                        feature_search_view(),
                        background="#0F172A",
                        border="1px solid #1E293B",
                        border_radius="12px",
                        box_shadow="0 4px 6px -1px rgba(0, 0, 0, 0.3)",
                        width="100%",
                    ),
                    spacing="4",
                    width="70%",
                ),

                # CỘT PHẢI (30%): TERMS SIMULATOR & DECISION NOTES
                rx.vstack(
                    what_if_view(),
                    decision_notes_view(),
                    spacing="4",
                    width="30%",
                    min_width="0",
                    max_width="30%",
                    overflow_x="hidden",
                ),
                width="100%",
                spacing="5",
                align_items="flex-start",
            ),
            max_width="1600px",
            margin="0 auto",
            padding_x="6",
            padding_y="5",
            width="100%",
        ),

        # Feature Detail Drawer
        feature_detail_drawer(),

        on_mount=UnderwritingState.load_demo_clients,
        width="100%",
        min_height="100vh",
        background="#090D16",
    )
