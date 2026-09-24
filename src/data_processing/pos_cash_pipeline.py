import os
import gc
import re
import time
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

def process_pos_cash_pipeline(raw_pos_path: str, output_parquet_path: str = None) -> pd.DataFrame:
    """Production ETL Pipeline for POS CASH Balance Data (10M+ records).
    Transforms monthly snapshots into installment progress metrics, regulatory delinquency
    buckets, time-decayed delinquency signals, and aggregates them by SK_ID_CURR.
    """
    start_time = time.time()
    print("=" * 75)
    print("🚀 EXECUTING POS CASH BALANCE PROCESSING PIPELINE")
    print("=" * 75)

    # 1. Load Raw Dataset
    if not os.path.exists(raw_pos_path):
        raise FileNotFoundError(f"Input file not found at: {raw_pos_path}")

    print(f"📖 Loading raw POS_CASH_balance from: {raw_pos_path}")
    df_pos = pd.read_csv(raw_pos_path)
    print(f"   • Loaded {len(df_pos):,} records across {df_pos.shape[1]} raw columns.")

    # 2. Process MONTHS_BALANCE (Temporal Decay Metrics)
    df_pos['POS_MONTHS_BALANCE_YEARS'] = df_pos['MONTHS_BALANCE'].abs() / 12.0
    df_pos['POS_IS_RECENT_6M'] = (df_pos['MONTHS_BALANCE'] >= -6).astype(int)
    df_pos['POS_IS_RECENT_12M'] = (df_pos['MONTHS_BALANCE'] >= -12).astype(int)
    df_pos['POS_IS_RECENT_24M'] = (df_pos['MONTHS_BALANCE'] >= -24).astype(int)

    # 3. Process CNT_INSTALMENT
    df_pos['POS_CNT_INSTALMENT_IS_NA'] = df_pos['CNT_INSTALMENT'].isna().astype(int)
    df_pos['POS_CNT_INSTALMENT_CLEAN'] = df_pos['CNT_INSTALMENT'].fillna(0.0)
    df_pos['POS_IS_SHORT_TERM'] = (
        (df_pos['POS_CNT_INSTALMENT_CLEAN'] > 0.0) & (df_pos['POS_CNT_INSTALMENT_CLEAN'] <= 12.0)
    ).astype(int)
    df_pos['POS_IS_LONG_TERM'] = (df_pos['POS_CNT_INSTALMENT_CLEAN'] > 24.0).astype(int)

    # 4. Process CNT_INSTALMENT_FUTURE & Completion Progress
    df_pos['POS_CNT_INSTALMENT_FUTURE_IS_NA'] = df_pos['CNT_INSTALMENT_FUTURE'].isna().astype(int)
    df_pos['POS_CNT_INSTALMENT_FUTURE_CLEAN'] = df_pos['CNT_INSTALMENT_FUTURE'].fillna(0.0)
    df_pos['POS_IS_ACTIVE_LOAN'] = (df_pos['POS_CNT_INSTALMENT_FUTURE_CLEAN'] > 0.0).astype(int)

    if 'POS_CNT_INSTALMENT_CLEAN' in df_pos.columns:
        df_pos['POS_COMPLETION_RATIO'] = 1.0 - (
            df_pos['POS_CNT_INSTALMENT_FUTURE_CLEAN'] / (df_pos['POS_CNT_INSTALMENT_CLEAN'] + 1e-5)
        )
        df_pos['POS_COMPLETION_RATIO'] = df_pos['POS_COMPLETION_RATIO'].clip(lower=0.0, upper=1.0)
    else:
        df_pos['POS_COMPLETION_RATIO'] = 0.0

    df_pos['POS_IS_NEAR_COMPLETION'] = (
        (df_pos['POS_CNT_INSTALMENT_FUTURE_CLEAN'] > 0.0) & (df_pos['POS_CNT_INSTALMENT_FUTURE_CLEAN'] <= 3.0)
    ).astype(int)

    # 5. One-Hot Encoding for NAME_CONTRACT_STATUS (Strict int dtype)
    df_pos['NAME_CONTRACT_STATUS'] = df_pos['NAME_CONTRACT_STATUS'].fillna('XNA')
    df_pos = pd.get_dummies(df_pos, columns=['NAME_CONTRACT_STATUS'], prefix='POS_STATUS', dummy_na=False, dtype=int)

    status_cols = [col for col in df_pos.columns if col.startswith('POS_STATUS_')]
    for col in status_cols:
        clean_col = re.sub(r'[^\w_]', '_', col)
        clean_col = re.sub(r'_{2,}', '_', clean_col)
        df_pos.rename(columns={col: clean_col}, inplace=True)

    # 6. Process SK_DPD (Regulatory Delinquency Tiers)
    df_pos['POS_IS_DPD'] = (df_pos['SK_DPD'] > 0).astype(int)
    df_pos['POS_IS_DPD_1_30'] = ((df_pos['SK_DPD'] >= 1) & (df_pos['SK_DPD'] <= 30)).astype(int)
    df_pos['POS_IS_DPD_30'] = (df_pos['SK_DPD'] > 30).astype(int)
    df_pos['POS_IS_DPD_60'] = (df_pos['SK_DPD'] > 60).astype(int)
    df_pos['POS_IS_DPD_90'] = (df_pos['SK_DPD'] > 90).astype(int)

    # 7. Process SK_DPD_DEF (Tolerance-Adjusted Delinquency Tiers)
    df_pos['POS_IS_DPD_DEF'] = (df_pos['SK_DPD_DEF'] > 0).astype(int)
    df_pos['POS_IS_DPD_DEF_1_30'] = ((df_pos['SK_DPD_DEF'] >= 1) & (df_pos['SK_DPD_DEF'] <= 30)).astype(int)
    df_pos['POS_IS_DPD_DEF_30'] = (df_pos['SK_DPD_DEF'] > 30).astype(int)
    df_pos['POS_IS_DPD_DEF_60'] = (df_pos['SK_DPD_DEF'] > 60).astype(int)
    df_pos['POS_IS_DPD_DEF_90'] = (df_pos['SK_DPD_DEF'] > 90).astype(int)

    # 8. Advanced Interaction Features
    df_pos['POS_DPD_DEF_RATIO'] = (df_pos['SK_DPD_DEF'] / (df_pos['SK_DPD'] + 1e-5)).clip(lower=0.0, upper=1.0)

    # Time-decayed delinquency signals
    df_pos['POS_DPD_RECENT_6M'] = df_pos['SK_DPD'] * df_pos['POS_IS_RECENT_6M']
    df_pos['POS_DPD_DEF_RECENT_6M'] = df_pos['SK_DPD_DEF'] * df_pos['POS_IS_RECENT_6M']
    df_pos['POS_DPD_RECENT_12M'] = df_pos['SK_DPD'] * df_pos['POS_IS_RECENT_12M']
    df_pos['POS_DPD_DEF_RECENT_12M'] = df_pos['SK_DPD_DEF'] * df_pos['POS_IS_RECENT_12M']
    df_pos['POS_DPD_RECENT_24M'] = df_pos['SK_DPD'] * df_pos['POS_IS_RECENT_24M']
    df_pos['POS_DPD_DEF_RECENT_24M'] = df_pos['SK_DPD_DEF'] * df_pos['POS_IS_RECENT_24M']

    if 'POS_CNT_INSTALMENT_FUTURE_CLEAN' in df_pos.columns and 'POS_CNT_INSTALMENT_CLEAN' in df_pos.columns:
        df_pos['POS_REMAINING_TERM_RATIO'] = (
            df_pos['POS_CNT_INSTALMENT_FUTURE_CLEAN'] / (df_pos['POS_CNT_INSTALMENT_CLEAN'] + 1e-5)
        ).clip(lower=0.0, upper=1.0)
    else:
        df_pos['POS_REMAINING_TERM_RATIO'] = 0.0

    # 9. Time-Series Trend Dynamics
    dpd_col = 'SK_DPD' if 'SK_DPD' in df_pos.columns else 'POS_IS_DPD'
    months_col = 'MONTHS_BALANCE'

    dpd_recent_3m = df_pos[dpd_col] * (df_pos[months_col] >= -3).astype(int)
    dpd_recent_6m = df_pos[dpd_col] * (df_pos[months_col] >= -6).astype(int)
    dpd_recent_12m = df_pos[dpd_col] * (df_pos[months_col] >= -12).astype(int)

    df_pos['POS_DPD_TREND_6M_12M'] = (dpd_recent_6m + 1e-5) / (dpd_recent_12m + 1e-5)
    df_pos['POS_DPD_IS_DETERIORATING'] = (dpd_recent_3m > df_pos[dpd_col].mean()).astype(int)

    completion_col = 'POS_COMPLETION_RATIO'
    if completion_col in df_pos.columns:
        df_pos['POS_COMPLETION_TREND_6M'] = df_pos[completion_col] * (df_pos[months_col] >= -6).astype(int)

    # 10. Explicit Dictionary Aggregation per SK_ID_CURR
    print("🔄 Grouping and aggregating records by SK_ID_CURR...")
    agg_dict = {
        'SK_ID_PREV': ['nunique'],
        'MONTHS_BALANCE': ['min', 'max', 'mean'],
        'POS_MONTHS_BALANCE_YEARS': ['max'],
        'POS_IS_RECENT_6M': ['mean', 'sum'],
        'POS_IS_RECENT_12M': ['mean', 'sum'],
        'POS_IS_RECENT_24M': ['mean', 'sum'],
        'POS_CNT_INSTALMENT_IS_NA': ['mean', 'sum'],
        'POS_CNT_INSTALMENT_CLEAN': ['mean', 'max', 'sum'],
        'POS_IS_SHORT_TERM': ['mean', 'sum'],
        'POS_IS_LONG_TERM': ['mean', 'sum'],
        'POS_CNT_INSTALMENT_FUTURE_IS_NA': ['mean', 'sum'],
        'POS_CNT_INSTALMENT_FUTURE_CLEAN': ['mean', 'min', 'max'],
        'POS_IS_ACTIVE_LOAN': ['mean', 'sum'],
        'POS_COMPLETION_RATIO': ['mean', 'min', 'max'],
        'POS_IS_NEAR_COMPLETION': ['mean', 'sum'],
        'POS_REMAINING_TERM_RATIO': ['mean', 'max'],
        'SK_DPD': ['max', 'mean', 'sum', 'var'],
        'POS_IS_DPD': ['mean', 'sum'],
        'POS_IS_DPD_1_30': ['mean', 'sum'],
        'POS_IS_DPD_30': ['mean', 'sum'],
        'POS_IS_DPD_60': ['mean', 'sum'],
        'POS_IS_DPD_90': ['mean', 'sum'],
        'SK_DPD_DEF': ['max', 'mean', 'sum'],
        'POS_IS_DPD_DEF': ['mean', 'sum'],
        'POS_IS_DPD_DEF_1_30': ['mean', 'sum'],
        'POS_IS_DPD_DEF_30': ['mean', 'sum'],
        'POS_IS_DPD_DEF_60': ['mean', 'sum'],
        'POS_IS_DPD_DEF_90': ['mean', 'sum'],
        'POS_DPD_DEF_RATIO': ['mean', 'max'],
        'POS_DPD_RECENT_6M': ['mean', 'sum', 'max'],
        'POS_DPD_DEF_RECENT_6M': ['mean', 'sum', 'max'],
        'POS_DPD_RECENT_12M': ['mean', 'sum', 'max'],
        'POS_DPD_DEF_RECENT_12M': ['mean', 'sum', 'max'],
        'POS_DPD_RECENT_24M': ['mean', 'sum', 'max'],
        'POS_DPD_DEF_RECENT_24M': ['mean', 'sum', 'max'],
        'POS_DPD_TREND_6M_12M': ['mean', 'max'],
        'POS_DPD_IS_DETERIORATING': ['mean', 'sum'],
        'POS_COMPLETION_TREND_6M': ['mean', 'max'],
        'POS_STATUS_Active': ['mean', 'sum'],
        'POS_STATUS_Completed': ['mean', 'sum'],
        'POS_STATUS_Signed': ['mean', 'sum'],
        'POS_STATUS_Demand': ['mean', 'sum'],
        'POS_STATUS_Returned_to_the_store': ['mean', 'sum'],
        'POS_STATUS_Approved': ['mean', 'sum'],
        'POS_STATUS_Amortized_debt': ['mean', 'sum'],
        'POS_STATUS_Canceled': ['mean', 'sum'],
        'POS_STATUS_XNA': ['mean', 'sum']
    }

    valid_agg_dict = {col: funcs for col, funcs in agg_dict.items() if col in df_pos.columns}
    pos_agg = df_pos.groupby('SK_ID_CURR').agg(valid_agg_dict)

    # 11. Flatten Column Names & Apply POS_ Prefix Uniformly
    pos_agg.columns = pd.Index([
        'POS_COUNT_UNIQUE_LOANS' if col == ('SK_ID_PREV', 'nunique') else
        f"POS_{col[0]}_{col[1].upper()}" if not col[0].startswith('POS_') else
        f"{col[0]}_{col[1].upper()}"
        for col in pos_agg.columns
    ])

    # 12. Regex Sanitization for Tree Algorithms
    pos_agg.columns = [re.sub(r'[^\w_]', '_', col) for col in pos_agg.columns]
    pos_agg.columns = [re.sub(r'_{2,}', '_', col) for col in pos_agg.columns]
    pos_agg.reset_index(inplace=True)

    # 13. Optional Parquet Export
    if output_parquet_path:
        os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
        pos_agg.to_parquet(output_parquet_path, compression='snappy', index=False)
        print(f"💾 Saved aggregated POS CASH data to: {output_parquet_path}")

    execution_time = time.time() - start_time
    print("=" * 75)
    print(f"✅ Pipeline Completed in {execution_time:.2f}s! Clients: {pos_agg.shape[0]:,} | Features: {pos_agg.shape[1]}")
    print("=" * 75)

    del df_pos
    gc.collect()
    return pos_agg

if __name__ == "__main__":
    RAW_PATH = "/Users/nguyenminhtri/FinalYearPro/data/raw/POS_CASH_balance.csv"
    OUTPUT_PATH = "/Users/nguyenminhtri/FinalYearPro/data/preprocess/pos_cash_clean_FE.parquet"
    process_pos_cash_pipeline(RAW_PATH, OUTPUT_PATH)