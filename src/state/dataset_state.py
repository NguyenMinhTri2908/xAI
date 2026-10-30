import os
from pathlib import Path
from typing import List, Dict, Any
import reflex as rx
import pandas as pd
from .base_state import (
    BaseUnderwritingState,
    get_production_dir,
    get_unique_filepath,
    scan_production_datasets,
    INITIAL_PRODUCTION_DATASETS,
    INITIAL_SELECTED_FILE,
)
from src.data_processing.ingestion_service import (
    load_dataset_from_upload,
    set_active_dataset,
    get_active_dataset,
    get_active_client_ids,
    get_client_table_summary,
)


class DatasetState(BaseUnderwritingState):
    """Quản lý nạp file, danh sách khách hàng (Client Registry) và phân trang."""

    # Dữ liệu danh sách khách hàng và lựa chọn
    client_list: List[Dict[str, Any]] = []
    available_client_ids: List[str] = []
    total_clients_count: int = 0

    # Data Ingestion Toolbar State
    selected_dataset_source: str = "production"
    active_source_label: str = "No Dataset Loaded"

    # Production Datasets State
    production_datasets: List[Dict[str, Any]] = INITIAL_PRODUCTION_DATASETS
    selected_production_file: str = INITIAL_SELECTED_FILE

    # Quản lý hiển thị Client Registry (Trang 1)
    is_dataset_loaded: bool = False
    registry_display_limit: int = 35
    registry_search_query: str = ""

    def set_registry_search_query(self, query: str):
        """Lọc tìm kiếm Client ID theo thời gian thực (Real-time Filter)."""
        self.registry_search_query = query.strip()
        q = self.registry_search_query
        if q and self.is_dataset_loaded:
            if not any(q in str(r.get("SK_ID_CURR", "")) for r in self.client_list):
                df = get_active_dataset()
                if not df.empty and "SK_ID_CURR" in df.columns:
                    matches = df[df["SK_ID_CURR"].astype(str).str.contains(q, case=False, na=False)].head(20)
                    if not matches.empty:
                        from src.data_processing.ingestion_service import format_df_to_summary_records
                        extra = format_df_to_summary_records(matches)
                        self.client_list = extra + self.client_list

    def load_more_registry_clients(self):
        """Tải thêm dòng khi cuộn bảng Client Registry (Feature Search Style Lazy Scroll)."""
        if self.registry_display_limit < len(self.client_list):
            self.registry_display_limit += 25

    @rx.var
    def filtered_client_list(self) -> List[Dict[str, Any]]:
        """Lọc danh sách Client Registry theo ID tìm kiếm với giới hạn hiển thị tránh quá tải DOM."""
        if not self.is_dataset_loaded or not self.client_list:
            return []

        q = self.registry_search_query.strip().lower()
        if not q:
            return self.client_list[:self.registry_display_limit]

        matches = [
            row for row in self.client_list
            if q in str(row.get("SK_ID_CURR", "")).lower()
        ]
        return matches[:self.registry_display_limit]

    @rx.var
    def registry_scroll_status(self) -> str:
        """Thông báo trạng thái cuộn chuột ở cuối bảng."""
        if not self.is_dataset_loaded:
            return ""
        if self.registry_search_query.strip():
            return f"Showing {len(self.filtered_client_list)} matching records"
        if self.registry_display_limit < len(self.client_list):
            return f"Showing {self.registry_display_limit} of {len(self.client_list)} records • Scroll down to load more..."
        return f"Showing all {len(self.client_list)} loaded records"

    def clear_registry_search(self):
        self.registry_search_query = ""

    @rx.event
    def scan_production_dir(self):
        """Tự động quét thư mục data/production và cập nhật danh sách tập dữ liệu."""
        try:
            scanned = scan_production_datasets()
            self.production_datasets = scanned
            if scanned:
                if not self.selected_production_file or not any(d["filename"] == self.selected_production_file for d in scanned):
                    has_master = any(d["filename"] == "test_features_master.parquet" for d in scanned)
                    self.selected_production_file = "test_features_master.parquet" if has_master else scanned[0]["filename"]
            else:
                self.selected_production_file = ""
        except Exception as e:
            print(f"[DatasetState.scan_production_dir] Fallback exception: {e}")

    @rx.event
    def scan_production_datasets(self):
        """Alias cho scan_production_dir để tương thích ngược với các component frontend."""
        return self.scan_production_dir()

    @rx.event
    def set_selected_production_file(self, filename: str):
        """Người dùng click chọn một dataset trong danh sách Thẻ 1: tự động ẩn Alert cũ."""
        self.selected_production_file = str(filename)
        self.show_alert = False
        self.alert_token += 1

    @rx.var
    def active_dataset_badge_text(self) -> str:
        """Chuỗi hiển thị trên Tag/Badge Active Dataset của bảng Client Registry."""
        if not self.is_dataset_loaded or not self.selected_dataset_source:
            return "Active: None"
        return f"Active: {self.selected_dataset_source} | {self.total_clients_count:,} Records"

    @rx.var
    def has_production_datasets(self) -> bool:
        return len(self.production_datasets) > 0

    @rx.var
    def dataset_source_options(self) -> List[str]:
        if self.production_datasets:
            return [d["filename"] for d in self.production_datasets]
        return []

    @rx.var
    def selected_dataset_source_label(self) -> str:
        return self.selected_production_file if self.selected_production_file else "None Selected"

    def handle_source_select(self, val: str):
        self.selected_production_file = val

    async def load_selected_production_dataset(self):
        """Nạp tập dữ liệu được chọn từ Thẻ 1 (Preprocessed Datasets)."""
        if not self.selected_production_file:
            return

        self.is_ingesting = True
        yield
        try:
            prod_dir = get_production_dir()
            file_path = prod_dir / self.selected_production_file
            if not file_path.exists():
                self.alert_message = f"File not found in data/production: {self.selected_production_file}"
                self.alert_type = "error"
                self.show_alert = True
                self.status_message = self.alert_message
                self.is_ingesting = False
                return

            if self.selected_production_file.endswith(".parquet"):
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)

            if "SK_ID_CURR" not in df.columns:
                if df.index.name == "SK_ID_CURR":
                    df = df.reset_index()
                else:
                    df["SK_ID_CURR"] = range(100001, 100001 + len(df))

            source_label = f"{self.selected_production_file} ({len(df):,} records)"
            set_active_dataset(df, source_label)

            self.selected_dataset_source = self.selected_production_file
            self.active_source_label = source_label
            self.available_client_ids = get_active_client_ids()
            self.total_clients_count = len(self.available_client_ids)
            self.client_list = get_client_table_summary(100)
            self.registry_display_limit = 35
            self.is_dataset_loaded = True

            self.alert_token += 1
            current_token = self.alert_token
            self.alert_message = f"✓ Successfully loaded dataset: {self.selected_production_file} ({self.total_clients_count:,} records ready for inspection)"
            self.alert_type = "success"
            self.show_alert = True
            self.status_message = self.alert_message

            if self.available_client_ids:
                first_id = self.available_client_ids[0]
                yield
                if hasattr(self, "select_and_evaluate_client"):
                    yield type(self).select_and_evaluate_client(first_id)
                else:
                    from src.state.inspection_state import InspectionState
                    yield InspectionState.select_and_evaluate_client(first_id)

            yield type(self).auto_dismiss_alert(current_token)
        except Exception as e:
            self.alert_message = f"Error loading dataset: {str(e)}"
            self.alert_type = "error"
            self.show_alert = True
            self.status_message = self.alert_message
        finally:
            self.is_ingesting = False

    async def run_pipeline(self):
        """Kích hoạt pipeline nạp dữ liệu từ dataset đang chọn."""
        return await self.load_selected_production_dataset()

    async def handle_file_upload(self, files: List[rx.UploadFile]):
        """Xử lý nạp file CSV/Parquet tùy chỉnh do người dùng upload."""
        if not files:
            return

        file = files[0]
        fname = file.filename.lower()

        if not (fname.endswith(".csv") or fname.endswith(".parquet") or fname.endswith(".pq")):
            self.alert_message = "File size exceeds 500MB limit or unsupported format."
            self.alert_type = "error"
            self.show_alert = True
            self.status_message = self.alert_message
            return

        self.is_ingesting = True
        yield
        try:
            self.uploaded_file_name = file.filename
            file_bytes = await file.read()

            max_size_bytes = 500 * 1024 * 1024
            if len(file_bytes) > max_size_bytes:
                self.alert_message = "File size exceeds 500MB limit or unsupported format."
                self.alert_type = "error"
                self.show_alert = True
                self.status_message = self.alert_message
                self.is_ingesting = False
                return

            df, source_label = load_dataset_from_upload(file_bytes, file.filename)
            if df is None or df.empty:
                self.alert_message = f"File {file.filename} contained no valid data."
                self.alert_type = "error"
                self.show_alert = True
                self.status_message = self.alert_message
                self.is_ingesting = False
                return

            prod_dir = get_production_dir()
            os.makedirs(prod_dir, exist_ok=True)

            export_ext = ".parquet" if (fname.endswith(".csv") or fname.endswith(".parquet") or fname.endswith(".pq")) else Path(file.filename).suffix
            base_export_name = Path(file.filename).stem + export_ext

            unique_file_path = get_unique_filepath(prod_dir, base_export_name)
            saved_filename = unique_file_path.name

            if export_ext == ".parquet":
                df.to_parquet(unique_file_path, index=False)
            else:
                df.to_csv(unique_file_path, index=False)

            active_label = f"{saved_filename} ({len(df):,} records)"
            set_active_dataset(df, active_label)

            self.selected_dataset_source = saved_filename
            self.active_source_label = active_label
            self.available_client_ids = get_active_client_ids()
            self.total_clients_count = len(self.available_client_ids)
            self.client_list = get_client_table_summary(100)
            self.registry_display_limit = 35
            self.is_dataset_loaded = True
            self.upload_dialog_open = False

            self.scan_production_dir()
            self.selected_production_file = saved_filename

            self.alert_token += 1
            current_token = self.alert_token
            self.alert_message = f"✓ Dataset ingested & saved to data/production as {saved_filename}"
            self.alert_type = "success"
            self.show_alert = True
            self.status_message = self.alert_message

            if self.available_client_ids:
                first_id = self.available_client_ids[0]
                yield
                if hasattr(self, "select_and_evaluate_client"):
                    yield type(self).select_and_evaluate_client(first_id)
                else:
                    from src.state.inspection_state import InspectionState
                    yield InspectionState.select_and_evaluate_client(first_id)

            yield type(self).auto_dismiss_alert(current_token)
        except Exception as e:
            self.alert_message = f"Error processing uploaded file: {str(e)}"
            self.alert_type = "error"
            self.show_alert = True
            self.status_message = self.alert_message
        finally:
            self.is_ingesting = False

