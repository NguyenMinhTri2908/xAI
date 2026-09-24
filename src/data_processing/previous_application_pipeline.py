import os
import gc
import re
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

def process_previous_application_pipeline(raw_prev_path: str, output_parquet_path: str = None) -> pd.DataFrame:
    """Production ETL Pipeline for Previous Applications (Home Credit Historical Contracts).
    Removes noisy metadata, rectifies temporal anomalies (365243 placeholders),
    engineers contract approval/downsizing ratios, and performs aggregated flattening per SK_ID_CURR.
    """
    print("=" * 70)
    print("🚀 EXECUTING PREVIOUS APPLICATION PROCESSING PIPELINE")
    print("=" * 70)

    # 1. Load Raw Dataset
    if not os.path.exists(raw_prev_path):
        raise FileNotFoundError(f"Input file not found at: {raw_prev_path}")

    print(f"📖 Loading raw previous application dataset from: {raw_prev_path}")
    df_prev = pd.read_csv(raw_prev_path)
    print(f"   • Loaded {len(df_prev):,} records across {df_prev.shape[1]} raw columns.")

    # 2. Drop Noisy & Low-Importance Metadata Columns
    cols_to_drop = [
        'WEEKDAY_APPR_PROCESS_START', 'HOUR_APPR_PROCESS_START',
        'FLAG_LAST_APPL_PER_CONTRACT', 'NFLAG_LAST_APPL_IN_DAY',
        'NFLAG_MICRO_CASH', 'NAME_CASH_LOAN_PURPOSE',
        'NAME_PAYMENT_TYPE', 'CODE_REJECT_REASON',
        'NAME_TYPE_SUITE', 'NAME_CLIENT_TYPE',
        'NAME_GOODS_CATEGORY', 'NAME_PORTFOLIO',
        'NAME_PRODUCT_TYPE', 'CHANNEL_TYPE',
        'SELLERPLACE_AREA', 'NAME_SELLER_INDUSTRY',
        'NAME_YIELD_GROUP', 'PRODUCT_COMBINATION',
        'NFLAG_INSURED_ON_APPROVAL'
    ]
    existing_drops = [col for col in cols_to_drop if col in df_prev.columns]
    df_prev.drop(columns=existing_drops, inplace=True, errors='ignore')
    print(f"   • Dropped {len(existing_drops)} uninformative columns.")

    # 3. Process AMT_ANNUITY
    df_prev['PREV_ANNUITY_IS_NA'] = df_prev['AMT_ANNUITY'].isna().astype(int)
    annuity_cap = df_prev['AMT_ANNUITY'].quantile(0.999)
    df_prev['AMT_ANNUITY_CLEAN'] = df_prev['AMT_ANNUITY'].clip(upper=annuity_cap).fillna(0.0)
    if 'AMT_CREDIT' in df_prev.columns:
        df_prev['PREV_ANNUITY_TO_CREDIT'] = df_prev['AMT_ANNUITY_CLEAN'] / (df_prev['AMT_CREDIT'] + 1e-5)

    # 4. Process AMT_APPLICATION
    df_prev['PREV_APP_IS_ZERO'] = (df_prev['AMT_APPLICATION'] == 0.0).astype(int)
    app_cap = df_prev['AMT_APPLICATION'].quantile(0.999)
    df_prev['AMT_APPLICATION_CLEAN'] = df_prev['AMT_APPLICATION'].clip(upper=app_cap)
    if 'AMT_CREDIT' in df_prev.columns:
        df_prev['PREV_APP_CREDIT_PERC'] = df_prev['AMT_APPLICATION_CLEAN'] / (df_prev['AMT_CREDIT'] + 1e-5)
        df_prev['PREV_APP_CREDIT_DIFF'] = df_prev['AMT_APPLICATION_CLEAN'] - df_prev['AMT_CREDIT']
        df_prev['PREV_IS_DOWNSIZED'] = (df_prev['PREV_APP_CREDIT_DIFF'] > 0).astype(int)

    # 5. Process AMT_CREDIT
    df_prev['PREV_CREDIT_IS_ZERO'] = (df_prev['AMT_CREDIT'] == 0.0).astype(int)
    credit_cap = df_prev['AMT_CREDIT'].quantile(0.999)
    df_prev['AMT_CREDIT_CLEAN'] = df_prev['AMT_CREDIT'].clip(upper=credit_cap)

    # 6. Process AMT_DOWN_PAYMENT
    df_prev['PREV_DOWN_PAYMENT_IS_NA'] = df_prev['AMT_DOWN_PAYMENT'].isna().astype(int)
    dp_cap = df_prev['AMT_DOWN_PAYMENT'].quantile(0.999)
    df_prev['AMT_DOWN_PAYMENT_CLEAN'] = df_prev['AMT_DOWN_PAYMENT'].clip(lower=0.0, upper=dp_cap).fillna(0.0)
    df_prev['PREV_HAS_DOWN_PAYMENT'] = (df_prev['AMT_DOWN_PAYMENT_CLEAN'] > 0.0).astype(int)
    if 'AMT_CREDIT' in df_prev.columns:
        df_prev['PREV_DOWN_PAYMENT_TO_CREDIT'] = df_prev['AMT_DOWN_PAYMENT_CLEAN'] / (df_prev['AMT_CREDIT'] + 1e-5)

    # 7. Process AMT_GOODS_PRICE
    df_prev['PREV_GOODS_PRICE_IS_NA'] = df_prev['AMT_GOODS_PRICE'].isna().astype(int)
    gp_cap = df_prev['AMT_GOODS_PRICE'].quantile(0.999)
    df_prev['AMT_GOODS_PRICE_CLEAN'] = df_prev['AMT_GOODS_PRICE'].clip(upper=gp_cap)
    if 'AMT_CREDIT' in df_prev.columns:
        df_prev['AMT_GOODS_PRICE_CLEAN'] = df_prev['AMT_GOODS_PRICE_CLEAN'].fillna(df_prev['AMT_CREDIT'])
        df_prev['PREV_GOODS_CREDIT_RATIO'] = df_prev['AMT_CREDIT'] / (df_prev['AMT_GOODS_PRICE_CLEAN'] + 1e-5)
    else:
        df_prev['AMT_GOODS_PRICE_CLEAN'] = df_prev['AMT_GOODS_PRICE_CLEAN'].fillna(0.0)

    # 8. Process RATE_DOWN_PAYMENT
    df_prev['PREV_RATE_DOWN_PAYMENT_IS_NA'] = df_prev['RATE_DOWN_PAYMENT'].isna().astype(int)
    df_prev['RATE_DOWN_PAYMENT_CLEAN'] = df_prev['RATE_DOWN_PAYMENT'].clip(lower=0.0, upper=1.0).fillna(0.0)

    # 9. Process Extreme Missing Rate Features
    df_prev['PREV_RATE_INTEREST_PRIMARY_IS_NA'] = df_prev['RATE_INTEREST_PRIMARY'].isna().astype(int)
    df_prev.drop(columns=['RATE_INTEREST_PRIMARY'], inplace=True, errors='ignore')

    df_prev['PREV_RATE_INTEREST_PRIVILEGED_IS_NA'] = df_prev['RATE_INTEREST_PRIVILEGED'].isna().astype(int)
    df_prev.drop(columns=['RATE_INTEREST_PRIVILEGED'], inplace=True, errors='ignore')

    # 10. Process NAME_CONTRACT_STATUS
    df_prev['PREV_IS_APPROVED'] = (df_prev['NAME_CONTRACT_STATUS'] == 'Approved').astype(int)
    df_prev['PREV_IS_CANCELED'] = (df_prev['NAME_CONTRACT_STATUS'] == 'Canceled').astype(int)
    df_prev['PREV_IS_REFUSED'] = (df_prev['NAME_CONTRACT_STATUS'] == 'Refused').astype(int)
    df_prev['PREV_IS_UNUSED'] = (df_prev['NAME_CONTRACT_STATUS'] == 'Unused offer').astype(int)

    # 11. Process DAYS_DECISION
    df_prev['PREV_DECISION_YEARS'] = df_prev['DAYS_DECISION'].abs() / 365.25
    df_prev['PREV_IS_RECENT_1Y'] = (df_prev['DAYS_DECISION'] >= -365).astype(int)
    df_prev['PREV_IS_RECENT_2Y'] = (df_prev['DAYS_DECISION'] >= -730).astype(int)

    # 12. Process CNT_PAYMENT
    df_prev['PREV_CNT_PAYMENT_IS_NA'] = df_prev['CNT_PAYMENT'].isna().astype(int)
    df_prev['CNT_PAYMENT_CLEAN'] = df_prev['CNT_PAYMENT'].fillna(0.0)
    df_prev['PREV_IS_SHORT_TERM'] = ((df_prev['CNT_PAYMENT_CLEAN'] > 0.0) & (df_prev['CNT_PAYMENT_CLEAN'] <= 12.0)).astype(int)
    if 'AMT_ANNUITY_CLEAN' in df_prev.columns:
        df_prev['PREV_TOTAL_CONTRACT_VAL'] = df_prev['AMT_ANNUITY_CLEAN'] * df_prev['CNT_PAYMENT_CLEAN']

    # 13. Process DAYS Time Anomalies (Replace 365243 with NaN)
    temporal_anom_cols = [
        'DAYS_FIRST_DRAWING', 'DAYS_FIRST_DUE',
        'DAYS_LAST_DUE_1ST_VERSION', 'DAYS_LAST_DUE', 'DAYS_TERMINATION'
    ]
    for c in temporal_anom_cols:
        if c in df_prev.columns:
            df_prev[c] = df_prev[c].replace(365243, np.nan)

    # Temporal feature derivations
    df_prev['PREV_FIRST_DRAWING_IS_NA'] = df_prev['DAYS_FIRST_DRAWING'].isna().astype(int)
    df_prev['PREV_FIRST_DRAWING_YEARS'] = df_prev['DAYS_FIRST_DRAWING'].abs() / 365.25

    df_prev['PREV_FIRST_DUE_IS_NA'] = df_prev['DAYS_FIRST_DUE'].isna().astype(int)
    df_prev['PREV_FIRST_DUE_YEARS'] = df_prev['DAYS_FIRST_DUE'].abs() / 365.25
    if 'DAYS_FIRST_DRAWING' in df_prev.columns:
        df_prev['PREV_DAYS_DRAWING_TO_DUE'] = df_prev['DAYS_FIRST_DUE'] - df_prev['DAYS_FIRST_DRAWING']

    df_prev['PREV_LAST_DUE_1ST_VERSION_IS_NA'] = df_prev['DAYS_LAST_DUE_1ST_VERSION'].isna().astype(int)
    df_prev['PREV_LAST_DUE_1ST_VERSION_YEARS'] = df_prev['DAYS_LAST_DUE_1ST_VERSION'].abs() / 365.25
    if 'DAYS_FIRST_DUE' in df_prev.columns:
        df_prev['PREV_PLANNED_CONTRACT_DURATION'] = df_prev['DAYS_LAST_DUE_1ST_VERSION'] - df_prev['DAYS_FIRST_DUE']

    df_prev['PREV_LAST_DUE_IS_NA'] = df_prev['DAYS_LAST_DUE'].isna().astype(int)
    df_prev['PREV_LAST_DUE_YEARS'] = df_prev['DAYS_LAST_DUE'].abs() / 365.25
    if 'DAYS_FIRST_DUE' in df_prev.columns:
        df_prev['PREV_ACTUAL_CONTRACT_DURATION'] = df_prev['DAYS_LAST_DUE'] - df_prev['DAYS_FIRST_DUE']
    if 'DAYS_LAST_DUE_1ST_VERSION' in df_prev.columns:
        df_prev['PREV_DAYS_EARLY_TERMINATION'] = df_prev['DAYS_LAST_DUE_1ST_VERSION'] - df_prev['DAYS_LAST_DUE']

    df_prev['PREV_TERMINATION_IS_NA'] = df_prev['DAYS_TERMINATION'].isna().astype(int)
    df_prev['PREV_TERMINATION_YEARS'] = df_prev['DAYS_TERMINATION'].abs() / 365.25
    if 'DAYS_LAST_DUE' in df_prev.columns:
        df_prev['PREV_DAYS_DUE_TO_TERMINATION'] = df_prev['DAYS_TERMINATION'] - df_prev['DAYS_LAST_DUE']

    # 14. One-Hot Encoding for Remaining Categoricals (Cast strictly to int)
    cat_cols = df_prev.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    cat_cols = [c for c in cat_cols if c != 'NAME_CONTRACT_STATUS']
    df_prev = pd.get_dummies(df_prev, columns=cat_cols, dummy_na=True, dtype=int)
    df_prev.drop(columns=['NAME_CONTRACT_STATUS'], inplace=True, errors='ignore')

    # Cast any boolean columns to int
    for col in df_prev.select_dtypes(include=['bool']).columns:
        df_prev[col] = df_prev[col].astype(int)

    # 15. Prefix Alignment: Apply 'PREV_' prefix uniformly
    exclude_keys = ['SK_ID_CURR', 'SK_ID_PREV']
    rename_dict = {col: f'PREV_{col}' for col in df_prev.columns if col not in exclude_keys and not col.startswith('PREV_')}
    df_prev.rename(columns=rename_dict, inplace=True)

    # 16. Build Dynamic Aggregation Dictionary
    print("🔄 Grouping and aggregating records by SK_ID_CURR...")
    num_aggregations = {'SK_ID_PREV': 'count'}
    for col in df_prev.columns:
        if col in exclude_keys:
            continue
        if df_prev[col].nunique() == 2 and set(df_prev[col].dropna().unique()).issubset({0, 1}):
            num_aggregations[col] = ['mean', 'sum']
        else:
            num_aggregations[col] = ['min', 'max', 'mean', 'sum', 'var']

    prev_agg = df_prev.groupby('SK_ID_CURR').agg(num_aggregations)
    prev_agg.columns = pd.Index(
        [f"{col}_{stat.upper()}" if col != 'SK_ID_PREV' else 'PREV_COUNT' for col, stat in prev_agg.columns]
    )

    # 17. Sanitize Column Names for Tree Model Safety (Regex replacement)
    prev_agg.columns = [re.sub(r'[^\w_]', '_', col) for col in prev_agg.columns]
    prev_agg.columns = [re.sub(r'_{2,}', '_', col) for col in prev_agg.columns]
    prev_agg.reset_index(inplace=True)

    # 18. Optional Persistence & Cleanup
    if output_parquet_path:
        os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
        prev_agg.to_parquet(output_parquet_path, compression='snappy', index=False)
        print(f"💾 Saved aggregated previous application data to: {output_parquet_path}")

    print(f"✅ Finished Previous Application Pipeline. Final shape: {prev_agg.shape[0]:,} clients | {prev_agg.shape[1]} features.")

    del df_prev
    gc.collect()
    return prev_agg

if __name__ == "__main__":
    RAW_PATH = "/Users/nguyenminhtri/FinalYearPro/data/raw/previous_application.csv"
    OUTPUT_PATH = "/Users/nguyenminhtri/FinalYearPro/data/preprocess/prev_app_clean_fe_v2.parquet"
    process_previous_application_pipeline(RAW_PATH, OUTPUT_PATH)
