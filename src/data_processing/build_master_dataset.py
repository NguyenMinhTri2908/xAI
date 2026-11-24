import os
import gc
import json
import time
import warnings
import pandas as pd

warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

# Import centralized configurations & paths from src/config.py
from src.config import (
    CONFIG_PATH,
    SCHEMA_PATH,
    FEATURE_DICT_PATH,
    DATA_RAW_DIR,
    DATA_PRODUCTION_DIR,
    MASTER_TEST_PARQUET,
    DEMO_SAMPLES_PARQUET,
    BASE_DIR
)
from src.data_processing.main_pipeline import transform_application_for_inference


# ==============================================================================
# DYNAMIC PATH RESOLVER (Tìm file tự động ở mọi vị trí khả dĩ)
# ==============================================================================
def find_file(filename: str) -> str:
    """Tự động quét các thư mục data để tìm đúng vị trí file parquet."""
    search_dirs = [
        os.path.join(BASE_DIR, "data/preprocess/table"),
        os.path.join(BASE_DIR, "data/processed/table"),
        os.path.join(BASE_DIR, "data/processed"),
        os.path.join(BASE_DIR, "data/preprocess"),
    ]
    for d in search_dirs:
        candidate = os.path.join(d, filename)
        if os.path.exists(candidate):
            return candidate
    return ""


RAW_TEST_PATH = os.path.join(DATA_RAW_DIR, "application_test.csv")
RAW_BUREAU_MAP_PATH = os.path.join(DATA_RAW_DIR, "bureau.csv")

PROD_DIR = DATA_PRODUCTION_DIR
OUTPUT_MASTER_PATH = MASTER_TEST_PARQUET
OUTPUT_DEMO_PATH = DEMO_SAMPLES_PARQUET

FAIR_PROHIBITED_COLUMNS = [
    'CODE_GENDER', 'NAME_FAMILY_STATUS', 'CNT_CHILDREN', 'CNT_FAM_MEMBERS',
    'INCOME_PER_PERSON', 'OBS_30_CNT_SOCIAL_CIRCLE', 'DEF_30_CNT_SOCIAL_CIRCLE',
    'OBS_60_CNT_SOCIAL_CIRCLE', 'DEF_60_CNT_SOCIAL_CIRCLE',
    'DEF_TO_OBS_30', 'DEF_TO_OBS_60'
]


def load_json_artifact(filepath: str) -> dict:
    """Loads a JSON configuration artifact safely."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Missing required artifact: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def update_feature_dictionary(feature_table_map: dict, output_path: str):
    """
    Cập nhật từ điển đặc trưng chuẩn tinh gọn:
    - Chỉ lưu duy nhất 2 trường: 'table' (tên bảng raw) và 'description'.
    - Lọc bỏ sạch sẽ các trường rác cũ (source, tag).
    - Bảo toàn 100% nội dung description đã tự nhập tay trước đó.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    existing_dict = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                existing_dict = json.load(f)
        except Exception:
            existing_dict = {}

    cleaned_dict = {}
    for feat, tbl in feature_table_map.items():
        # Lấy description cũ nếu đã có (và không phải là giá trị tự gen dạng title-case cũ)
        old_desc = ""
        if feat in existing_dict:
            old_desc = existing_dict[feat].get("description", "")
            # Nếu description cũ trùng khớp với tên cột biến đổi title thì reset rỗng để nhập tay
            if old_desc == feat.replace("_", " ").title():
                old_desc = ""

        # Cấu trúc tinh gọn tuyệt đối: CHỈ CÓ table VÀ description
        cleaned_dict[feat] = {
            "table": tbl,
            "description": old_desc
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(cleaned_dict, f, indent=4, ensure_ascii=False)
    print(f"📖 Đã tinh gọn và đồng bộ {len(cleaned_dict)} đặc trưng vào: {output_path}")


def prepare_bureau_balance_client_level(client_ids: set = None) -> pd.DataFrame:
    """Maps loan-level bureau balance (SK_ID_BUREAU) to client-level (SK_ID_CURR)."""
    bb_path = find_file("df_bureau_balance_clean_fe.parquet")
    if not bb_path or not os.path.exists(RAW_BUREAU_MAP_PATH):
        print("   ⚠️ Bureau balance file hoặc raw bureau.csv missing. Bỏ qua BB aggregation.")
        return pd.DataFrame()

    print(f"🔹 Processing Bureau Balance từ: {bb_path}")
    df_map = pd.read_csv(RAW_BUREAU_MAP_PATH, usecols=['SK_ID_CURR', 'SK_ID_BUREAU'])
    if client_ids is not None:
        df_map = df_map[df_map['SK_ID_CURR'].isin(client_ids)]
        if df_map.empty:
            return pd.DataFrame()

    df_bb = pd.read_parquet(bb_path)
    if client_ids is not None:
        df_bb = df_bb[df_bb['SK_ID_BUREAU'].isin(set(df_map['SK_ID_BUREAU']))]
        if df_bb.empty:
            return pd.DataFrame()

    df_bb_mapped = df_bb.merge(df_map, on='SK_ID_BUREAU', how='inner').drop(columns=['SK_ID_BUREAU'])

    feature_cols = [c for c in df_bb_mapped.columns if c != 'SK_ID_CURR']
    bb_aggs = {}
    for col in feature_cols:
        if any(k in col for k in ['SUM', 'COUNT', 'RECENT']):
            bb_aggs[col] = ['sum', 'max', 'mean']
        else:
            bb_aggs[col] = ['mean', 'max']

    df_bb_curr = df_bb_mapped.groupby('SK_ID_CURR').agg(bb_aggs)
    df_bb_curr.columns = [f"{col}_{stat.upper()}" for col, stat in df_bb_curr.columns]
    df_bb_curr.reset_index(inplace=True)

    del df_bb, df_map, df_bb_mapped
    gc.collect()
    print(f"   ✓ Successfully aggregated BB to {len(df_bb_curr):,} clients.")
    return df_bb_curr


def process_master_pipeline(df_raw: pd.DataFrame, update_dict: bool = False) -> pd.DataFrame:
    """
    Pipeline chính tiền xử lý và merge các bảng phụ để tạo ra đầy đủ 891 features chuẩn mô hình:
    - Nhận df_raw từ tệp upload hoặc dataframe ứng dụng.
    - Chạy transform_application_for_inference nếu là bảng application thô.
    - Left-join với các bảng phụ: bureau, previous_application, POS_CASH, installments, credit_card, bureau_balance.
    - Loại bỏ các biến nhạy cảm Fair Lending.
    - Align chính xác 891 features theo đúng Data Contract của mô hình.
    - Ép kiểu biến phân loại theo Schema.
    """
    config = load_json_artifact(CONFIG_PATH)
    metadata = load_json_artifact(SCHEMA_PATH)

    target_features = config["feature_names"]
    categorical_mappings = metadata.get("categorical_mappings", {})

    # 1. Đảm bảo có khóa chính SK_ID_CURR
    if 'SK_ID_CURR' not in df_raw.columns:
        if df_raw.index.name == 'SK_ID_CURR' or 'SK_ID_CURR' in str(df_raw.index.names):
            df_master = df_raw.reset_index()
        else:
            raise KeyError("Uploaded dataset must contain 'SK_ID_CURR' column as client identifier.")
    else:
        df_master = df_raw.copy()

    # 2. Nếu tệp upload đã là preprocessed dataset (đã có đủ 891 features chuẩn)
    if len(df_master.columns) >= len(target_features) and set(target_features[:20]).issubset(set(df_master.columns)):
        final_cols = ['SK_ID_CURR'] + target_features
        df_final = df_master.reindex(columns=final_cols)
        for cat_col, map_info in categorical_mappings.items():
            if cat_col in df_final.columns:
                valid_categories = list(map_info.get("label_to_code", {}).keys())
                if valid_categories:
                    df_final[cat_col] = pd.Categorical(df_final[cat_col].astype(str), categories=valid_categories)
        return df_final

    # 3. Tiền xử lý Application nếu là bảng thô
    if ("DAYS_BIRTH" in df_master.columns or "AMT_CREDIT" in df_master.columns) and "EXT_SOURCE_MEAN" not in df_master.columns:
        df_master = transform_application_for_inference(df_master)

    if 'SK_ID_CURR' not in df_master.columns and df_master.index.name == 'SK_ID_CURR':
        df_master = df_master.reset_index()

    initial_rows = len(df_master)
    client_ids = set(df_master['SK_ID_CURR'].dropna().astype(int))

    column_source_tracker = {}
    for col in df_master.columns:
        if col != 'SK_ID_CURR':
            column_source_tracker[col] = "application"

    # 4. Merge Bureau Balance
    df_bb_curr = prepare_bureau_balance_client_level(client_ids=client_ids)
    if not df_bb_curr.empty:
        cols_to_use = df_bb_curr.columns.difference(df_master.columns).tolist() + ['SK_ID_CURR']
        for col in cols_to_use:
            if col != 'SK_ID_CURR':
                column_source_tracker[col] = "bureau_balance"
        df_master = df_master.merge(df_bb_curr[cols_to_use], on='SK_ID_CURR', how='left')
        del df_bb_curr
        gc.collect()

    # 5. Cascading Left Joins với các Sub-Tables (Lọc nhanh theo client_ids để tối ưu tốc độ)
    sub_tables = [
        ("bureau", "df_bureau_clean_fe.parquet"),
        ("previous_application", "prev_app_clean_fe_v2.parquet"),
        ("POS_CASH_balance", "pos_cash_clean_FE.parquet"),
        ("installments_payments", "installments_payments_clean_FE.parquet"),
        ("credit_card_balance", "credit_card_balance_aggregated.parquet")
    ]

    for raw_name, filename in sub_tables:
        resolved_path = find_file(filename)
        if not resolved_path:
            continue

        try:
            df_sub = pd.read_parquet(resolved_path)
            if 'SK_ID_CURR' not in df_sub.columns:
                if df_sub.index.name == 'SK_ID_CURR' or 'SK_ID_CURR' in str(df_sub.index.names):
                    df_sub = df_sub.reset_index()
                else:
                    del df_sub
                    continue

            # Tối ưu: Lọc chỉ những client_ids cần merge
            df_sub = df_sub[df_sub['SK_ID_CURR'].isin(client_ids)]
            cols_to_use = df_sub.columns.difference(df_master.columns).tolist() + ['SK_ID_CURR']
            for col in cols_to_use:
                if col != 'SK_ID_CURR':
                    column_source_tracker[col] = raw_name

            df_master = df_master.merge(df_sub[cols_to_use], on='SK_ID_CURR', how='left')
            del df_sub
            gc.collect()
        except Exception as e:
            print(f"[process_master_pipeline] Warning merging {raw_name}: {e}")

    # 6. Fair-Lending Enforcement: Loại bỏ biến cấm
    drop_fair = [c for c in FAIR_PROHIBITED_COLUMNS if c in df_master.columns]
    if drop_fair:
        df_master.drop(columns=drop_fair, inplace=True)

    # 7. Data Contract Feature Alignment: Giữ đúng 891 features theo thứ tự mô hình
    final_cols = ['SK_ID_CURR'] + target_features
    df_final = df_master.reindex(columns=final_cols)

    # Cập nhật feature dictionary nếu được chỉ định
    if update_dict:
        model_feature_table_map = {
            feat: column_source_tracker.get(feat, "application")
            for feat in target_features
        }
        update_feature_dictionary(model_feature_table_map, FEATURE_DICT_PATH)

    # 8. Ép kiểu dữ liệu phân loại theo schema
    for cat_col, map_info in categorical_mappings.items():
        if cat_col in df_final.columns:
            valid_categories = list(map_info.get("label_to_code", {}).keys())
            if valid_categories:
                df_final[cat_col] = pd.Categorical(df_final[cat_col].astype(str), categories=valid_categories)

    return df_final


def build_master_dataset():
    start_time = time.time()
    print("=" * 80)
    print("🚀 EXECUTING MASTER PRODUCTION PIPELINE (build_master_dataset.py)")
    print("=" * 80)

    print(f"📖 Loading and transforming raw main application test: {RAW_TEST_PATH}")
    df_raw_test = pd.read_csv(RAW_TEST_PATH)
    df_final = process_master_pipeline(df_raw_test, update_dict=True)

    # Persist to Isolated Production Directory
    os.makedirs(PROD_DIR, exist_ok=True)
    print(f"💾 Saving complete production dataset to: {OUTPUT_MASTER_PATH}")
    df_final.to_parquet(OUTPUT_MASTER_PATH, compression='snappy', index=False)

    demo_df = df_final.head(1000).copy()
    demo_df.to_parquet(OUTPUT_DEMO_PATH, compression='snappy', index=False)
    print(f"⚡ Exported {len(demo_df):,} demo records to: {OUTPUT_DEMO_PATH}")

    total_time = time.time() - start_time
    print("=" * 80)
    print(f"🎉 MASTER DATASET BUILD COMPLETE IN: {total_time:.2f} SECONDS")
    print(f"📊 Final Master Shape : {df_final.shape[0]:,} clients | {df_final.shape[1]-1} features (100% Aligned)")
    print(f"📂 Output Location    : {OUTPUT_MASTER_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    build_master_dataset()