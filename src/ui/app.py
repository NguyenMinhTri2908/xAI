import reflex as rx

# Import hai trang chính của kiến trúc Multi-Page
from src.ui.pages.data_management import data_management_page
from src.ui.pages.inspection_workbench import inspection_workbench_page

# Đăng ký tường minh toàn bộ Application States vào State Registry
from src.ui.state import UnderwritingState
from src.ui.drawer_state import FeatureDrawerState
from src.ui.feature_search_state import FeatureSearchState

# Re-export index để tương thích ngược
index = data_management_page

# Khởi tạo Reflex Application
app = rx.App()

# TRANG 1: DATA INGESTION & DATASET MANAGEMENT (Trang chủ và /data)
app.add_page(
    data_management_page,
    route="/",
    title="Data Management & Registry | xAI Credit Scoring",
    on_load=UnderwritingState.scan_production_dir,
)
app.add_page(
    data_management_page,
    route="/data",
    title="Data Management & Registry | xAI Credit Scoring",
    on_load=UnderwritingState.scan_production_dir,
)

# TRANG 2: CLIENT INSPECTION WORKBENCH (/inspection)
app.add_page(
    inspection_workbench_page,
    route="/inspection",
    title="Client Inspection Workbench | xAI Credit Scoring",
)