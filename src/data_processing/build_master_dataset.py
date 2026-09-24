import os
import gc
import re
import json
import time
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore', category=pd.errors.PerformanceWarning)

# Import centralized configurations & paths from src/config.py
from src.config import (
    CONFIG_PATH,
    SCHEMA_PATH,
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


def prepare_bureau_balance_client_level() -> pd.DataFrame:
    """Maps loan-level bureau balance (SK_ID_BUREAU) to client-level (SK_ID_CURR)."""
    bb_path = find_file("df_bureau_balance_clean_fe.parquet")
    if not bb_path or not os.path.exists(RAW_BUREAU_MAP_PATH):
        print("   ⚠️ Bureau balance file hoặc raw bureau.csv missing. Bỏ qua BB aggregation.")
        return pd.DataFrame()

    print(f"🔹 Processing Bureau Balance từ: {bb_path}")
    df_bb = pd.read_parquet(bb_path)
    df_map = pd.read_csv(RAW_BUREAU_MAP_PATH, usecols=['SK_ID_CURR', 'SK_ID_BUREAU'])

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


def build_master_dataset():
    start_time = time.time()
    print("=" * 80)
    print("🚀 EXECUTING MASTER PRODUCTION PIPELINE (build_master_dataset.py)")
    print("=" * 80)

    # 1. Load Data Contract & Feature Metadata
    print("📦 Loading Data Contract & Feature Metadata...")
    config = load_json_artifact(CONFIG_PATH)
    metadata = load_json_artifact(SCHEMA_PATH)

    target_features = config["feature_names"]
    categorical_mappings = metadata.get("categorical_mappings", {})

    # 2. Process Raw Main Application Table
    print(f"📖 Loading and transforming raw main application test: {RAW_TEST_PATH}")
    df_raw_test = pd.read_csv(RAW_TEST_PATH)
    df_master = transform_application_for_inference(df_raw_test)

    if 'SK_ID_CURR' not in df_master.columns and df_master.index.name == 'SK_ID_CURR':
        df_master = df_master.reset_index()

    initial_rows = len(df_master)
    print(f"   • Baseline Master Test records: {initial_rows:,} clients | {df_master.shape[1]} columns")

    # 3. Step-by-Step Cascading Joins with Sub-Tables (Sử dụng bộ dò file tự động)
    sub_tables = [
        ("Bureau", "df_bureau_clean_fe.parquet"),
        ("Previous Application", "prev_app_clean_fe_v2.parquet"),
        ("POS CASH Balance", "pos_cash_clean_FE.parquet"),
        ("Installments Payments", "installments_payments_clean_FE.parquet"),
        ("Credit Card Balance", "credit_card_balance_aggregated.parquet")
    ]

    df_bb_curr = prepare_bureau_balance_client_level()
    if not df_bb_curr.empty:
        cols_to_use = df_bb_curr.columns.difference(df_master.columns).tolist() + ['SK_ID_CURR']
        df_master = df_master.merge(df_bb_curr[cols_to_use], on='SK_ID_CURR', how='left')
        del df_bb_curr
        gc.collect()

    for name, filename in sub_tables:
        resolved_path = find_file(filename)
        if not resolved_path:
            print(f"⚠️ [{name}] File '{filename}' not found in any search path. Skipping!")
            continue

        print(f"⏳ Left-joining with {name} từ {resolved_path}...")
        df_sub = pd.read_parquet(resolved_path)

        if 'SK_ID_CURR' not in df_sub.columns:
            if df_sub.index.name == 'SK_ID_CURR' or 'SK_ID_CURR' in str(df_sub.index.names):
                df_sub = df_sub.reset_index()
            else:
                print(f"   ❌ Missing 'SK_ID_CURR' in {name}. Skipping!")
                del df_sub
                continue

        cols_to_use = df_sub.columns.difference(df_master.columns).tolist() + ['SK_ID_CURR']
        df_master = df_master.merge(df_sub[cols_to_use], on='SK_ID_CURR', how='left')
        print(f"   ✓ Merged! Current total columns: {df_master.shape[1]}")

        del df_sub
        gc.collect()

    # 4. Integrity Validation
    assert len(
        df_master) == initial_rows, f"❌ Data Integrity Failed: Row count changed from {initial_rows} to {len(df_master)}!"
    print(f"✅ Row integrity verified: Exact {initial_rows:,} clients preserved.")

    # 5. Fair-Lending Enforcement: Strip prohibited demographic and proxy attributes
    drop_fair = [c for c in FAIR_PROHIBITED_COLUMNS if c in df_master.columns]
    if drop_fair:
        df_master.drop(columns=drop_fair, inplace=True)
        print(f"🛡️ Fair Lending: Stripped {len(drop_fair)} sensitive/proxy attributes.")

    # 6. Data Contract Feature Alignment (Tối ưu chống phân mảnh RAM)
    print("📐 Aligning feature matrix with trained ensemble model contract...")
    final_cols = ['SK_ID_CURR'] + target_features

    # Sử dụng reindex thay cho vòng lặp gán np.nan (Triệt tiêu 100% PerformanceWarning)
    df_final = df_master.reindex(columns=final_cols)

    # Ép kiểu dữ liệu phân loại theo schema
    for cat_col, map_info in categorical_mappings.items():
        if cat_col in df_final.columns:
            valid_categories = list(map_info.get("label_to_code", {}).keys())
            if valid_categories:
                df_final[cat_col] = pd.Categorical(df_final[cat_col].astype(str), categories=valid_categories)

    # 7. Persist to Isolated Production Directory
    os.makedirs(PROD_DIR, exist_ok=True)

    print(f"💾 Saving complete production dataset to: {OUTPUT_MASTER_PATH}")
    df_final.to_parquet(OUTPUT_MASTER_PATH, compression='snappy', index=False)

    demo_df = df_final.head(1000).copy()
    demo_df.to_parquet(OUTPUT_DEMO_PATH, compression='snappy', index=False)
    print(f"⚡ Exported {len(demo_df):,} demo records to: {OUTPUT_DEMO_PATH}")

    total_time = time.time() - start_time
    print("=" * 80)
    print(f"🎉 MASTER DATASET BUILD COMPLETE IN: {total_time:.2f} SECONDS")
    print(f"📊 Final Master Shape : {df_final.shape[0]:,} clients | {len(target_features)} features (100% Aligned)")
    print(f"📂 Output Location    : {OUTPUT_MASTER_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    build_master_dataset()
