import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
import reflex as rx
import pandas as pd
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


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
    """Tự động quét DUY NHẤT thư mục data/production, đọc metadata và kiểm tra pipeline readiness."""
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


class BaseUnderwritingState(rx.State):
    """Reflex Base State quản lý trạng thái nền tảng: Alert, Loading, Dialog."""

    is_loading: bool = False
    is_ingesting: bool = False
    status_message: str = ""

    # Alert notification banner state (Thanh Alert màu xanh lục đậm trên cùng)
    show_alert: bool = False
    alert_message: str = ""
    alert_type: str = "success"  # "success" | "error"
    alert_token: int = 0

    # Dialog state
    upload_dialog_open: bool = False
    uploaded_file_name: str = ""

    # AI Optimization & Restructuring State (Shared across State hierarchy)
    is_optimizing: bool = False
    is_baseline_optimal: bool = False
    visible_proposals_count: int = 2
    is_loading_alternatives: bool = False
    alternatives_loaded: bool = False
    optimization_options: List[Dict[str, Any]] = []
    recommended_option: Optional[Dict[str, Any]] = None
    alternative_options: List[Dict[str, Any]] = []
    show_optimization_results: bool = False
    show_alternative_options: bool = False

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

    def open_upload_dialog(self):
        self.upload_dialog_open = True

    def close_upload_dialog(self):
        self.upload_dialog_open = False

