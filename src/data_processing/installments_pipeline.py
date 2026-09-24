import os
import gc
import re
import time
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

def process_installments_pipeline(raw_ins_path: str, output_parquet_path: str = None) -> pd.DataFrame:
    """Production ETL Pipeline for Installments Payments Data (13.6M+ records).
    Extracts behavioral payment dynamics, schedule modifications, delay/early offsets,
    monetary shortfalls, and aggregates records into client-level (SK_ID_CURR) profile.
    """
    start_time = time.time()
    print("=" * 75)
    print("🚀 EXECUTING INSTALLMENTS PAYMENTS PROCESSING PIPELINE")
    print("=" * 75)

    # 1. Load Raw Dataset
    if not os.path.exists(raw_ins_path):
        raise FileNotFoundError(f"Input file not found at: {raw_ins_path}")

    print(f"📖 Loading raw installments_payments from: {raw_ins_path}")
    df_ins = pd.read_csv(raw_ins_path)
    print(f"   • Loaded {len(df_ins):,} records across {df_ins.shape[1]} raw columns.")

    # 2. Process NUM_INSTALMENT_VERSION (Contract Modifications)
    df_ins['INS_IS_CREDIT_CARD'] = (df_ins['NUM_INSTALMENT_VERSION'] == 0.0).astype(int)
    df_ins['INS_IS_STANDARD_SCHEDULE'] = (df_ins['NUM_INSTALMENT_VERSION'] == 1.0).astype(int)
    df_ins['INS_IS_RESTRUCTURED'] = (df_ins['NUM_INSTALMENT_VERSION'] > 1.0).astype(int)

    # 3. Process NUM_INSTALMENT_NUMBER (Tenor Cycle Stages)
    df_ins['INS_IS_INITIAL_STAGE'] = (df_ins['NUM_INSTALMENT_NUMBER'] <= 6).astype(int)
    df_ins['INS_IS_MATURE_STAGE'] = (df_ins['NUM_INSTALMENT_NUMBER'] > 24).astype(int)

    # 4. Process DAYS_INSTALMENT (Standardized Monthly Windows)
    df_ins['INS_MONTHS_INSTALMENT'] = (df_ins['DAYS_INSTALMENT'] / 30.4375).astype(int)
    df_ins['INS_IS_RECENT_6M'] = (df_ins['DAYS_INSTALMENT'] >= -180).astype(int)
    df_ins['INS_IS_RECENT_12M'] = (df_ins['DAYS_INSTALMENT'] >= -365).astype(int)
    df_ins['INS_IS_RECENT_24M'] = (df_ins['DAYS_INSTALMENT'] >= -730).astype(int)

    # 5. Process DAYS_ENTRY_PAYMENT (Delay vs. Early Settlement Metrics)
    df_ins['INS_DAYS_ENTRY_PAYMENT_IS_NA'] = df_ins['DAYS_ENTRY_PAYMENT'].isna().astype(int)
    df_ins['INS_PAYMENT_DELAY'] = (df_ins['DAYS_ENTRY_PAYMENT'] - df_ins['DAYS_INSTALMENT']).clip(lower=0.0)
    df_ins['INS_PAYMENT_EARLY'] = (df_ins['DAYS_INSTALMENT'] - df_ins['DAYS_ENTRY_PAYMENT']).clip(lower=0.0)
    df_ins['INS_IS_PAYMENT_DELAYED'] = (df_ins['INS_PAYMENT_DELAY'] > 0.0).astype(int)
    df_ins['INS_IS_PAYMENT_EARLY'] = (df_ins['INS_PAYMENT_EARLY'] > 0.0).astype(int)

    # 6. Process AMT_PAYMENT & Monetary Shortfall Interactions
    df_ins['INS_AMT_PAYMENT_IS_NA'] = df_ins['AMT_PAYMENT'].isna().astype(int)
    df_ins['AMT_INSTALMENT'] = df_ins['AMT_INSTALMENT'].fillna(0.0)
    df_ins['AMT_PAYMENT'] = df_ins['AMT_PAYMENT'].fillna(0.0)

    df_ins['INS_AMT_INSTALMENT_IS_ZERO'] = (df_ins['AMT_INSTALMENT'] == 0.0).astype(int)
    df_ins['INS_AMT_PAYMENT_IS_ZERO'] = (df_ins['AMT_PAYMENT'] == 0.0).astype(int)

    # Positive = Underpaid (Shortfall), Negative = Overpaid
    df_ins['INS_PAYMENT_DIFF'] = df_ins['AMT_INSTALMENT'] - df_ins['AMT_PAYMENT']
    df_ins['INS_PAYMENT_RATIO'] = (df_ins['AMT_PAYMENT'] / (df_ins['AMT_INSTALMENT'] + 1e-5)).clip(lower=0.0, upper=5.0)

    df_ins['INS_IS_UNDERPAID'] = (df_ins['INS_PAYMENT_DIFF'] > 1.0).astype(int)
    df_ins['INS_IS_OVERPAID'] = (df_ins['INS_PAYMENT_DIFF'] < -1.0).astype(int)

    # 7. Explicit Aggregation Dictionary
    print("🔄 Grouping and aggregating records by SK_ID_CURR...")
    agg_dict = {
        'SK_ID_PREV': ['nunique'],
        'NUM_INSTALMENT_VERSION': ['nunique', 'max'],
        'NUM_INSTALMENT_NUMBER': ['max', 'mean'],
        'DAYS_INSTALMENT': ['min', 'max', 'mean'],
        'DAYS_ENTRY_PAYMENT': ['min', 'max', 'mean'],
        'AMT_INSTALMENT': ['min', 'max', 'mean', 'sum'],
        'AMT_PAYMENT': ['min', 'max', 'mean', 'sum'],
        'INS_PAYMENT_DELAY': ['max', 'mean', 'sum', 'var'],
        'INS_PAYMENT_EARLY': ['max', 'mean', 'sum'],
        'INS_IS_PAYMENT_DELAYED': ['mean', 'sum'],
        'INS_IS_PAYMENT_EARLY': ['mean', 'sum'],
        'INS_PAYMENT_DIFF': ['max', 'mean', 'sum', 'var'],
        'INS_PAYMENT_RATIO': ['min', 'max', 'mean'],
        'INS_IS_UNDERPAID': ['mean', 'sum'],
        'INS_IS_OVERPAID': ['mean', 'sum'],
        'INS_IS_CREDIT_CARD': ['mean'],
        'INS_IS_RESTRUCTURED': ['mean', 'sum'],
        'INS_IS_INITIAL_STAGE': ['mean'],
        'INS_IS_MATURE_STAGE': ['mean'],
        'INS_IS_RECENT_6M': ['mean', 'sum'],
        'INS_IS_RECENT_12M': ['mean', 'sum'],
        'INS_IS_RECENT_24M': ['mean', 'sum']
    }

    valid_agg_dict = {col: funcs for col, funcs in agg_dict.items() if col in df_ins.columns}
    ins_agg = df_ins.groupby('SK_ID_CURR').agg(valid_agg_dict)

    # 8. MultiIndex Flattening & Prefix Enforcement
    ins_agg.columns = pd.Index([
        'INS_COUNT_UNIQUE_LOANS' if col == ('SK_ID_PREV', 'nunique') else
        f"INS_{col[0]}_{col[1].upper()}" if not col[0].startswith('INS_') else
        f"{col[0]}_{col[1].upper()}"
        for col in ins_agg.columns
    ])

    # 9. Clean Column Headers with Regex (LightGBM/XGBoost JSON Safety)
    ins_agg.columns = [re.sub(r'[^\w_]', '_', col) for col in ins_agg.columns]
    ins_agg.columns = [re.sub(r'_{2,}', '_', col) for col in ins_agg.columns]
    ins_agg.reset_index(inplace=True)

    # 10. Optional Persistence
    if output_parquet_path:
        os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
        ins_agg.to_parquet(output_parquet_path, compression='snappy', index=False)
        print(f"💾 Saved aggregated installments data to: {output_parquet_path}")

    exec_time = time.time() - start_time
    print("=" * 75)
    print(f"✅ Pipeline Completed in {exec_time:.2f}s! Clients: {ins_agg.shape[0]:,} | Features: {ins_agg.shape[1]}")
    print("=" * 75)

    del df_ins
    gc.collect()
    return ins_agg

if __name__ == "__main__":
    RAW_PATH = "/Users/nguyenminhtri/FinalYearPro/data/raw/installments_payments.csv"
    OUTPUT_PATH = "/Users/nguyenminhtri/FinalYearPro/data/preprocess/installments_payments_clean_FE.parquet"
    process_installments_pipeline(RAW_PATH, OUTPUT_PATH)