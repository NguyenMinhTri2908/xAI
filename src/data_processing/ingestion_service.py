import os
import io
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from src.config import (
    DEMO_SAMPLES_PARQUET,
    MASTER_TEST_PARQUET,
    DATA_RAW_DIR
)
from src.data_processing.main_pipeline import transform_application_for_inference

RAW_APPLICATION_CSV = os.path.join(DATA_RAW_DIR, "application_test.csv")

PRESET_DATASETS = [
    {
        "id": "demo_samples",
        "name": "demo_samples.parquet (1,000 Demo Clients)",
        "path": DEMO_SAMPLES_PARQUET
    },
    {
        "id": "test_master",
        "name": "test_features_master.parquet (Master Production)",
        "path": MASTER_TEST_PARQUET
    },
    {
        "id": "raw_application",
        "name": "application_test.csv (Raw Home Credit)",
        "path": RAW_APPLICATION_CSV
    }
]

# In-memory storage for currently active dataset
_ACTIVE_DATASET: Optional[pd.DataFrame] = None
_ACTIVE_SOURCE_NAME: str = "demo_samples.parquet"


def get_preset_options() -> List[Dict[str, str]]:
    """Trả về danh sách các dataset mẫu có sẵn trong hệ thống."""
    return PRESET_DATASETS


def set_active_dataset(df: pd.DataFrame, source_name: str):
    """Cập nhật dataset đang được chọn trong bộ nhớ RAM."""
    global _ACTIVE_DATASET, _ACTIVE_SOURCE_NAME
    _ACTIVE_DATASET = df
    _ACTIVE_SOURCE_NAME = source_name


def get_active_dataset() -> pd.DataFrame:
    """Lấy dataset đang hoạt động. Nếu chưa nạp, tự động nạp demo_samples.parquet."""
    global _ACTIVE_DATASET
    if _ACTIVE_DATASET is None:
        if os.path.exists(DEMO_SAMPLES_PARQUET):
            _ACTIVE_DATASET = pd.read_parquet(DEMO_SAMPLES_PARQUET)
        else:
            _ACTIVE_DATASET = pd.DataFrame()
    return _ACTIVE_DATASET


def get_active_source_name() -> str:
    return _ACTIVE_SOURCE_NAME


def load_dataset_from_source(source_id: str) -> Tuple[pd.DataFrame, str]:
    """
    Nạp dữ liệu từ preset có sẵn (data/production hoặc data/raw).
    """
    if source_id == "demo_samples":
        if not os.path.exists(DEMO_SAMPLES_PARQUET):
            raise FileNotFoundError(f"File not found: {DEMO_SAMPLES_PARQUET}")
        df = pd.read_parquet(DEMO_SAMPLES_PARQUET)
        source_label = "demo_samples.parquet (1,000 clients)"
    elif source_id == "test_master":
        if not os.path.exists(MASTER_TEST_PARQUET):
            raise FileNotFoundError(f"File not found: {MASTER_TEST_PARQUET}")
        # Đọc 2,000 dòng đầu tiên của master để tốc độ phản hồi cực nhanh trên dashboard
        df = pd.read_parquet(MASTER_TEST_PARQUET).head(2000)
        source_label = f"test_features_master.parquet ({len(df):,} clients)"
    elif source_id == "raw_application":
        if not os.path.exists(RAW_APPLICATION_CSV):
            raise FileNotFoundError(f"File not found: {RAW_APPLICATION_CSV}")
        raw_df = pd.read_csv(RAW_APPLICATION_CSV, nrows=200)
        df = transform_application_for_inference(raw_df)
        source_label = f"application_test.csv ({len(df)} clients processed)"
    else:
        # Fallback to demo
        df = pd.read_parquet(DEMO_SAMPLES_PARQUET)
        source_label = "demo_samples.parquet"

    # Đảm bảo có SK_ID_CURR
    if "SK_ID_CURR" not in df.columns:
        df["SK_ID_CURR"] = range(100001, 100001 + len(df))

    set_active_dataset(df, source_label)
    return df, source_label


def load_dataset_from_upload(file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, str]:
    """
    Xử lý file CSV hoặc Parquet do người dùng upload.
    Tự động nhận diện nếu cần chạy transform_application_for_inference.
    """
    is_parquet = filename.lower().endswith(".parquet") or filename.lower().endswith(".pq")
    is_csv = filename.lower().endswith(".csv") or filename.lower().endswith(".txt")

    if is_parquet:
        df = pd.read_parquet(io.BytesIO(file_bytes))
    else:
        # Mặc định đọc theo CSV
        try:
            df = pd.read_csv(io.BytesIO(file_bytes))
        except Exception:
            df = pd.read_parquet(io.BytesIO(file_bytes))

    # Nếu file raw (có DAYS_BIRTH / DAYS_EMPLOYED mà thiếu các biến phái sinh như AGE_YEARS)
    if ("DAYS_BIRTH" in df.columns or "AMT_CREDIT" in df.columns) and "EXT_SOURCE_MEAN" not in df.columns:
        try:
            df = transform_application_for_inference(df)
        except Exception as e:
            print(f"[IngestionService] Notice: raw transform skipped or failed: {e}")

    # Đảm bảo có SK_ID_CURR
    if "SK_ID_CURR" not in df.columns:
        if df.index.name == "SK_ID_CURR":
            df = df.reset_index()
        else:
            df["SK_ID_CURR"] = range(100001, 100001 + len(df))

    source_label = f"{filename} ({len(df)} records)"
    set_active_dataset(df, source_label)
    return df, source_label


def get_active_client_ids() -> List[str]:
    """Lấy danh sách ID đã được sắp xếp tăng dần."""
    df = get_active_dataset()
    if df.empty or "SK_ID_CURR" not in df.columns:
        return []
    ids = sorted(df["SK_ID_CURR"].dropna().astype(int).unique().tolist())
    return [str(i) for i in ids]


def get_client_row_data(client_id: str) -> Optional[pd.Series]:
    """Trích xuất hàng dữ liệu của client được chỉ định."""
    df = get_active_dataset()
    if df.empty or "SK_ID_CURR" not in df.columns:
        return None

    try:
        int_id = int(client_id)
        matches = df[df["SK_ID_CURR"] == int_id]
    except (ValueError, TypeError):
        matches = df[df["SK_ID_CURR"].astype(str) == str(client_id)]

    if matches.empty:
        return None
    return matches.iloc[0]


_SCORING_ENGINE = None


def get_scoring_engine():
    """Singleton engine cache để tránh tải lại model mỗi lần hiển thị bảng."""
    global _SCORING_ENGINE
    if _SCORING_ENGINE is None:
        from src.engine.credit_scoring import CreditScoringEngine
        _SCORING_ENGINE = CreditScoringEngine()
    return _SCORING_ENGINE


def format_df_to_summary_records(sub_df: pd.DataFrame, compute_pd: bool = True) -> List[Dict[str, Any]]:
    """Chuyển đổi DataFrame thành danh sách record chuẩn hiển thị cho Client Registry."""
    if sub_df.empty:
        return []

    batch_preds = []
    if compute_pd:
        try:
            engine = get_scoring_engine()
            batch_preds = engine.predict_batch_pd(sub_df)
        except Exception as e:
            print(f"[IngestionService] Batch PD scoring warning: {e}")

    records = []
    for idx, (_, row) in enumerate(sub_df.iterrows()):
        sk_id = str(row.get("SK_ID_CURR", ""))

        income_val = row.get("AMT_INCOME_TOTAL", None)
        try:
            income_num = float(income_val) if pd.notna(income_val) else 0.0
            income_str = f"${income_num:,.0f}" if income_num > 0 else "None"
        except (ValueError, TypeError):
            income_str = "None"

        credit_val = row.get("AMT_CREDIT", None)
        try:
            credit_num = float(credit_val) if pd.notna(credit_val) else 0.0
            credit_str = f"${credit_num:,.0f}" if credit_num > 0 else "None"
        except (ValueError, TypeError):
            credit_str = "None"

        annuity_val = row.get("AMT_ANNUITY", None)
        try:
            annuity_num = float(annuity_val) if pd.notna(annuity_val) else 0.0
            annuity_str = f"${annuity_num:,.0f} / mo" if annuity_num > 0 else "None"
        except (ValueError, TypeError):
            annuity_str = "None"

        pd_display = "N/A"
        tier = "N/A"
        decision = "N/A"
        pd_color = "#94A3B8"
        if idx < len(batch_preds):
            pred = batch_preds[idx]
            pd_display = pred.get("pd_display", "N/A")
            tier = pred.get("tier", "N/A")
            decision = pred.get("decision", "N/A")
            pd_val = pred.get("pd_val", 0.0)
            if pd_val <= 0.15:
                pd_color = "#10B981"  # Xanh lá (Low risk)
            elif pd_val <= 0.17:
                pd_color = "#F59E0B"  # Vàng hổ phách (Gray zone)
            else:
                pd_color = "#EF4444"  # Đỏ (High risk)

        records.append({
            "SK_ID_CURR": sk_id,
            "INCOME_DISPLAY": income_str,
            "CREDIT_DISPLAY": credit_str,
            "ANNUITY_DISPLAY": annuity_str,
            "PD_DISPLAY": pd_display,
            "TIER": tier,
            "DECISION": decision,
            "PD_COLOR": pd_color,
        })

    return records


def get_client_table_summary(limit: int = 100, compute_pd: bool = True) -> List[Dict[str, Any]]:
    """Tạo tóm tắt danh sách khách hàng phục vụ Client Registry và Queue Drawer."""
    df = get_active_dataset()
    if df.empty:
        return []
    sub_df = df.head(limit).copy()
    return format_df_to_summary_records(sub_df, compute_pd=compute_pd)
