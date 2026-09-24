import os
import gc
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

def process_bureau_balance_pipeline(raw_bb_path: str, output_parquet_path: str = None) -> pd.DataFrame:
    """Production ETL Pipeline for Credit Bureau Monthly Balance Data (27.3M records).
    Encodes payment status, constructs ordinal severity metrics, extracts time-series
    dynamics, and aggregates records to the loan level (SK_ID_BUREAU).
    """
    print("=" * 70)
    print("🚀 EXECUTING BUREAU BALANCE PROCESSING PIPELINE")
    print("=" * 70)

    # 1. Load Raw Dataset
    if not os.path.exists(raw_bb_path):
        raise FileNotFoundError(f"Input file not found at: {raw_bb_path}")

    print(f"📖 Loading raw bureau balance from: {raw_bb_path}")
    df_bb = pd.read_csv(raw_bb_path)
    print(f"   • Loaded {len(df_bb):,} records across {df_bb.shape[1]} raw columns.")

    # 2. Row-Level Feature Engineering (Memory Optimized int8)
    print("⚙️ Executing row-level encodings and risk bucket flags...")
    status_dummies = pd.get_dummies(df_bb['STATUS'], prefix='BB_STATUS').astype(np.int8)
    df_bb = pd.concat([df_bb, status_dummies], axis=1)

    df_bb['BB_IS_OVERDUE'] = df_bb['STATUS'].isin(['0', '1', '2', '3', '4', '5']).astype(np.int8)
    df_bb['BB_IS_DPD_30PLUS'] = df_bb['STATUS'].isin(['1', '2', '3', '4', '5']).astype(np.int8)
    df_bb['BB_IS_NPL_90PLUS'] = df_bb['STATUS'].isin(['3', '4', '5']).astype(np.int8)

    df_bb['BB_IN_RECENT_6M'] = (df_bb['MONTHS_BALANCE'] >= -6).astype(np.int8)
    df_bb['BB_IN_RECENT_12M'] = (df_bb['MONTHS_BALANCE'] >= -12).astype(np.int8)
    df_bb['BB_IN_RECENT_24M'] = (df_bb['MONTHS_BALANCE'] >= -24).astype(np.int8)

    # 3. Advanced Time-Series Severity Mapping & Recency Tracking
    print("⚡ Mapping ordinal risk severity and tracking delinquency points...")
    severity_map = {'C': 0, 'X': 0, '0': 1, '1': 2, '2': 3, '3': 4, '4': 5, '5': 6}
    df_bb['BB_SEVERITY_SCORE'] = df_bb['STATUS'].map(severity_map).fillna(0).astype(np.int8)
    df_bb['BB_OVERDUE_MONTHS_BALANCE'] = np.where(df_bb['BB_IS_OVERDUE'] == 1, df_bb['MONTHS_BALANCE'], np.nan)

    # 4. Aggregation Level 1 (SK_ID_BUREAU)
    print("🔄 Grouping 27.3M records by SK_ID_BUREAU...")
    bb_agg_dict = {
        'MONTHS_BALANCE': ['min', 'size'],
        'BB_SEVERITY_SCORE': ['max', 'mean'],
        'BB_OVERDUE_MONTHS_BALANCE': ['max'],
        'BB_STATUS_0': ['sum', 'mean'],
        'BB_STATUS_1': ['sum', 'mean'],
        'BB_STATUS_2': ['sum', 'mean'],
        'BB_STATUS_3': ['sum', 'mean'],
        'BB_STATUS_4': ['sum', 'mean'],
        'BB_STATUS_5': ['sum', 'mean'],
        'BB_STATUS_C': ['sum', 'mean'],
        'BB_STATUS_X': ['sum', 'mean'],
        'BB_IS_OVERDUE': ['sum', 'mean'],
        'BB_IS_DPD_30PLUS': ['sum', 'mean'],
        'BB_IS_NPL_90PLUS': ['sum', 'mean'],
        'BB_IN_RECENT_6M': ['sum'],
        'BB_IN_RECENT_12M': ['sum'],
        'BB_IN_RECENT_24M': ['sum']
    }

    valid_bb_aggs = {col: aggs for col, aggs in bb_agg_dict.items() if col in df_bb.columns}
    df_bb_agg = df_bb.groupby('SK_ID_BUREAU').agg(valid_bb_aggs)
    df_bb_agg.columns = [f"{col}_{stat.upper()}" for col, stat in df_bb_agg.columns]
    df_bb_agg.reset_index(inplace=True)

    # 5. Advanced Trend & Recency Metrics
    print("📐 Computing time-series momentum and recency distance...")
    df_bb_agg['BB_MONTHS_SINCE_LAST_OVERDUE'] = df_bb_agg['BB_OVERDUE_MONTHS_BALANCE_MAX'].abs()
    df_bb_agg.drop(columns=['BB_OVERDUE_MONTHS_BALANCE_MAX'], inplace=True)

    if 'BB_IS_OVERDUE_SUM' in df_bb_agg.columns:
        recent_6m_overdue = (
            df_bb[df_bb['MONTHS_BALANCE'] >= -6]
            .groupby('SK_ID_BUREAU')['BB_IS_OVERDUE']
            .sum()
            .reset_index()
        )
        recent_6m_overdue.columns = ['SK_ID_BUREAU', 'BB_OVERDUE_SUM_RECENT_6M']

        df_bb_agg = df_bb_agg.merge(recent_6m_overdue, on='SK_ID_BUREAU', how='left')
        df_bb_agg['BB_OVERDUE_SUM_RECENT_6M'] = df_bb_agg['BB_OVERDUE_SUM_RECENT_6M'].fillna(0)

        df_bb_agg['BB_OVERDUE_TREND_RATIO_6M'] = (
            df_bb_agg['BB_OVERDUE_SUM_RECENT_6M'] / (df_bb_agg['BB_IS_OVERDUE_SUM'] + 1e-5)
        )

    # 6. Optional Persistence & Cleanup
    if output_parquet_path:
        os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
        df_bb_agg.to_parquet(output_parquet_path, index=False)
        print(f"💾 Saved loan-level bureau balance data to: {output_parquet_path}")

    print(f"✅ Finished Bureau Balance Pipeline. Final shape: {df_bb_agg.shape[0]:,} loans | {df_bb_agg.shape[1]} features.")

    del df_bb
    gc.collect()
    return df_bb_agg

if __name__ == "__main__":
    RAW_PATH = "/Users/nguyenminhtri/FinalYearPro/data/raw/bureau_balance.csv"
    OUTPUT_PATH = "/Users/nguyenminhtri/FinalYearPro/data/preprocess/df_bureau_balance_clean_fe.parquet"
    process_bureau_balance_pipeline(RAW_PATH, OUTPUT_PATH)