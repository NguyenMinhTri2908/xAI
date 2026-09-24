import os
import gc
import re
import time
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


def process_credit_card_pipeline(raw_cc_path: str, output_parquet_path: str = None) -> pd.DataFrame:
    """Production ETL Pipeline for Credit Card Monthly Balance Data (3.8M+ records).
    Computes revolving credit utilization, ATM vs POS drawing dynamics, minimum payment
    shortfalls, fee/interest burdens, and aggregates features into client-level (SK_ID_CURR) profile.
    """
    start_time = time.time()
    print("=" * 75)
    print("🚀 EXECUTING CREDIT CARD BALANCE PROCESSING PIPELINE")
    print("=" * 75)

    # 1. Load Raw Dataset
    if not os.path.exists(raw_cc_path):
        raise FileNotFoundError(f"Input file not found at: {raw_cc_path}")

    print(f"📖 Loading raw credit_card_balance from: {raw_cc_path}")
    df_cc = pd.read_csv(raw_cc_path)
    print(f"   • Loaded {len(df_cc):,} records across {df_cc.shape[1]} raw columns.")

    # 2. Process MONTHS_BALANCE (Recency Windows)
    df_cc['CC_IS_RECENT_6M'] = (df_cc['MONTHS_BALANCE'] >= -6).astype(int)
    df_cc['CC_IS_RECENT_12M'] = (df_cc['MONTHS_BALANCE'] >= -12).astype(int)
    df_cc['CC_IS_RECENT_24M'] = (df_cc['MONTHS_BALANCE'] >= -24).astype(int)

    # 3. Process AMT_BALANCE
    df_cc['AMT_BALANCE'] = df_cc['AMT_BALANCE'].fillna(0.0)
    df_cc['CC_AMT_BALANCE_IS_ZERO'] = (df_cc['AMT_BALANCE'] == 0.0).astype(int)
    df_cc['CC_AMT_BALANCE_IS_NEGATIVE'] = (df_cc['AMT_BALANCE'] < 0.0).astype(int)
    df_cc['CC_AMT_BALANCE_POS'] = df_cc['AMT_BALANCE'].clip(lower=0.0)

    # 4. Process AMT_CREDIT_LIMIT_ACTUAL & Utilization Ratios
    df_cc['AMT_CREDIT_LIMIT_ACTUAL'] = df_cc['AMT_CREDIT_LIMIT_ACTUAL'].fillna(0.0)
    df_cc['CC_IS_ZERO_LIMIT'] = (df_cc['AMT_CREDIT_LIMIT_ACTUAL'] == 0.0).astype(int)
    df_cc['CC_AMT_LIMIT_POS'] = df_cc['AMT_CREDIT_LIMIT_ACTUAL'].clip(lower=0.0)

    df_cc['CC_LIMIT_UTILIZATION'] = (
            df_cc['CC_AMT_BALANCE_POS'] / (df_cc['AMT_CREDIT_LIMIT_ACTUAL'] + 1e-5)
    ).clip(lower=0.0, upper=3.0)

    df_cc['CC_IS_OVERLIMIT'] = (
            (df_cc['AMT_BALANCE'] > df_cc['AMT_CREDIT_LIMIT_ACTUAL']) &
            (df_cc['AMT_CREDIT_LIMIT_ACTUAL'] > 0.0)
    ).astype(int)
    df_cc['CC_OVERLIMIT_AMT'] = (df_cc['AMT_BALANCE'] - df_cc['AMT_CREDIT_LIMIT_ACTUAL']).clip(lower=0.0)
    df_cc['CC_IS_HIGH_UTILIZATION'] = (df_cc['CC_LIMIT_UTILIZATION'] >= 0.8).astype(int)

    # 5. Process Drawings (ATM vs. Total Drawings)
    df_cc['CC_AMT_DRAWINGS_ATM_IS_NA'] = df_cc['AMT_DRAWINGS_ATM_CURRENT'].isna().astype(int)
    df_cc['AMT_DRAWINGS_ATM_CURRENT'] = df_cc['AMT_DRAWINGS_ATM_CURRENT'].fillna(0.0)
    df_cc['AMT_DRAWINGS_CURRENT'] = df_cc['AMT_DRAWINGS_CURRENT'].fillna(0.0)

    df_cc['CC_IS_DRAWING_ATM'] = (df_cc['AMT_DRAWINGS_ATM_CURRENT'] > 0.0).astype(int)
    df_cc['CC_IS_DRAWING_ANY'] = (df_cc['AMT_DRAWINGS_CURRENT'] > 0.0).astype(int)

    df_cc['CC_DRAWING_ATM_RATIO'] = (
            df_cc['AMT_DRAWINGS_ATM_CURRENT'] / (df_cc['AMT_DRAWINGS_CURRENT'] + 1e-5)
    ).clip(lower=0.0, upper=1.0)

    df_cc['CC_AMT_DRAWINGS_POS_EST'] = (df_cc['AMT_DRAWINGS_CURRENT'] - df_cc['AMT_DRAWINGS_ATM_CURRENT']).clip(
        lower=0.0)
    df_cc['CC_DRAWING_TO_BALANCE_RATIO'] = (
            df_cc['AMT_DRAWINGS_CURRENT'] / (df_cc['CC_AMT_BALANCE_POS'] + 1e-5)
    ).clip(lower=0.0, upper=3.0)

    # 6. Process POS Specific Drawings
    df_cc['CC_AMT_DRAWINGS_POS_IS_NA'] = df_cc['AMT_DRAWINGS_POS_CURRENT'].isna().astype(int)
    df_cc['AMT_DRAWINGS_POS_CURRENT'] = df_cc['AMT_DRAWINGS_POS_CURRENT'].fillna(0.0)
    df_cc['CC_IS_DRAWING_POS'] = (df_cc['AMT_DRAWINGS_POS_CURRENT'] > 0.0).astype(int)

    # 7. Process AMT_INST_MIN_REGULARITY & Shortfalls
    df_cc['CC_AMT_INST_MIN_IS_NA'] = df_cc['AMT_INST_MIN_REGULARITY'].isna().astype(int)
    df_cc['AMT_INST_MIN_REGULARITY'] = df_cc['AMT_INST_MIN_REGULARITY'].fillna(0.0)
    df_cc['CC_IS_MIN_PAYMENT_REQUIRED'] = (df_cc['AMT_INST_MIN_REGULARITY'] > 0.0).astype(int)

    df_cc['CC_AMT_PAYMENT_IS_NA'] = df_cc['AMT_PAYMENT_CURRENT'].isna().astype(int)
    df_cc['AMT_PAYMENT_CURRENT'] = df_cc['AMT_PAYMENT_CURRENT'].fillna(0.0)

    df_cc['CC_PAYMENT_MIN_DIFF'] = df_cc['AMT_INST_MIN_REGULARITY'] - df_cc['AMT_PAYMENT_CURRENT']
    df_cc['CC_IS_UNDERPAID_MIN'] = (df_cc['CC_PAYMENT_MIN_DIFF'] > 1.0).astype(int)
    df_cc['CC_PAYMENT_RATIO_MIN'] = (
            df_cc['AMT_PAYMENT_CURRENT'] / (df_cc['AMT_INST_MIN_REGULARITY'] + 1e-5)
    ).clip(lower=0.0, upper=5.0)

    # 8. Process Total Payment Inflows & Full Payer Status
    df_cc['AMT_PAYMENT_TOTAL_CURRENT'] = df_cc['AMT_PAYMENT_TOTAL_CURRENT'].fillna(0.0)
    df_cc['CC_IS_PAYMENT_TOTAL_POS'] = (df_cc['AMT_PAYMENT_TOTAL_CURRENT'] > 0.0).astype(int)
    df_cc['CC_PAYMENT_TO_BALANCE_RATIO'] = (
            df_cc['AMT_PAYMENT_TOTAL_CURRENT'] / (df_cc['CC_AMT_BALANCE_POS'] + 1e-5)
    ).clip(lower=0.0, upper=3.0)

    df_cc['CC_IS_FULL_PAYER'] = (
            (df_cc['CC_PAYMENT_TO_BALANCE_RATIO'] >= 0.99) &
            (df_cc['CC_AMT_BALANCE_POS'] > 0.0)
    ).astype(int)

    # 9. Process Principal Debt Structure & Non-Principal Fees
    df_cc['AMT_RECEIVABLE_PRINCIPAL'] = df_cc['AMT_RECEIVABLE_PRINCIPAL'].fillna(0.0)
    df_cc['CC_AMT_PRINCIPAL_POS'] = df_cc['AMT_RECEIVABLE_PRINCIPAL'].clip(lower=0.0)
    df_cc['CC_PRINCIPAL_TO_BALANCE_RATIO'] = (
            df_cc['CC_AMT_PRINCIPAL_POS'] / (df_cc['CC_AMT_BALANCE_POS'] + 1e-5)
    ).clip(lower=0.0, upper=1.0)
    df_cc['CC_NON_PRINCIPAL_AMT'] = (df_cc['CC_AMT_BALANCE_POS'] - df_cc['CC_AMT_PRINCIPAL_POS']).clip(lower=0.0)

    # 10. Process Drawing Counts & Ticket Sizes
    df_cc['CNT_DRAWINGS_ATM_CURRENT'] = df_cc['CNT_DRAWINGS_ATM_CURRENT'].fillna(0.0)
    df_cc['CC_AVG_AMT_PER_ATM_DRAWING'] = df_cc['AMT_DRAWINGS_ATM_CURRENT'] / (df_cc['CNT_DRAWINGS_ATM_CURRENT'] + 1e-5)
    df_cc['CC_IS_HIGH_ATM_FREQ'] = (df_cc['CNT_DRAWINGS_ATM_CURRENT'] >= 3.0).astype(int)

    df_cc['CNT_DRAWINGS_CURRENT'] = df_cc['CNT_DRAWINGS_CURRENT'].fillna(0.0)
    df_cc['CC_AVG_AMT_PER_DRAWING'] = df_cc['AMT_DRAWINGS_CURRENT'] / (df_cc['CNT_DRAWINGS_CURRENT'] + 1e-5)
    df_cc['CC_DRAWING_ATM_CNT_RATIO'] = (
            df_cc['CNT_DRAWINGS_ATM_CURRENT'] / (df_cc['CNT_DRAWINGS_CURRENT'] + 1e-5)
    ).clip(lower=0.0, upper=1.0)
    df_cc['CC_IS_FREQUENT_USER'] = (df_cc['CNT_DRAWINGS_CURRENT'] >= 5.0).astype(int)

    df_cc['CNT_DRAWINGS_POS_CURRENT'] = df_cc['CNT_DRAWINGS_POS_CURRENT'].fillna(0.0)
    df_cc['CC_AVG_AMT_PER_POS_DRAWING'] = df_cc['AMT_DRAWINGS_POS_CURRENT'] / (df_cc['CNT_DRAWINGS_POS_CURRENT'] + 1e-5)
    df_cc['CC_DRAWING_POS_CNT_RATIO'] = (
            df_cc['CNT_DRAWINGS_POS_CURRENT'] / (df_cc['CNT_DRAWINGS_CURRENT'] + 1e-5)
    ).clip(lower=0.0, upper=1.0)

    # 11. Process Mature Installments & Status Indicators
    df_cc['CC_CNT_INSTALMENT_MATURE_IS_NA'] = df_cc['CNT_INSTALMENT_MATURE_CUM'].isna().astype(int)
    df_cc['CNT_INSTALMENT_MATURE_CUM'] = df_cc['CNT_INSTALMENT_MATURE_CUM'].fillna(0.0)
    df_cc['CC_IS_MATURE_ACCOUNT'] = (df_cc['CNT_INSTALMENT_MATURE_CUM'] >= 6.0).astype(int)

    df_cc['CC_STATUS_IS_ACTIVE'] = (df_cc['NAME_CONTRACT_STATUS'] == 'Active').astype(int)
    df_cc['CC_STATUS_IS_COMPLETED'] = (df_cc['NAME_CONTRACT_STATUS'] == 'Completed').astype(int)

    # 12. Process DPD Delinquency
    df_cc['SK_DPD'] = df_cc['SK_DPD'].fillna(0.0)
    df_cc['CC_IS_DPD'] = (df_cc['SK_DPD'] > 0.0).astype(int)
    df_cc['CC_IS_DPD_30'] = (df_cc['SK_DPD'] >= 30.0).astype(int)
    df_cc['CC_IS_DPD_90'] = (df_cc['SK_DPD'] >= 90.0).astype(int)

    df_cc['SK_DPD_DEF'] = df_cc['SK_DPD_DEF'].fillna(0.0)
    df_cc['CC_IS_DPD_DEF'] = (df_cc['SK_DPD_DEF'] > 0.0).astype(int)
    df_cc['CC_DPD_TOLERANCE_DAYS'] = (df_cc['SK_DPD'] - df_cc['SK_DPD_DEF']).clip(lower=0.0)

    # Alias for consistent aggregation matching notebook
    df_cc['CC_IS_ZERO_BALANCE'] = df_cc['CC_AMT_BALANCE_IS_ZERO']
    df_cc['CC_ZERO_BALANCE'] = df_cc['CC_AMT_BALANCE_IS_ZERO']

    # 13. GroupBy Aggregation Dictionary per SK_ID_CURR
    print("🔄 Grouping and aggregating credit card statements by SK_ID_CURR...")
    cc_agg_candidate = {
        'MONTHS_BALANCE': ['min', 'max', 'size'],
        'AMT_CREDIT_LIMIT_ACTUAL': ['mean', 'max', 'last'],
        'CC_AMT_LIMIT_POS': ['mean', 'max', 'last'],
        'CC_LIMIT_UTILIZATION': ['mean', 'max', 'last'],
        'CC_IS_OVERLIMIT': ['mean', 'sum', 'max'],
        'CC_OVERLIMIT_AMT': ['mean', 'max', 'sum'],
        'AMT_BALANCE': ['mean', 'max', 'last', 'std'],
        'CC_AMT_BALANCE_POS': ['mean', 'max', 'last'],
        'CC_IS_ZERO_BALANCE': ['mean', 'sum'],
        'CC_ZERO_BALANCE': ['mean', 'sum'],
        'AMT_DRAWINGS_CURRENT': ['mean', 'max', 'sum'],
        'AMT_DRAWINGS_ATM_CURRENT': ['mean', 'max', 'sum'],
        'AMT_DRAWINGS_POS_CURRENT': ['mean', 'max', 'sum'],
        'AMT_DRAWINGS_OTHER_CURRENT': ['mean', 'max', 'sum'],
        'CC_IS_DRAWING_POS': ['mean', 'sum'],
        'CC_IS_DRAWING_ATM': ['mean', 'sum'],
        'CC_DRAWING_ATM_RATIO': ['mean', 'max'],
        'CC_DRAWING_TO_BALANCE_RATIO': ['mean', 'max'],
        'AMT_INST_MIN_REGULARITY': ['mean', 'max', 'last'],
        'CC_IS_MIN_PAYMENT_REQUIRED': ['mean', 'sum'],
        'AMT_PAYMENT_CURRENT': ['mean', 'max', 'sum'],
        'CC_PAYMENT_MIN_DIFF': ['mean', 'max', 'sum'],
        'CC_IS_UNDERPAID_MIN': ['mean', 'sum', 'max'],
        'CC_PAYMENT_RATIO_MIN': ['mean', 'min', 'last'],
        'AMT_PAYMENT_TOTAL_CURRENT': ['mean', 'max', 'sum'],
        'CC_IS_PAYMENT_TOTAL_POS': ['mean', 'sum'],
        'CC_PAYMENT_TO_BALANCE_RATIO': ['mean', 'max', 'last'],
        'CC_IS_FULL_PAYER': ['mean', 'sum', 'last'],
        'AMT_RECEIVABLE_PRINCIPAL': ['mean', 'max', 'last'],
        'CC_PRINCIPAL_TO_BALANCE_RATIO': ['mean', 'min', 'last'],
        'CC_NON_PRINCIPAL_AMT': ['mean', 'max', 'sum'],
        'AMT_RECIVABLE': ['mean', 'max', 'last'],
        'AMT_TOTAL_RECEIVABLE': ['mean', 'max', 'last'],
        'CNT_DRAWINGS_CURRENT': ['mean', 'max', 'sum'],
        'CNT_DRAWINGS_ATM_CURRENT': ['mean', 'max', 'sum'],
        'CNT_DRAWINGS_POS_CURRENT': ['mean', 'max', 'sum'],
        'CNT_DRAWINGS_OTHER_CURRENT': ['mean', 'max', 'sum'],
        'CC_AVG_AMT_PER_ATM_DRAWING': ['mean', 'max'],
        'CC_IS_HIGH_ATM_FREQ': ['mean', 'sum'],
        'CC_AVG_AMT_PER_DRAWING': ['mean', 'max'],
        'CC_DRAWING_ATM_CNT_RATIO': ['mean', 'max'],
        'CC_IS_FREQUENT_USER': ['mean', 'sum'],
        'CC_AVG_AMT_PER_POS_DRAWING': ['mean', 'max'],
        'CC_DRAWING_POS_CNT_RATIO': ['mean', 'max'],
        'CNT_INSTALMENT_MATURE_CUM': ['max', 'last'],
        'CC_IS_MATURE_ACCOUNT': ['mean', 'last'],
        'CC_STATUS_IS_ACTIVE': ['mean', 'last'],
        'CC_STATUS_IS_COMPLETED': ['mean', 'last'],
        'SK_DPD': ['mean', 'max', 'std'],
        'CC_IS_DPD': ['mean', 'sum', 'max'],
        'CC_IS_DPD_30': ['mean', 'sum', 'max'],
        'CC_IS_DPD_90': ['mean', 'sum', 'max'],
        'SK_DPD_DEF': ['mean', 'max', 'std'],
        'CC_IS_DPD_DEF': ['mean', 'sum', 'max'],
        'CC_DPD_TOLERANCE_DAYS': ['mean', 'max'],
        'CC_AMT_DRAWINGS_ATM_IS_NA': ['mean', 'sum'],
        'CC_AMT_DRAWINGS_POS_IS_NA': ['mean', 'sum'],
        'CC_AMT_INST_MIN_IS_NA': ['mean', 'sum'],
        'CC_AMT_PAYMENT_IS_NA': ['mean', 'sum'],
        'CC_CNT_INSTALMENT_MATURE_IS_NA': ['mean', 'sum']
    }

    cc_agg_safe = {col: agg_list for col, agg_list in cc_agg_candidate.items() if col in df_cc.columns}
    df_cc_agg = df_cc.groupby('SK_ID_CURR').agg(cc_agg_safe)

    # 14. Flatten MultiIndex and Enforce Clean CC_ Prefix
    df_cc_agg.columns = [f"CC_{col}_{fn.upper()}" for col, fn in df_cc_agg.columns]

    # Clean double prefixes and regex sanitize for LightGBM/XGBoost
    cleaned_cols = []
    for col in df_cc_agg.columns:
        clean = col.replace('CC_CC_', 'CC_')
        if not clean.startswith('CC_'):
            clean = f"CC_{clean}"
        clean = re.sub(r'[^\w_]', '_', clean)
        clean = re.sub(r'_{2,}', '_', clean)
        cleaned_cols.append(clean)

    df_cc_agg.columns = cleaned_cols
    df_cc_agg.reset_index(inplace=True)

    # 15. Optional Parquet Export
    if output_parquet_path:
        os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
        df_cc_agg.to_parquet(output_parquet_path, compression='snappy', index=False)
        print(f"💾 Saved aggregated credit card data to: {output_parquet_path}")

    exec_time = time.time() - start_time
    print("=" * 75)
    print(f"✅ Pipeline Completed in {exec_time:.2f}s! Clients: {df_cc_agg.shape[0]:,} | Features: {df_cc_agg.shape[1]}")
    print("=" * 75)

    del df_cc
    gc.collect()
    return df_cc_agg


if __name__ == "__main__":
    RAW_PATH = "/Users/nguyenminhtri/FinalYearPro/data/raw/credit_card_balance.csv"
    OUTPUT_PATH = "/Users/nguyenminhtri/FinalYearPro/data/preprocess/table/credit_card_balance_aggregated.parquet"
    process_credit_card_pipeline(RAW_PATH, OUTPUT_PATH)