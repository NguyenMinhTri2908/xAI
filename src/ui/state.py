import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Union
from .feature_search_state import FeatureSearchState
from src.ui.utils.formatters import format_client_age, format_client_experience

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import reflex as rx
import pandas as pd
import pyarrow.parquet as pq
from src.engine.credit_scoring import CreditScoringEngine
from src.pricing.pricing_engine import pricing_engine
from src.config.pricing_config import retail_pricing_config
from src.data_processing.ingestion_service import (
    load_dataset_from_source,
    load_dataset_from_upload,
    set_active_dataset,
    get_active_dataset,
    get_active_client_ids,
    get_client_row_data,
    get_client_table_summary,
)

_ENGINE = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = CreditScoringEngine()
    return _ENGINE


def get_production_dir() -> Path:
    """Xác định chính xác thư mục data/production qua multi-path check và đảm bảo thư mục tồn tại."""
    candidates = [
        Path("/Users/nguyenminhtri/FinalYearPro/data/production"),
        PROJECT_ROOT / "data" / "production",
        Path("data/production").resolve(),
    ]
    for p in candidates:
        if p.exists() and p.is_dir():
            return p
    fallback = PROJECT_ROOT / "data" / "production"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_unique_filepath(directory: Union[Path, str], filename: str) -> Path:
    """Kiểm tra và trả về đường dẫn file duy nhất không bị trùng lặp trong thư mục data/production.
    Nếu filename đã tồn tại (ví dụ: application_test.parquet), tự động thêm hậu tố _1, _2, _3...
    trước phần mở rộng (ví dụ: application_test_1.parquet, application_test_2.parquet).
    Đảm bảo tuyệt đối KHÔNG BAO GIỜ ghi đè (Never overwrite) lên dữ liệu cũ đã có.
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)

    target_path = dir_path / filename
    if not target_path.exists():
        return target_path

    stem = target_path.stem
    suffix = target_path.suffix

    counter = 1
    while True:
        candidate_name = f"{stem}_{counter}{suffix}"
        candidate_path = dir_path / candidate_name
        if not candidate_path.exists():
            return candidate_path
        counter += 1


def scan_production_datasets() -> List[Dict[str, Any]]:
    """Tự động quét DUY NHẤT thư mục data/production, đọc metadata và kiểm tra pipeline readiness.
    Tuyệt đối không quét hay liệt kê các file trong thư mục gốc data/."""
    prod_dir = get_production_dir()
    os.makedirs(prod_dir, exist_ok=True)

    if not prod_dir.exists():
        return []

    datasets = []
    try:
        files = sorted([
            f for f in os.listdir(prod_dir)
            if (f.endswith(".parquet") or f.endswith(".csv")) and not f.startswith(".")
        ])
    except Exception as e:
        print(f"[scan_production_datasets] Error listing {prod_dir}: {e}")
        return []

    for f in files:
        fpath = prod_dir / f
        ext = ".parquet" if f.endswith(".parquet") else ".csv"
        num_rows = 0
        num_cols = 0
        has_sk_id = False
        has_features = False

        try:
            if ext == ".parquet":
                meta = pq.ParquetFile(fpath)
                num_rows = meta.metadata.num_rows
                cols = meta.schema.names
                num_cols = len(cols)
                has_sk_id = "SK_ID_CURR" in cols
                has_features = any(c in cols for c in ["EXT_SOURCE_MEAN", "AMT_CREDIT", "AMT_INCOME_TOTAL", "EXT_SOURCE_2", "TARGET", "PD"])
            else:
                df_head = pd.read_csv(fpath, nrows=1)
                cols = list(df_head.columns)
                num_cols = len(cols)
                has_sk_id = "SK_ID_CURR" in cols
                has_features = any(c in cols for c in ["EXT_SOURCE_MEAN", "AMT_CREDIT", "AMT_INCOME_TOTAL", "EXT_SOURCE_2", "TARGET", "PD"])
                with open(fpath, "r", encoding="utf-8") as cf:
                    num_rows = max(sum(1 for _ in cf) - 1, 0)
        except Exception as e:
            print(f"[scan_production_datasets] Error reading {f}: {e}")
            continue

        is_validated = has_sk_id and has_features
        status_badge = "✓ Validated & Ready" if is_validated else "⚠️ Raw / Needs Pipeline"
        status_badge_color = "green" if is_validated else "amber"

        feat_count = num_cols - 1 if has_sk_id else num_cols
        feat_count_label = f"{feat_count} Features" if feat_count > 0 else f"{num_cols} Columns"
        rows_label = f"{num_rows:,} Rows"

        datasets.append({
            "filename": f,
            "id": f,
            "path": str(fpath),
            "format_tag": ext,
            "features_count": feat_count_label,
            "rows_count": rows_label,
            "features_rows_label": f"{feat_count_label} / {rows_label}",
            "is_validated": is_validated,
            "status_badge": status_badge,
            "status_badge_color": status_badge_color,
        })

    return datasets


INITIAL_PRODUCTION_DATASETS: List[Dict[str, Any]] = scan_production_datasets()
INITIAL_SELECTED_FILE: str = (
    "test_features_master.parquet"
    if any(d["filename"] == "test_features_master.parquet" for d in INITIAL_PRODUCTION_DATASETS)
    else (INITIAL_PRODUCTION_DATASETS[0]["filename"] if INITIAL_PRODUCTION_DATASETS else "")
)


DEFAULT_RECOMMENDED_OPTION: Dict[str, Any] = {
    "title": "Recommended Proposal",
    "opt_type": "recommended",
    "credit": 0.0,
    "term": 12,
    "annuity": 0.0,
    "dti": 0.0,
    "pd": 0.0,
    "tier": "None",
    "decision": "None",
    "factor": 1.0,
    "credit_display": "$0",
    "credit_delta_text": "",
    "credit_delta_color": "#94A3B8",
    "term_display": "12 Months",
    "term_delta_text": "",
    "term_delta_color": "#94A3B8",
    "annuity_display": "$0 / mo",
    "annuity_val_color": "#F8FAFC",
    "annuity_delta_text": "",
    "annuity_delta_color": "#94A3B8",
    "dti_display": "0.0%",
    "dti_val_color": "#34D399",
    "dti_delta_text": "",
    "dti_delta_color": "#94A3B8",
    "pd_display": "0.00%",
    "pd_color": "#34D399",
    "pd_delta_text": "",
    "pd_delta_color": "#34D399",
    "offered_rate": 12.0,
    "rate_display": "12.00%",
    "rate_delta_text": "",
    "rate_delta_color": "#94A3B8",
}


class UnderwritingState(rx.State):
    """Reflex state quản lý Data Ingestion, chọn hồ sơ và thẩm định tín dụng."""

    # Dữ liệu danh sách khách hàng và lựa chọn
    client_list: List[Dict[str, Any]] = []
    available_client_ids: List[str] = []
    selected_client_id: str = ""
    total_clients_count: int = 0
    is_loading: bool = False

    # Data Ingestion Toolbar State
    selected_dataset_source: str = "production"
    active_source_label: str = "No Dataset Loaded"
    is_ingesting: bool = False
    status_message: str = ""
    upload_dialog_open: bool = False
    uploaded_file_name: str = ""

    # Card 1: Dynamic Production Datasets Auto-Scan State (Quét duy nhất data/production)
    production_datasets: List[Dict[str, Any]] = INITIAL_PRODUCTION_DATASETS
    selected_production_file: str = INITIAL_SELECTED_FILE

    # Alert notification banner state (Thanh Alert màu xanh lục đậm trên cùng)
    show_alert: bool = False
    alert_message: str = ""
    alert_type: str = "success"  # "success" | "error"
    alert_token: int = 0

    # Kết quả thẩm định
    current_pd: float = 0.0
    current_score_percent: float = 0.0
    current_tier: str = "None"
    current_decision: str = "None"
    top_risk_factors: List[Dict[str, Any]] = []
    top_positive_factors: List[Dict[str, Any]] = []
    selected_client_raw: Dict[str, Any] = {}
    current_client_shap: Dict[str, float] = {}

    # --- RISK MITIGATION & TERMS SIMULATOR STATE ---
    # Baseline values (Original client record)
    baseline_amt_credit: float = 0.0
    baseline_term_months: int = 12
    baseline_amt_annuity: float = 0.0
    baseline_amt_income_total: float = 0.0
    baseline_dti: float = 0.0
    baseline_pd: float = 0.0
    baseline_score_percent: float = 0.0
    baseline_tier: str = "None"
    baseline_decision: str = "None"
    baseline_offered_rate: float = 12.0
    sim_offered_rate: float = 12.0
    baseline_rate_display: str = "12.00%"
    baseline_decision_status: str = "APPROVED"
    baseline_decision_color: str = "#34D399"
    credit_decision_status: str = "APPROVED"
    credit_decision_color: str = "#34D399"
    credit_decision_text: str = "Approved under Risk Appetite"

    # Simulation active levers
    sim_amt_credit: float = 0.0
    sim_term_months: int = 12
    sim_amt_annuity: float = 0.0
    sim_amt_income_total: float = 0.0
    sim_dti: float = 0.0
    interest_rate_factor: float = 0.08
    is_sim_calculating: bool = False
    sim_rate_display: str = "12.00%"
    sim_rate_delta_text: str = ""
    sim_rate_delta_color: str = "#94A3B8"
    sim_decision_status: str = "APPROVED"
    sim_decision_color: str = "#34D399"
    sim_credit_decision: str = "APPROVED"
    sim_credit_decision_color: str = "#34D399"

    # Two-way bound string variables for text input fields
    sim_amt_credit_str: str = "0"
    sim_term_months_str: str = "12"
    sim_amt_annuity_str: str = "0"
    sim_amt_income_str: str = "0"

    # Simulation real-time predicted outcomes
    sim_pd: float = 0.0
    sim_score_percent: float = 0.0
    sim_tier: str = "None"
    sim_decision: str = "None"
    sim_delta_pts: float = 0.0
    sim_delta_text: str = "0.00 pts"
    sim_delta_color: str = "#94A3B8"
    is_optimizing: bool = False
    is_loading_alternatives: bool = False
    alternatives_loaded: bool = False
    optimization_options: List[Dict[str, Any]] = []
    recommended_option: Dict[str, Any] = DEFAULT_RECOMMENDED_OPTION
    alternative_options: List[Dict[str, Any]] = []
    show_optimization_results: bool = False
    show_alternative_options: bool = False

    @rx.event
    def toggle_alternative_options(self):
        """Lazy load hoặc đóng/mở danh sách phương án kịch bản thay thế."""
        if not self.show_alternative_options:
            if not self.alternatives_loaded:
                self.is_loading_alternatives = True
                self.show_alternative_options = True
                yield
                self._compute_alternative_options()
                self.alternatives_loaded = True
                self.is_loading_alternatives = False
            else:
                self.show_alternative_options = True
        else:
            self.show_alternative_options = False

    load_or_toggle_alternatives = toggle_alternative_options

    def load_demo_clients(self):
        """Khởi động mặc định nạp demo_samples.parquet vào State."""
        if not self.available_client_ids:
            df, source_label = load_dataset_from_source("demo_samples")
            self.selected_dataset_source = "demo_samples"
            self.active_source_label = source_label
            self.available_client_ids = get_active_client_ids()
            self.total_clients_count = len(self.available_client_ids)
            self.client_list = get_client_table_summary(100)

        if self.available_client_ids and (not self.selected_client_id or self.selected_client_id == "None"):
            first_id = self.available_client_ids[0]
            self.select_and_evaluate_client(first_id)

    # --- DATA INGESTION HANDLERS ---

    # Quản lý hiển thị Client Registry (Trang 1)
    is_dataset_loaded: bool = False
    registry_display_limit: int = 35
    registry_search_query: str = ""

    def set_registry_search_query(self, query: str):
        """Lọc tìm kiếm Client ID theo thời gian thực (Real-time Filter)."""
        self.registry_search_query = query.strip()
        q = self.registry_search_query
        if q and self.is_dataset_loaded:
            # Nếu chưa có trong 100 bản ghi nạp sẵn, tìm sâu trong active dataset
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

    def inspect_client(self, client_id: str):
        """Lưu selected_client_id vào State, kích hoạt đánh giá và chuyển sang Trang 2."""
        self.select_and_evaluate_client(str(client_id))
        return rx.redirect("/inspection")

    def clear_registry_search(self):
        self.registry_search_query = ""

    def open_upload_dialog(self):
        self.upload_dialog_open = True

    def close_upload_dialog(self):
        self.upload_dialog_open = False

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
            print(f"[UnderwritingState.scan_production_dir] Fallback exception: {e}")

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

    @rx.event
    def reset_alert(self):
        """Ẩn thanh Alert cũ khi người dùng bắt đầu thao tác chọn hoặc thả file mới."""
        self.show_alert = False
        self.alert_token += 1

    @rx.event
    def dismiss_alert(self):
        """Đóng thanh thông báo alert trên cùng bằng nút [x]."""
        self.show_alert = False
        self.alert_token += 1

    @rx.event(background=True)
    async def auto_dismiss_alert(self, token: int):
        """Tự động tắt thanh thông báo Alert sau 5 giây (chạy nền không block UI)."""
        import asyncio
        await asyncio.sleep(5)
        async with self:
            if self.alert_token == token:
                self.show_alert = False

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
                yield self.select_and_evaluate_client(first_id)

            yield UnderwritingState.auto_dismiss_alert(current_token)
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
        """Xử lý nạp file CSV/Parquet tùy chỉnh do người dùng upload với kiểm tra size 500MB và format,
        chạy pipeline tiền xử lý, tự động lưu file đầu ra vào data/production không ghi đè,
        và re-scan cập nhật Thẻ 1.
        """
        if not files:
            return

        file = files[0]
        fname = file.filename.lower()

        # 1. Kiểm tra định dạng đuôi file (.csv hoặc .parquet)
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

            # 2. Rào chắn kích thước file tối đa 500MB (500 * 1024 * 1024 bytes)
            max_size_bytes = 500 * 1024 * 1024
            if len(file_bytes) > max_size_bytes:
                self.alert_message = "File size exceeds 500MB limit or unsupported format."
                self.alert_type = "error"
                self.show_alert = True
                self.status_message = self.alert_message
                self.is_ingesting = False
                return

            # 3. Chạy pipeline tiền xử lý và feature alignment
            df, source_label = load_dataset_from_upload(file_bytes, file.filename)
            if df is None or df.empty:
                self.alert_message = f"File {file.filename} contained no valid data."
                self.alert_type = "error"
                self.show_alert = True
                self.status_message = self.alert_message
                self.is_ingesting = False
                return

            # 4. Tự động lưu kết quả đã xử lý vào thư mục data/production (định dạng .parquet)
            prod_dir = get_production_dir()
            os.makedirs(prod_dir, exist_ok=True)

            export_ext = ".parquet" if (fname.endswith(".csv") or fname.endswith(".parquet") or fname.endswith(".pq")) else Path(file.filename).suffix
            base_export_name = Path(file.filename).stem + export_ext

            # Kiểm tra chống trùng tên file (Auto-increment suffix: _1, _2...)
            unique_file_path = get_unique_filepath(prod_dir, base_export_name)
            saved_filename = unique_file_path.name

            # Xuất trực tiếp file đầu ra vào data/production/
            if export_ext == ".parquet":
                df.to_parquet(unique_file_path, index=False)
            else:
                df.to_csv(unique_file_path, index=False)

            # 5. Cập nhật State nạp dữ liệu
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

            # 6. Tự động re-scan Thẻ 1 và chọn file vừa lưu
            self.scan_production_dir()
            self.selected_production_file = saved_filename

            # 7. Bắn Toast Notification / Alert màu xanh và hẹn giờ tự tắt sau 5s
            self.alert_token += 1
            current_token = self.alert_token
            self.alert_message = f"✓ Dataset ingested & saved to data/production as {saved_filename}"
            self.alert_type = "success"
            self.show_alert = True
            self.status_message = self.alert_message

            if self.available_client_ids:
                first_id = self.available_client_ids[0]
                yield
                yield self.select_and_evaluate_client(first_id)

            yield UnderwritingState.auto_dismiss_alert(current_token)
        except Exception as e:
            self.alert_message = f"Error processing uploaded file: {str(e)}"
            self.alert_type = "error"
            self.show_alert = True
            self.status_message = self.alert_message
        finally:
            self.is_ingesting = False

    def select_previous_client(self):
        """Chọn hồ sơ phía trước trong danh sách."""
        if not self.available_client_ids or not self.selected_client_id:
            return
        try:
            idx = self.available_client_ids.index(str(self.selected_client_id))
            if idx > 0:
                prev_id = self.available_client_ids[idx - 1]
                return self.select_and_evaluate_client(prev_id)
        except ValueError:
            pass

    def select_next_client(self):
        """Chọn hồ sơ kế tiếp trong danh sách."""
        if not self.available_client_ids or not self.selected_client_id:
            return
        try:
            idx = self.available_client_ids.index(str(self.selected_client_id))
            if idx < len(self.available_client_ids) - 1:
                next_id = self.available_client_ids[idx + 1]
                return self.select_and_evaluate_client(next_id)
        except ValueError:
            pass

    # --- COMPUTED VARS ---

    @rx.var
    def client_id_options(self) -> List[str]:
        """Danh sách ID hiển thị cho Dropdown chọn hồ sơ (tối đa 500 ID đầu để UI nhẹ mượt)."""
        return self.available_client_ids[:500]

    @rx.var
    def is_first_client(self) -> bool:
        if not self.available_client_ids or not self.selected_client_id:
            return True
        return self.available_client_ids[0] == str(self.selected_client_id)

    @rx.var
    def is_last_client(self) -> bool:
        if not self.available_client_ids or not self.selected_client_id:
            return True
        return self.available_client_ids[-1] == str(self.selected_client_id)

    @rx.var
    def current_client_index_display(self) -> str:
        if not self.available_client_ids or not self.selected_client_id:
            return "1"
        try:
            idx = self.available_client_ids.index(str(self.selected_client_id))
            return f"{idx + 1}"
        except ValueError:
            return "1"

    @rx.var
    def client_age(self) -> str:
        return str(self.selected_client_raw.get("AGE", "None"))

    @rx.var
    def client_experience(self) -> str:
        return str(self.selected_client_raw.get("EXPERIENCE", "None"))

    @rx.var
    def client_credit(self) -> str:
        return str(self.selected_client_raw.get("Credit", "None"))

    @rx.var
    def client_annuity(self) -> str:
        return str(self.selected_client_raw.get("Annuity", "None"))

    @rx.var
    def client_term(self) -> str:
        return str(self.selected_client_raw.get("TERM", "None"))

    @rx.var
    def client_dti(self) -> str:
        return str(self.selected_client_raw.get("PAYMENT_TO_INCOME", "None"))

    @rx.var
    def pd_display(self) -> str:
        if not self.selected_client_id or self.current_decision == "None":
            return "0.00%"
        pd_val = float(self.current_pd)
        pd_pct = pd_val * 100 if pd_val <= 1.0 else pd_val
        return f"{pd_pct:.2f}%"

    @rx.var
    def baseline_pd_display(self) -> str:
        return f"{self.baseline_score_percent:.2f}%"

    @rx.var
    def decision_color(self) -> str:
        dec = self.current_decision.upper()
        if "APPROVE" in dec:
            return "#10B981"  # Xanh lá
        elif "WAIT" in dec or "REVIEW" in dec or "COMMITTEE" in dec:
            return "#F59E0B"  # Vàng hổ phách
        elif "DECLINE" in dec or "REJECT" in dec:
            return "#EF4444"  # Đỏ
        return "#94A3B8"

    @rx.var
    def decision_bg_color(self) -> str:
        dec = self.current_decision.upper()
        if "APPROVE" in dec:
            return "rgba(16, 185, 129, 0.12)"
        elif "WAIT" in dec or "REVIEW" in dec or "COMMITTEE" in dec:
            return "rgba(245, 158, 11, 0.12)"
        elif "DECLINE" in dec or "REJECT" in dec:
            return "rgba(239, 68, 68, 0.12)"
        return "rgba(15, 23, 42, 0.6)"

    # --- LOGIC THẨM ĐỊNH VÀ TÍNH TOÁN ---

    def select_and_evaluate_client(self, client_id: str):
        if not client_id:
            return
        self.selected_client_id = str(client_id)
        self.is_loading = True

        client_series = get_client_row_data(client_id)
        if client_series is None:
            self.is_loading = False
            return

        # 1. Trích xuất AMT_CREDIT
        credit_val = client_series.get("AMT_CREDIT", None)
        try:
            credit_num = float(credit_val) if pd.notna(credit_val) else 0.0
            credit_str = f"${credit_num:,.0f}" if credit_num > 0 else "None"
        except (ValueError, TypeError):
            credit_num = 0.0
            credit_str = "None"

        # 2. Trích xuất AMT_ANNUITY
        annuity_val = client_series.get("AMT_ANNUITY", None)
        try:
            annuity_num = float(annuity_val) if pd.notna(annuity_val) else 0.0
            annuity_str = f"${annuity_num:,.0f} / mo" if annuity_num > 0 else "None"
        except (ValueError, TypeError):
            annuity_num = 0.0
            annuity_str = "None"

        # 3. Trích xuất AMT_INCOME_TOTAL
        income_val = client_series.get("AMT_INCOME_TOTAL", None)
        try:
            income_num = float(income_val) if pd.notna(income_val) else 0.0
            income_str = f"${income_num:,.0f}" if income_num > 0 else "None"
        except (ValueError, TypeError):
            income_num = 0.0
            income_str = "None"

        # 4. Tính toán TERM (Credit / Annuity)
        if credit_num > 0 and annuity_num > 0:
            term_months = round(credit_num / annuity_num)
            term_str = f"{term_months} months"
        else:
            term_str = "None"

        # 5. Tính toán PAYMENT-TO-INCOME (DTI)
        if income_num > 0 and annuity_num > 0:
            dti_ratio = (annuity_num / income_num) * 100
            dti_str = f"{dti_ratio:.1f}%"
        else:
            dti_str = "None"

        # 6. Gán Dictionary Thông Tin Khách Hàng
        raw_age = client_series.get("AGE")
        if pd.isna(raw_age) or raw_age is None:
            raw_age = client_series.get("DAYS_BIRTH")
        if pd.isna(raw_age) or raw_age is None:
            raw_age = client_series.get("AGE_YEARS")

        raw_exp = client_series.get("EXPERIENCE")
        if pd.isna(raw_exp) or raw_exp is None:
            raw_exp = client_series.get("DAYS_EMPLOYED")
        if pd.isna(raw_exp) or raw_exp is None:
            raw_exp = client_series.get("EMPLOYED_YEARS")

        self.selected_client_raw = {
            "ID": str(client_id),
            "NAME": "Client Name",
            "AGE": format_client_age(raw_age),
            "EXPERIENCE": format_client_experience(raw_exp),
            "Credit": credit_str,
            "Annuity": annuity_str,
            "TERM": term_str,
            "PAYMENT_TO_INCOME": dti_str,
            "Income": income_str,
        }

        # 7. Chạy mô hình backend
        engine = get_engine()
        result = engine.predict_single(client_series)

        self.current_pd = result.get("probability_of_default", 0.0)
        self.current_score_percent = result.get("score_percent", 0.0)
        self.current_tier = result.get("tier", "None")
        self.current_decision = result.get("decision", "None")

        raw_risks = [dict(item) for item in result.get("top_risk_factors", [])]
        raw_positives = [dict(item) for item in result.get("top_positive_factors", [])]

        shap_lookup: Dict[str, float] = {}
        if "all_shap_values" in result and isinstance(result["all_shap_values"], dict):
            shap_lookup = {k: round(float(v), 4) for k, v in result["all_shap_values"].items()}
        else:
            for item in raw_risks:
                feat = item.get("feature")
                if feat:
                    shap_lookup[feat] = round(float(item.get("shap_value", 0.0)), 4)
            for item in raw_positives:
                feat = item.get("feature")
                if feat:
                    shap_lookup[feat] = round(float(item.get("shap_value", 0.0)), 4)

        if raw_risks:
            max_risk = max([abs(float(f.get("shap_value", 0.0))) for f in raw_risks]) or 1.0
            for f in raw_risks:
                pct = round((abs(float(f.get("shap_value", 0.0))) / max_risk) * 100, 1)
                f["bar_width"] = f"{max(pct, 6.0)}%"

        if raw_positives:
            max_trust = max([abs(float(f.get("shap_value", 0.0))) for f in raw_positives]) or 1.0
            for f in raw_positives:
                pct = round((abs(float(f.get("shap_value", 0.0))) / max_trust) * 100, 1)
                f["bar_width"] = f"{max(pct, 6.0)}%"

        self.top_risk_factors = raw_risks
        self.top_positive_factors = raw_positives

        # 8. Cập nhật Baseline và khởi tạo Terms Simulator
        self.baseline_amt_credit = credit_num
        self.baseline_amt_annuity = annuity_num
        self.baseline_amt_income_total = income_num
        self.baseline_term_months = term_months if (credit_num > 0 and annuity_num > 0) else 12
        self.baseline_dti = dti_ratio if (income_num > 0 and annuity_num > 0) else 0.0
        self.baseline_pd = self.current_pd
        self.baseline_score_percent = self.current_score_percent
        self.baseline_tier = self.current_tier
        self.baseline_decision = self.current_decision

        pd_dec = float(self.baseline_score_percent) / 100.0
        client_term = int(getattr(self, "baseline_term_months", 24))

        # 1. Tính toán lãi suất RBP
        p_res = pricing_engine.compute_baseline_pricing(pd_dec, client_term)
        self.baseline_offered_rate = p_res["applied_rate_percent"]
        self.sim_offered_rate = self.baseline_offered_rate
        self.baseline_rate_display = p_res["applied_rate_display"]
        self.sim_rate_display = self.baseline_rate_display
        self.sim_rate_delta_text = ""
        self.sim_rate_delta_color = "#94A3B8"

        # 2. Đánh giá quyết định tín dụng theo Cut-off & DTI cho Baseline qua Pricing Engine tập trung
        eval_res = pricing_engine.evaluate_credit_decision(
            pd_decimal=pd_dec,
            dti_percent=float(self.baseline_dti),
        )
        self.baseline_decision_status = eval_res["decision"]
        self.baseline_decision_color = eval_res["color"]
        self.credit_decision_text = eval_res["status_text"]

        self.credit_decision_status = self.baseline_decision_status
        self.credit_decision_color = self.baseline_decision_color

        self.sim_decision_status = self.baseline_decision_status
        self.sim_decision_color = self.baseline_decision_color
        self.sim_credit_decision = self.sim_decision_status
        self.sim_credit_decision_color = self.sim_decision_color
        self.is_sim_calculating = False

        if self.baseline_amt_credit > 0 and self.baseline_term_months > 0 and self.baseline_amt_annuity > 0:
            implied_factor = ((self.baseline_amt_annuity * self.baseline_term_months) / self.baseline_amt_credit) - 1.0
            if 0.0 <= implied_factor <= 0.35:
                self.interest_rate_factor = round(implied_factor, 3)
            else:
                self.interest_rate_factor = 0.08
        else:
            self.interest_rate_factor = 0.08

        # Tiền xử lý và lưu cache 891 features cho client hiện tại
        try:
            engine.cache_client_features(client_series, str(client_id))
        except Exception as e:
            print(f"[cache_client_features] Warning: {e}")

        self.reset_simulation_to_baseline()
        self.is_loading = False

        return FeatureSearchState.update_client_shap(shap_lookup)

    # ==============================================================================
    # RISK MITIGATION & TERMS SIMULATOR LOGIC & BOUNDS CLAMPING
    # ==============================================================================

    @rx.var
    def sim_credit_slider_min(self) -> float:
        base = self.baseline_amt_credit if self.baseline_amt_credit > 0 else (self.sim_amt_credit if self.sim_amt_credit > 0 else 100000.0)
        return float(round(base * 0.5, -2))

    @rx.var
    def sim_credit_slider_max(self) -> float:
        base = self.baseline_amt_credit if self.baseline_amt_credit > 0 else (self.sim_amt_credit if self.sim_amt_credit > 0 else 100000.0)
        return float(max(round(base * 1.5, -2), round(base * 0.5, -2) + 1000.0))

    @rx.var
    def sim_income_slider_min(self) -> float:
        base = self.baseline_amt_income_total if self.baseline_amt_income_total > 0 else (self.sim_amt_income_total if self.sim_amt_income_total > 0 else 50000.0)
        return float(round(base * 0.7, -2))

    @rx.var
    def sim_income_slider_max(self) -> float:
        base = self.baseline_amt_income_total if self.baseline_amt_income_total > 0 else (self.sim_amt_income_total if self.sim_amt_income_total > 0 else 50000.0)
        return float(max(round(base * 2.0, -2), round(base * 0.7, -2) + 1000.0))

    @rx.var
    def sim_annuity_slider_min(self) -> float:
        base_credit = self.baseline_amt_credit if self.baseline_amt_credit > 0 else (self.sim_amt_credit if self.sim_amt_credit > 0 else 100000.0)
        credit_min = base_credit * 0.5
        min_annuity = (credit_min / 60.0) * (1.0 + self.interest_rate_factor)
        return float(max(round(min_annuity, -2), 500.0))

    @rx.var
    def sim_annuity_slider_max(self) -> float:
        # Giới hạn max ở mức DTI <= 70%
        income = self.sim_amt_income_total if self.sim_amt_income_total > 0 else (self.baseline_amt_income_total if self.baseline_amt_income_total > 0 else 50000.0)
        max_dti = income * 0.70
        min_annuity = self.sim_annuity_slider_min
        return float(max(round(max_dti, -2), min_annuity + 1000.0))

    @rx.var
    def sim_amt_credit_slider(self) -> List[float]:
        # Neo ở 0% nếu < Min, neo ở 100% nếu > Max
        val = float(self.sim_amt_credit)
        val = min(max(val, self.sim_credit_slider_min), self.sim_credit_slider_max)
        return [val]

    @rx.var
    def sim_term_months_slider(self) -> List[float]:
        # Neo trong khoảng cố định [3, 60]
        val = float(self.sim_term_months)
        val = min(max(val, 3.0), 60.0)
        return [val]

    @rx.var
    def sim_amt_annuity_slider(self) -> List[float]:
        # Neo ở 0% nếu < Min, neo ở 100% nếu > Max (DTI <= 70%)
        val = float(self.sim_amt_annuity)
        val = min(max(val, self.sim_annuity_slider_min), self.sim_annuity_slider_max)
        return [val]

    @rx.var
    def sim_amt_income_slider(self) -> List[float]:
        # Neo ở 0% nếu < Min, neo ở 100% nếu > Max
        val = float(self.sim_amt_income_total)
        val = min(max(val, self.sim_income_slider_min), self.sim_income_slider_max)
        return [val]

    @rx.var
    def sim_credit_min_display(self) -> str:
        return f"${self.sim_credit_slider_min:,.0f} (-50%)"

    @rx.var
    def sim_credit_max_display(self) -> str:
        return f"${self.sim_credit_slider_max:,.0f} (+50%)"

    @rx.var
    def sim_income_min_display(self) -> str:
        return f"${self.sim_income_slider_min:,.0f}"

    @rx.var
    def sim_income_max_display(self) -> str:
        return f"${self.sim_income_slider_max:,.0f}"

    @rx.var
    def sim_annuity_min_display(self) -> str:
        return f"${self.sim_annuity_slider_min:,.0f}"

    @rx.var
    def sim_annuity_max_display(self) -> str:
        return f"${self.sim_annuity_slider_max:,.0f}"

    @rx.var
    def sim_amt_credit_display(self) -> str:
        return f"${self.sim_amt_credit:,.0f}"

    @rx.var
    def sim_term_months_display(self) -> str:
        return f"{self.sim_term_months} Months"

    @rx.var
    def sim_amt_annuity_display(self) -> str:
        return f"${self.sim_amt_annuity:,.0f} / mo"

    @rx.var
    def sim_amt_income_display(self) -> str:
        return f"${self.sim_amt_income_total:,.0f}"

    @rx.var
    def sim_dti_display(self) -> str:
        return f"{self.sim_dti:.1f}%"

    @rx.var
    def sim_status_color(self) -> str:
        if self.sim_decision == "APPROVE":
            return "#10B981"
        elif self.sim_decision == "DECLINE":
            return "#EF4444"
        return "#F59E0B"

    @rx.var
    def sim_dti_color(self) -> str:
        if self.sim_dti <= 35.0:
            return "#10B981"
        elif self.sim_dti <= retail_pricing_config.max_dti_limit:
            return "#F59E0B"
        return "#EF4444"

    @rx.var
    def is_sim_dti_exceeded(self) -> bool:
        """Kiểm tra tỷ lệ DTI mô phỏng có vượt trần cho phép (max_dti_limit) hay không."""
        return float(self.sim_dti) > retail_pricing_config.max_dti_limit

    @rx.var
    def is_scenario_viable(self) -> bool:
        """Kiểm tra phương án mô phỏng có khả thi hay không (DTI <= max_dti_limit và PD không tăng quá 2.0 pts so với baseline)."""
        try:
            dti_ok = float(self.sim_dti) <= retail_pricing_config.max_dti_limit
            pd_ok = float(self.sim_score_percent) <= (float(self.baseline_score_percent) + 2.0)
            return dti_ok and pd_ok
        except (ValueError, TypeError):
            return True

    # --- METRICS & DELTA COMPUTED PROPERTIES ---

    @rx.var
    def is_simulated_changed(self) -> bool:
        """Kiểm tra xem người dùng đã điều chỉnh bất kỳ tham số nào khác với Baseline hay chưa."""
        return (
            abs(self.sim_amt_credit - self.baseline_amt_credit) > 1.0
            or self.sim_term_months != self.baseline_term_months
            or abs(self.sim_amt_annuity - self.baseline_amt_annuity) > 1.0
            or abs(self.sim_amt_income_total - self.baseline_amt_income_total) > 1.0
            or abs(self.sim_score_percent - self.baseline_score_percent) > 0.001
        )

    @rx.var
    def pd_display_value(self) -> str:
        return f"{self.sim_score_percent:.2f}%"

    @rx.var
    def pd_delta_badge_text(self) -> str:
        diff = round(self.sim_score_percent - self.baseline_score_percent, 2)
        if diff > 0.0:
            return f"(+{diff:.2f}% pts)"
        elif diff < 0.0:
            return f"(-{abs(diff):.2f}% pts)"
        return ""

    @rx.var
    def pd_delta_color(self) -> str:
        diff = self.sim_score_percent - self.baseline_score_percent
        # Xanh lá nếu rủi ro giảm (delta < 0), đỏ nếu rủi ro tăng (delta > 0)
        return "#10B981" if diff < 0.0 else "#EF4444"

    @rx.var
    def diff_credit_text(self) -> str:
        diff = round(self.sim_amt_credit - self.baseline_amt_credit)
        if diff > 0:
            return f"(+${diff:,.0f})"
        elif diff < 0:
            return f"(-${abs(diff):,.0f})"
        return ""

    @rx.var
    def diff_credit_color(self) -> str:
        diff = self.sim_amt_credit - self.baseline_amt_credit
        return "#10B981" if diff > 0 else "#EF4444"

    @rx.var
    def diff_term_text(self) -> str:
        diff = self.sim_term_months - self.baseline_term_months
        if diff > 0:
            return f"(+{diff}m)"
        elif diff < 0:
            return f"(-{abs(diff)}m)"
        return ""

    @rx.var
    def diff_term_color(self) -> str:
        diff = self.sim_term_months - self.baseline_term_months
        return "#10B981" if diff > 0 else "#EF4444"

    @rx.var
    def diff_annuity_text(self) -> str:
        diff = round(self.sim_amt_annuity - self.baseline_amt_annuity)
        if diff > 0:
            return f"(+${diff:,.0f})"
        elif diff < 0:
            return f"(-${abs(diff):,.0f})"
        return ""

    @rx.var
    def diff_annuity_color(self) -> str:
        diff = self.sim_amt_annuity - self.baseline_amt_annuity
        return "#10B981" if diff > 0 else "#EF4444"

    @rx.var
    def diff_income_text(self) -> str:
        diff = round(self.sim_amt_income_total - self.baseline_amt_income_total)
        if diff > 0:
            return f"(+${diff:,.0f})"
        elif diff < 0:
            return f"(-${abs(diff):,.0f})"
        return ""

    @rx.var
    def diff_income_color(self) -> str:
        diff = self.sim_amt_income_total - self.baseline_amt_income_total
        return "#10B981" if diff > 0 else "#EF4444"

    @rx.event
    def reset_simulation_to_baseline(self):
        """Khôi phục lại toàn bộ tham số Simulator về mức Baseline ban đầu của khách hàng (nhẹ, tức thì)."""
        self.sim_amt_credit = float(self.baseline_amt_credit)
        self.sim_term_months = int(self.baseline_term_months)
        self.sim_amt_annuity = float(self.baseline_amt_annuity)
        self.sim_amt_income_total = float(self.baseline_amt_income_total)
        self.sim_dti = float(self.baseline_dti)
        self.sim_pd = float(self.baseline_pd)
        self.sim_score_percent = float(self.baseline_score_percent)
        self.sim_tier = str(self.baseline_tier)
        self.sim_decision = str(self.baseline_decision)
        self.sim_offered_rate = float(self.baseline_offered_rate)
        self.sim_rate_display = str(self.baseline_rate_display)
        self.sim_rate_delta_text = ""
        self.sim_rate_delta_color = "#94A3B8"
        self.sim_decision_status = str(self.baseline_decision_status)
        self.sim_decision_color = str(self.baseline_decision_color)
        self.sim_credit_decision = self.sim_decision_status
        self.sim_credit_decision_color = self.sim_decision_color
        self.is_sim_calculating = False
        self.sim_delta_pts = 0.0
        self.sim_delta_text = "0.00 pts"
        self.sim_delta_color = "#94A3B8"
        self.is_optimizing = False
        self.is_loading_alternatives = False
        self.alternatives_loaded = False
        self.show_optimization_results = False
        self.optimization_options = []
        self.recommended_option = dict(DEFAULT_RECOMMENDED_OPTION)
        self.alternative_options = []
        self.show_alternative_options = False

        self.sim_amt_credit_str = f"{int(self.sim_amt_credit):,}" if self.sim_amt_credit > 0 else "0"
        self.sim_term_months_str = str(int(self.sim_term_months))
        self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}" if self.sim_amt_annuity > 0 else "0"
        self.sim_amt_income_str = f"{int(self.sim_amt_income_total):,}" if self.sim_amt_income_total > 0 else "0"

    def _sync_credit_or_term_drag(self):
        """Chỉ cập nhật UI cục bộ tức thì trong khi kéo slider để đạt 60fps mượt mà tuyệt đối."""
        term = max(self.sim_term_months, 1)
        self.sim_amt_annuity = round((self.sim_amt_credit / term) * (1.0 + self.interest_rate_factor), 1)
        income = max(self.sim_amt_income_total, 1.0)
        self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
        self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"
        self.sim_amt_credit_str = f"{int(self.sim_amt_credit):,}"
        self.sim_term_months_str = str(int(self.sim_term_months))

    def _sync_credit_or_term_changed(self):
        """Tự động tính lại AMT_ANNUITY và DTI khi AMT_CREDIT hoặc TERM_MONTHS thay đổi kèm ML inference."""
        self._sync_credit_or_term_drag()
        self.recalculate_simulation_pd()

    def _sync_annuity_changed(self):
        """Tự động suy ngược lại TERM_MONTHS và snapped về nấc gần nhất khi AMT_ANNUITY thay đổi."""
        annuity = max(self.sim_amt_annuity, 1.0)
        raw_term = (self.sim_amt_credit * (1.0 + self.interest_rate_factor)) / annuity
        snapped_steps = [3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
        self.sim_term_months = min(snapped_steps, key=lambda s: abs(s - raw_term))
        income = max(self.sim_amt_income_total, 1.0)
        self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
        self.sim_term_months_str = str(int(self.sim_term_months))
        self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"
        self.recalculate_simulation_pd()

    def _sync_income_changed(self):
        """Cập nhật DTI khi thu nhập thay đổi."""
        income = max(self.sim_amt_income_total, 1.0)
        self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
        self.sim_amt_income_str = f"{int(self.sim_amt_income_total):,}"
        self.recalculate_simulation_pd()

    # --- SLIDER HANDLERS (SMOOTH DRAG ON THE FLY + COMMIT ON RELEASE) ---

    @rx.event
    def set_sim_credit_from_slider(self, val: List[float]):
        """Cập nhật UI cục bộ bám sát con trỏ chuột khi đang kéo thanh AMT_CREDIT trong khoảng [Min, Max]."""
        if val:
            clamped = min(max(float(val[0]), self.sim_credit_slider_min), self.sim_credit_slider_max)
            if clamped == self.sim_amt_credit:
                return
            self.sim_amt_credit = clamped
            self.is_sim_calculating = True
            self._sync_credit_or_term_drag()

    @rx.event
    def set_sim_term_from_slider(self, val: List[float]):
        """Cập nhật UI cục bộ mượt mà bám sát con trỏ chuột khi đang kéo thanh TERM_MONTHS trong khoảng [3, 60]."""
        if val:
            raw_val = min(max(float(val[0]), 3.0), 60.0)
            snapped_steps = [3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
            new_term = min(snapped_steps, key=lambda s: abs(s - raw_val))
            if new_term == self.sim_term_months:
                return
            self.sim_term_months = new_term
            self.is_sim_calculating = True
            self._sync_credit_or_term_drag()

    @rx.event
    def set_sim_annuity_from_slider(self, val: List[float]):
        """Cập nhật UI cục bộ mượt mà khi đang kéo thanh AMT_ANNUITY trong khoảng [Min, Max] (DTI <= 70%)."""
        if val:
            clamped = min(max(float(val[0]), self.sim_annuity_slider_min), self.sim_annuity_slider_max)
            if clamped == self.sim_amt_annuity:
                return
            self.sim_amt_annuity = clamped
            self.is_sim_calculating = True
            raw_term = (self.sim_amt_credit * (1.0 + self.interest_rate_factor)) / max(self.sim_amt_annuity, 1.0)
            snapped_steps = [3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
            self.sim_term_months = min(snapped_steps, key=lambda s: abs(s - raw_term))
            income = max(self.sim_amt_income_total, 1.0)
            self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
            self.sim_term_months_str = str(int(self.sim_term_months))
            self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"

    @rx.event
    def set_sim_income_from_slider(self, val: List[float]):
        """Cập nhật UI cục bộ mượt mà khi đang kéo thanh AMT_INCOME_TOTAL trong khoảng [Min, Max]."""
        if val:
            clamped = min(max(float(val[0]), self.sim_income_slider_min), self.sim_income_slider_max)
            if clamped == self.sim_amt_income_total:
                return
            self.sim_amt_income_total = clamped
            self.is_sim_calculating = True
            income = max(self.sim_amt_income_total, 1.0)
            self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
            self.sim_amt_income_str = f"{int(self.sim_amt_income_total):,}"

    @rx.event
    def commit_sim_slider(self, val: List[float]):
        """Kích hoạt Machine Learning re-inference khi người dùng nhả chuột (on_value_commit)."""
        self.recalculate_simulation_pd()

    @rx.event
    def set_sim_term_preset(self, months: int):
        """Click nhanh phím Quick Preset Pill (3m, 6m, 12m, 24m, 36m, 48m, 60m)."""
        self.sim_term_months = int(months)
        self._sync_credit_or_term_changed()

    # --- TEXT INPUT HANDLERS (TWO-WAY BINDING) ---

    @rx.event
    def set_sim_credit_from_input(self, val: str):
        self.sim_amt_credit_str = val
        clean = val.replace("$", "").replace(",", "").strip()
        try:
            num = float(clean)
            if num > 0:
                self.sim_amt_credit = num
                term = max(self.sim_term_months, 1)
                self.sim_amt_annuity = round((self.sim_amt_credit / term) * (1.0 + self.interest_rate_factor), 1)
                self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"
                income = max(self.sim_amt_income_total, 1.0)
                self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
                self.recalculate_simulation_pd()
        except (ValueError, TypeError):
            pass

    @rx.event
    def set_sim_term_from_input(self, val: str):
        self.sim_term_months_str = val
        clean = val.replace("m", "").replace("mo", "").replace("months", "").strip()
        try:
            num = int(clean)
            if num > 0:
                self.sim_term_months = num
                term = max(self.sim_term_months, 1)
                self.sim_amt_annuity = round((self.sim_amt_credit / term) * (1.0 + self.interest_rate_factor), 1)
                self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"
                income = max(self.sim_amt_income_total, 1.0)
                self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
                self.recalculate_simulation_pd()
        except (ValueError, TypeError):
            pass

    @rx.event
    def set_sim_annuity_from_input(self, val: str):
        self.sim_amt_annuity_str = val
        clean = val.replace("$", "").replace(",", "").replace("/ mo", "").strip()
        try:
            num = float(clean)
            if num > 0:
                self.sim_amt_annuity = num
                raw_term = (self.sim_amt_credit * (1.0 + self.interest_rate_factor)) / self.sim_amt_annuity
                snapped_steps = [3, 6, 12, 18, 24, 30, 36, 42, 48, 54, 60]
                self.sim_term_months = min(snapped_steps, key=lambda s: abs(s - raw_term))
                self.sim_term_months_str = str(int(self.sim_term_months))
                income = max(self.sim_amt_income_total, 1.0)
                self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
                self.recalculate_simulation_pd()
        except (ValueError, TypeError):
            pass

    @rx.event
    def set_sim_income_from_input(self, val: str):
        self.sim_amt_income_str = val
        clean = val.replace("$", "").replace(",", "").strip()
        try:
            num = float(clean)
            if num > 0:
                self.sim_amt_income_total = num
                income = max(self.sim_amt_income_total, 1.0)
                self.sim_dti = round((self.sim_amt_annuity / income) * 100.0, 1)
                self.recalculate_simulation_pd()
        except (ValueError, TypeError):
            pass

    @rx.event
    def recalculate_simulation_pd(self):
        """Chạy suy luận lại xác suất vỡ nợ (PD), Rating Tier, Lãi suất RBP và Quyết định tín dụng theo thời gian thực (siêu tốc qua cache)."""
        if not self.selected_client_id:
            self.is_sim_calculating = False
            return

        try:
            engine = get_engine()
            # 1. Đảm bảo cache đặc trưng luôn sẵn sàng cho client hiện tại
            if (getattr(engine, "_cached_clean_df", None) is None or getattr(engine, "_cached_client_id", None) != str(self.selected_client_id)) and self.selected_client_id:
                client_series = get_client_row_data(self.selected_client_id)
                if client_series is not None:
                    engine.cache_client_features(client_series, str(self.selected_client_id))

            # 2. Lấy các tham số truyền vào predict_pd_from_cache an toàn
            credit = float(self.sim_amt_credit)
            annuity = float(self.sim_amt_annuity)
            income = float(self.sim_amt_income_total)
            if credit <= 0:
                credit = float(self.baseline_amt_credit) if float(self.baseline_amt_credit) > 0 else 100000.0
            if annuity <= 0:
                annuity = float(self.baseline_amt_annuity) if float(self.baseline_amt_annuity) > 0 else 5000.0
            if income <= 0:
                income = float(self.baseline_amt_income_total) if float(self.baseline_amt_income_total) > 0 else 50000.0

            # Dự đoán siêu tốc qua cached dataframe
            sim_pd, sim_tier, sim_decision = engine.predict_pd_from_cache(
                credit=credit,
                annuity=annuity,
                income=income,
            )

            # Fallback an toàn nếu model trả về None hoặc <= 0.0001: KHÔNG gán đè 0.0 mà fallback giữ nguyên baseline PD thập phân
            baseline_pd_dec = float(self.baseline_score_percent) / 100.0 if self.baseline_score_percent > 0 else (float(self.baseline_pd) if self.baseline_pd > 0 else 0.0377)
            import math
            if sim_pd is None or math.isnan(float(sim_pd)) or float(sim_pd) <= 0.0001:
                print(f"[recalculate_simulation_pd] Warning: sim_pd was {sim_pd}, falling back to baseline {baseline_pd_dec}")
                sim_pd = baseline_pd_dec
                sim_tier = self.baseline_tier if self.baseline_tier != "None" else "Tier A"
                sim_decision = self.baseline_decision if self.baseline_decision != "None" else "APPROVE"

            self.sim_pd = float(sim_pd)
            self.sim_score_percent = round(self.sim_pd * 100.0, 2)
            self.sim_tier = sim_tier
            self.sim_decision = sim_decision

            delta = round(self.sim_score_percent - self.baseline_score_percent, 2)
            self.sim_delta_pts = delta

            if delta > 0.0:
                self.sim_delta_text = f"▲ +{abs(delta):.2f} pts"
                self.sim_delta_color = "#EF4444"
            elif delta < 0.0:
                self.sim_delta_text = f"▼ -{abs(delta):.2f} pts"
                self.sim_delta_color = "#10B981"
            else:
                self.sim_delta_text = "0.00 pts"
                self.sim_delta_color = "#94A3B8"

            # 3. Chuỗi tính toán RBP và Quyết định cho What-If
            pricing_res = pricing_engine.compute_baseline_pricing(
                self.sim_pd,
                int(self.sim_term_months),
            )
            self.sim_offered_rate = pricing_res["applied_rate_percent"]
            self.sim_rate_display = pricing_res["applied_rate_display"]

            # Tính toán Delta lãi suất so với baseline_offered_rate
            diff_rate = round(self.sim_offered_rate - self.baseline_offered_rate, 2)
            if abs(diff_rate) < 0.01:
                self.sim_rate_delta_text = ""
            else:
                sign = "+" if diff_rate > 0 else ""
                self.sim_rate_delta_text = f"({sign}{diff_rate:.2f}%)"
                self.sim_rate_delta_color = "#F87171" if diff_rate > 0 else "#34D399"

            # 4. Đánh giá trạng thái mô phỏng tập trung qua Pricing Engine
            eval_res = pricing_engine.evaluate_credit_decision(
                pd_decimal=float(self.sim_pd),
                dti_percent=float(self.sim_dti),
            )
            self.sim_decision_status = eval_res["decision"]
            self.sim_decision_color = eval_res["color"]
            self.sim_credit_decision = self.sim_decision_status
            self.sim_credit_decision_color = self.sim_decision_color

            print(f"[recalculate_simulation_pd] Client ID={self.selected_client_id} | Output sim_pd={self.sim_pd:.4f} ({self.sim_score_percent}%) | Baseline PD={self.baseline_pd:.4f} ({self.baseline_score_percent}%) | Delta={delta:+.2f} pts | Decision={self.sim_decision_status}")

        except Exception as e:
            print(f"[recalculate_simulation_pd] Error: {e}")
            baseline_pd_dec = float(self.baseline_score_percent) / 100.0 if self.baseline_score_percent > 0 else (float(self.baseline_pd) if self.baseline_pd > 0 else 0.0377)
            self.sim_pd = float(baseline_pd_dec)
            self.sim_score_percent = round(self.sim_pd * 100.0, 2)
            self.sim_delta_pts = 0.0
            self.sim_delta_text = "0.00 pts"
            self.sim_delta_color = "#94A3B8"
            eval_res = pricing_engine.evaluate_credit_decision(
                pd_decimal=float(self.sim_pd),
                dti_percent=float(self.sim_dti),
            )
            self.sim_decision_status = eval_res["decision"]
            self.sim_decision_color = eval_res["color"]
            self.sim_credit_decision = self.sim_decision_status
            self.sim_credit_decision_color = self.sim_decision_color
            try:
                pricing_res = pricing_engine.compute_baseline_pricing(
                    self.sim_pd,
                    int(self.sim_term_months),
                )
                self.sim_offered_rate = pricing_res["applied_rate_percent"]
                self.sim_rate_display = pricing_res["applied_rate_display"]
            except Exception:
                pass
        finally:
            self.is_sim_calculating = False

    def _find_candidate_pool(self) -> List[Dict[str, Any]]:
        """Khảo sát không gian kỳ hạn và hạn mức để tìm tập ứng viên hợp lệ."""
        engine = get_engine()
        base_credit = float(self.baseline_amt_credit) if self.baseline_amt_credit > 0 else float(self.sim_amt_credit)
        if base_credit <= 0:
            base_credit = 100000.0

        income = float(self.sim_amt_income_total) if self.sim_amt_income_total > 0 else 50000.0

        candidate_terms = [12, 18, 24, 30, 36, 42, 48, 60]
        credit_factors = [1.0, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60, 0.55, 0.50]

        approved_candidates = []
        all_valid_candidates = []

        for cand_term in candidate_terms:
            for factor in credit_factors:
                cand_credit = round(base_credit * factor, -2)
                cand_annuity = round((cand_credit / cand_term) * (1.0 + self.interest_rate_factor), 1)
                cand_dti = round((cand_annuity / max(income, 1.0)) * 100.0, 1)

                # Ràng buộc điều kiện khả thi lành mạnh: DTI <= target_dti_healthy (40.0%)
                if cand_dti > retail_pricing_config.target_dti_healthy:
                    continue

                # Dự đoán siêu tốc qua cache model ensemble
                cand_pd, cand_tier, _ = engine.predict_pd_from_cache(
                    credit=cand_credit,
                    annuity=cand_annuity,
                    income=income,
                )
                if cand_pd is None or cand_pd <= 0:
                    continue

                # Đánh giá thẩm định thống nhất qua evaluate_credit_decision
                eval_cand = pricing_engine.evaluate_credit_decision(
                    pd_decimal=float(cand_pd),
                    dti_percent=float(cand_dti),
                )

                # Tính toán định giá RBP trực tiếp cho từng phương án ứng viên
                pricing_cand = pricing_engine.compute_baseline_pricing(
                    pd_decimal=float(cand_pd),
                    term_months=int(cand_term),
                )

                candidate_info = {
                    "credit": float(cand_credit),
                    "term": int(cand_term),
                    "annuity": float(cand_annuity),
                    "dti": float(cand_dti),
                    "pd": float(cand_pd),
                    "tier": str(cand_tier),
                    "decision": eval_cand["decision"],
                    "is_approved": eval_cand["is_approved"],
                    "reason_code": eval_cand["reason_code"],
                    "offered_rate": pricing_cand["applied_rate_percent"],
                    "rate_display": pricing_cand["applied_rate_display"],
                    "factor": float(factor),
                    "credit_display": f"${int(cand_credit):,}",
                    "term_display": f"{int(cand_term)} tháng",
                    "annuity_display": f"${int(cand_annuity):,}/mo",
                    "dti_display": f"{cand_dti:.1f}%",
                    "pd_display": f"{cand_pd * 100:.2f}%",
                }
                all_valid_candidates.append(candidate_info)

                # Bộ lọc khả thi cứng (Hard Feasibility Filter): PD <= default_cutoff_pd & DTI <= max_dti_limit
                if eval_cand["is_approved"]:
                    approved_candidates.append(candidate_info)

        pool = approved_candidates if approved_candidates else sorted(all_valid_candidates, key=lambda x: x["pd"])
        return pool

    def _build_optimization_entry(self, c: Dict[str, Any], title: str, opt_type: str) -> Dict[str, Any]:
        """Tạo đối tượng hiển thị chuẩn cho kịch bản tối ưu hóa."""
        base_credit_val = float(self.baseline_amt_credit) if self.baseline_amt_credit > 0 else (float(self.sim_amt_credit) if self.sim_amt_credit > 0 else 100000.0)
        base_term_val = int(self.baseline_term_months) if self.baseline_term_months > 0 else (int(self.sim_term_months) if self.sim_term_months > 0 else 12)
        base_annuity_val = float(self.baseline_amt_annuity) if self.baseline_amt_annuity > 0 else (float(self.sim_amt_annuity) if self.sim_amt_annuity > 0 else 1000.0)
        base_dti_val = float(self.baseline_dti) if self.baseline_dti > 0 else (float(self.sim_dti) if self.sim_dti > 0 else 30.0)
        base_pd_percent_val = float(self.baseline_score_percent) if self.baseline_score_percent > 0 else (float(self.current_score_percent) if self.current_score_percent > 0 else 10.0)

        cand_credit = float(c["credit"])
        diff_credit = cand_credit - base_credit_val
        credit_display = f"${int(cand_credit):,}"
        if diff_credit > 0:
            credit_delta_text = f"(+${int(abs(diff_credit)):,})"
            credit_delta_color = "#38BDF8"
        elif diff_credit < 0:
            credit_delta_text = f"(-${int(abs(diff_credit)):,})"
            credit_delta_color = "#94A3B8"
        else:
            credit_delta_text = "(0)"
            credit_delta_color = "#64748B"

        cand_term = int(c["term"])
        diff_term = cand_term - base_term_val
        term_display = f"{cand_term} Months"
        if diff_term > 0:
            term_delta_text = f"(+{diff_term}m)"
            term_delta_color = "#94A3B8"
        elif diff_term < 0:
            term_delta_text = f"(-{abs(diff_term)}m)"
            term_delta_color = "#94A3B8"
        else:
            term_delta_text = "(0)"
            term_delta_color = "#64748B"

        cand_annuity = float(c["annuity"])
        diff_annuity = cand_annuity - base_annuity_val
        annuity_display = f"${int(cand_annuity):,} / mo"
        if diff_annuity < -1.0:
            annuity_val_color = "#F8FAFC"
            annuity_delta_text = f"(-${int(abs(diff_annuity)):,} / mo)"
            annuity_delta_color = "#34D399"
        elif diff_annuity > 1.0:
            annuity_val_color = "#F87171"
            annuity_delta_text = f"(+${int(abs(diff_annuity)):,})"
            annuity_delta_color = "#F87171"
        else:
            annuity_val_color = "#F8FAFC"
            annuity_delta_text = "(0)"
            annuity_delta_color = "#64748B"

        cand_dti = float(c["dti"])
        diff_dti = round(cand_dti - base_dti_val, 1)
        dti_display = f"{cand_dti:.1f}%"
        if diff_dti < -0.05:
            dti_val_color = "#34D399"
            dti_delta_text = f"({diff_dti:+.1f}%)"
            dti_delta_color = "#34D399"
        elif diff_dti > 0.05:
            dti_val_color = "#F87171"
            dti_delta_text = f"({diff_dti:+.1f}%)"
            dti_delta_color = "#F87171"
        else:
            dti_val_color = "#F8FAFC"
            dti_delta_text = "(0.0%)"
            dti_delta_color = "#64748B"

        cand_pd = float(c["pd"])
        cand_pd_percent = cand_pd * 100.0
        diff_pd = round(cand_pd_percent - base_pd_percent_val, 2)
        pd_display = f"{cand_pd_percent:.2f}%"
        if diff_pd < -0.005:
            pd_color = "#34D399"
            pd_delta_text = f"({diff_pd:+.2f}%)"
            pd_delta_color = "#34D399"
        elif diff_pd > 0.005:
            pd_color = "#F87171"
            pd_delta_text = f"({diff_pd:+.2f}%)"
            pd_delta_color = "#F87171"
        else:
            pd_color = "#F8FAFC"
            pd_delta_text = "(0.00%)"
            pd_delta_color = "#64748B"

        cand_rate = float(c.get("offered_rate", 12.0))
        diff_rate = round(cand_rate - self.baseline_offered_rate, 2)
        rate_display = c.get("rate_display", f"{cand_rate:.2f}%")
        if diff_rate > 0.01:
            rate_delta_text = f"(+{diff_rate:.2f}%)"
            rate_delta_color = "#F87171"
        elif diff_rate < -0.01:
            rate_delta_text = f"({diff_rate:.2f}%)"
            rate_delta_color = "#34D399"
        else:
            rate_delta_text = "(0.00%)"
            rate_delta_color = "#64748B"

        entry = dict(c)
        entry.update({
            "title": title,
            "opt_type": opt_type,
            "offered_rate": cand_rate,
            "rate_display": rate_display,
            "rate_delta_text": rate_delta_text,
            "rate_delta_color": rate_delta_color,
            "credit_display": credit_display,
            "credit_delta_text": credit_delta_text,
            "credit_delta_color": credit_delta_color,
            "term_display": term_display,
            "term_delta_text": term_delta_text,
            "term_delta_color": term_delta_color,
            "annuity_display": annuity_display,
            "annuity_val_color": annuity_val_color,
            "annuity_delta_text": annuity_delta_text,
            "annuity_delta_color": annuity_delta_color,
            "dti_display": dti_display,
            "dti_val_color": dti_val_color,
            "dti_delta_text": dti_delta_text,
            "dti_delta_color": dti_delta_color,
            "pd_display": pd_display,
            "pd_color": pd_color,
            "pd_delta_text": pd_delta_text,
            "pd_delta_color": pd_delta_color,
        })
        return entry

    def _compute_alternative_options(self):
        """Tính toán 2 phương án phụ (Shortest Tenure & Balanced Compromise) theo cơ chế Lazy Loading."""
        try:
            pool = self._find_candidate_pool()
            if not pool:
                self.alternative_options = []
                return

            c1 = self.recommended_option
            c1_term = int(c1.get("term", 0))
            c1_credit = float(c1.get("credit", 0.0))

            # 2. Shortest Tenure
            rem_for_term = [c for c in pool if (c["term"], c["credit"]) != (c1_term, c1_credit)]
            if not rem_for_term:
                rem_for_term = pool
            c2 = sorted(rem_for_term, key=lambda x: (x["term"], -x["credit"], x["pd"]))[0]
            c2_entry = self._build_optimization_entry(c2, "Shortest Tenure", "shortest_tenure")

            # 3. Balanced Compromise
            rem_for_bal = [
                c for c in pool
                if (c["term"], c["credit"]) not in [(c1_term, c1_credit), (c2["term"], c2["credit"])]
            ]
            if not rem_for_bal:
                rem_for_bal = rem_for_term
            if not rem_for_bal:
                rem_for_bal = pool

            def balanced_score(c):
                term_diff = abs(c["term"] - 36) / 24.0
                factor_diff = abs(c["factor"] - 0.85) * 2.0
                return term_diff + factor_diff + (c["pd"] * 3.0)

            c3 = sorted(rem_for_bal, key=balanced_score)[0]
            c3_entry = self._build_optimization_entry(c3, "Balanced Compromise", "balanced_compromise")

            self.alternative_options = [c2_entry, c3_entry]
            self.optimization_options = [self.recommended_option, c2_entry, c3_entry]
            print(f"[DEBUG OPT] Lazy Loaded {len(self.alternative_options)} alternative options successfully.")
        except Exception as e:
            print(f"[DEBUG OPT] Lỗi khi _compute_alternative_options: {e}")
            self.alternative_options = []

    @rx.event
    def ai_auto_optimize(self):
        """AI Auto-Optimize: Tự động tìm kiếm kịch bản tái cơ cấu tối ưu (Strict On-Demand - Lazy Loading).
        Khi kích hoạt: CHỈ tìm nghiệm cho DUY NHẤT 1 phương án chính (Recommended Proposal).
        Hai phương án phụ sẽ được tính toán khi người dùng nhấn xem thêm (Lazy Loading).
        """
        print(f"[DEBUG OPT] >>> Bắt đầu chạy tối ưu cho hồ sơ... selected_client_id={self.selected_client_id}")
        self.is_optimizing = True
        yield

        try:
            if not self.selected_client_id or self.selected_client_id == "None":
                print(f"[DEBUG OPT] CẢNH BÁO: selected_client_id rỗng! Thử nạp demo và fallback...")
                if not self.available_client_ids:
                    self.load_demo_clients()
                if self.available_client_ids:
                    self.select_and_evaluate_client(str(self.available_client_ids[0]))
                    print(f"[DEBUG OPT] Đã tự động chọn và nạp hồ sơ fallback ID={self.selected_client_id}")
                else:
                    print(f"[DEBUG OPT] Không có available_client_ids! Dừng tối ưu.")
                    self.is_optimizing = False
                    return

            client_series = get_client_row_data(self.selected_client_id)
            if client_series is None:
                print(f"[DEBUG OPT] get_client_row_data trả về None cho ID: {self.selected_client_id}")
                self.is_optimizing = False
                return

            pool = self._find_candidate_pool()
            if not pool:
                print(f"[DEBUG OPT] CẢNH BÁO: Không có ứng viên nào trong pool!")
                self.optimization_options = []
                self.recommended_option = dict(DEFAULT_RECOMMENDED_OPTION)
                self.alternative_options = []
                self.show_optimization_results = False
                self.alternatives_loaded = False
                self.show_alternative_options = False
                return

            # CHỈ chạy thuật toán tìm nghiệm cho DUY NHẤT 1 phương án chính (Recommended Proposal)
            c1 = sorted(pool, key=lambda x: (-x["credit"], -x["term"], x["pd"]))[0]
            c1_entry = self._build_optimization_entry(c1, "Recommended Proposal", "recommended")

            self.recommended_option = c1_entry
            self.optimization_options = [c1_entry]
            self.alternative_options = []
            self.alternatives_loaded = False
            self.show_alternative_options = False
            self.show_optimization_results = True

            print(f"[DEBUG OPT] Đã tìm xong Recommended Option: {c1_entry['title']} | {c1_entry['credit_display']} | {c1_entry['term_display']} | PD: {c1_entry['pd_display']}")
        except Exception as e:
            print(f"[DEBUG OPT] LỖI NGOẠI LỆ trong ai_auto_optimize: {e}")
            self.show_optimization_results = False
        finally:
            self.is_optimizing = False

    @rx.event
    def apply_optimization_option(self, option: Any = None):
        """Áp dụng kịch bản tối ưu hóa được chọn vào Simulator."""
        try:
            print(f"[DEBUG OPT] >>> Bấm Áp dụng kịch bản: {option}")
            if option is None:
                option = self.recommended_option
            elif isinstance(option, int):
                if 0 <= option < len(self.optimization_options):
                    option = self.optimization_options[option]
                elif option == 0 and self.recommended_option:
                    option = self.recommended_option
            elif isinstance(option, dict):
                pass
            else:
                return

            self.sim_amt_credit = float(option.get("credit", self.sim_amt_credit))
            self.sim_term_months = int(option.get("term", self.sim_term_months))
            self.sim_amt_annuity = float(option.get("annuity", self.sim_amt_annuity))
            self.sim_dti = float(option.get("dti", self.sim_dti))

            self.sim_amt_credit_str = f"{int(self.sim_amt_credit):,}"
            self.sim_term_months_str = str(int(self.sim_term_months))
            self.sim_amt_annuity_str = f"{int(self.sim_amt_annuity):,}"
            self.sim_amt_income_str = f"{int(self.sim_amt_income_total):,}"

            self.recalculate_simulation_pd()
            print(f"[DEBUG OPT] Đã cập nhật Simulator: credit={self.sim_amt_credit}, term={self.sim_term_months}, annuity={self.sim_amt_annuity}, dti={self.sim_dti}")
        except Exception as e:
            print(f"[DEBUG OPT] Lỗi khi apply_optimization_option: {e}")
            print(f"[apply_optimization_option] Error: {e}")

    @rx.event
    def close_optimization_results(self):
        """Đóng/ẩn khung gợi ý kịch bản tối ưu."""
        self.show_optimization_results = False

    # Alias tương thích ngược
    auto_optimize_terms = ai_auto_optimize