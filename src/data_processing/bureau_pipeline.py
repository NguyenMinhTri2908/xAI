import os
import gc
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')


def process_bureau_pipeline(raw_bureau_path: str, output_parquet_path: str = None) -> pd.DataFrame:
    """Production ETL Pipeline for Credit Bureau Data.
    Cleans structural anomalies, engineers banking risk ratios, and executes
    multi-tier aggregation (Overall, Active, Closed) grouped by SK_ID_CURR.
    """
    print("=" * 70)
    print("🚀 EXECUTING BUREAU PROCESSING & AGGREGATION PIPELINE")
    print("=" * 70)

    # 1. Load Raw Bureau Data
    if not os.path.exists(raw_bureau_path):
        raise FileNotFoundError(f"Input file not found at: {raw_bureau_path}")

    print(f"📖 Loading raw bureau dataset from: {raw_bureau_path}")
    df = pd.read_csv(raw_bureau_path)
    print(f"   • Loaded {len(df):,} records across {df.shape[1]} raw columns.")

    # 2. Step 0: Drop Uninformative & High-Missing Columns
    cols_to_drop = ['CREDIT_CURRENCY', 'AMT_ANNUITY']
    existing_drop = [c for c in cols_to_drop if c in df.columns]
    if existing_drop:
        df.drop(columns=existing_drop, inplace=True)
        print(f"   • Dropped uninformative columns: {existing_drop}")

    # 3. Step 1: Process CREDIT_ACTIVE (Binary Indicator Flags)
    df['BUREAU_IS_CLOSED'] = (df['CREDIT_ACTIVE'] == 'Closed').astype(int)
    df['BUREAU_IS_ACTIVE'] = (df['CREDIT_ACTIVE'] == 'Active').astype(int)
    df['BUREAU_IS_SOLD'] = (df['CREDIT_ACTIVE'] == 'Sold').astype(int)
    df['BUREAU_IS_BAD_DEBT'] = (df['CREDIT_ACTIVE'] == 'Bad debt').astype(int)
    df['BUREAU_IS_BAD_OR_SOLD'] = df['CREDIT_ACTIVE'].isin(['Sold', 'Bad debt']).astype(int)
    df.drop(columns=['CREDIT_ACTIVE'], inplace=True)

    # 4. Step 2: Process DAYS_CREDIT (Timeline & Recency)
    df['BUREAU_CREDIT_YEARS'] = df['DAYS_CREDIT'].abs() / 365.25
    df['BUREAU_IS_RECENT_1Y'] = (df['DAYS_CREDIT'] >= -365).astype(int)
    df['BUREAU_IS_RECENT_6M'] = (df['DAYS_CREDIT'] >= -180).astype(int)

    # 5. Step 3: Process CREDIT_DAY_OVERDUE (Regulatory Delinquency Buckets)
    df['BUREAU_IS_OVERDUE'] = (df['CREDIT_DAY_OVERDUE'] > 0).astype(int)
    df['BUREAU_DPD_GR2'] = ((df['CREDIT_DAY_OVERDUE'] >= 10) & (df['CREDIT_DAY_OVERDUE'] <= 90)).astype(int)
    df['BUREAU_DPD_GR3'] = ((df['CREDIT_DAY_OVERDUE'] >= 91) & (df['CREDIT_DAY_OVERDUE'] <= 180)).astype(int)
    df['BUREAU_DPD_GR4'] = ((df['CREDIT_DAY_OVERDUE'] >= 181) & (df['CREDIT_DAY_OVERDUE'] <= 360)).astype(int)
    df['BUREAU_DPD_GR5'] = (df['CREDIT_DAY_OVERDUE'] > 360).astype(int)
    df['BUREAU_IS_NPL'] = (df['CREDIT_DAY_OVERDUE'] >= 91).astype(int)

    # 6. Step 4: Process DAYS_CREDIT_ENDDATE (Anomalies & Horizon)
    anom_mask = (df['DAYS_CREDIT_ENDDATE'] > 3652.5) | (df['DAYS_CREDIT_ENDDATE'] < -3652.5)
    df['BUREAU_ENDDATE_ANOM'] = anom_mask.astype(int)
    df['DAYS_CREDIT_ENDDATE_CLEAN'] = df['DAYS_CREDIT_ENDDATE'].copy()
    df.loc[anom_mask, 'DAYS_CREDIT_ENDDATE_CLEAN'] = np.nan
    df['BUREAU_LOAN_DURATION_DAYS'] = df['DAYS_CREDIT_ENDDATE_CLEAN'] - df['DAYS_CREDIT']
    df['BUREAU_IS_FUTURE_OBLIGATION'] = (df['DAYS_CREDIT_ENDDATE_CLEAN'] > 0).astype(int)
    df['BUREAU_IS_LONG_TERM'] = (df['DAYS_CREDIT_ENDDATE_CLEAN'] > 365).astype(int)

    # 7. Step 5: Process DAYS_ENDDATE_FACT (Settlement Timing)
    anom_fact_mask = df['DAYS_ENDDATE_FACT'] < -3652.5
    df['BUREAU_FACT_ANOM'] = anom_fact_mask.astype(int)
    df['DAYS_ENDDATE_FACT_CLEAN'] = df['DAYS_ENDDATE_FACT'].copy()
    df.loc[anom_fact_mask, 'DAYS_ENDDATE_FACT_CLEAN'] = np.nan
    df['BUREAU_SETTLEMENT_DIFF_DAYS'] = df['DAYS_ENDDATE_FACT_CLEAN'] - df['DAYS_CREDIT_ENDDATE_CLEAN']
    df['BUREAU_IS_EARLY_SETTLED'] = (df['BUREAU_SETTLEMENT_DIFF_DAYS'] < 0).astype(int)
    df['BUREAU_IS_LATE_SETTLED'] = (df['BUREAU_SETTLEMENT_DIFF_DAYS'] > 0).astype(int)

    # 8. Step 6: Process AMT_CREDIT_MAX_OVERDUE
    df['BUREAU_MAX_OVERDUE_IS_NA'] = df['AMT_CREDIT_MAX_OVERDUE'].isna().astype(int)
    df['AMT_CREDIT_MAX_OVERDUE_CLEAN'] = df['AMT_CREDIT_MAX_OVERDUE'].fillna(0.0)
    df['BUREAU_HAS_MAX_OVERDUE'] = (df['AMT_CREDIT_MAX_OVERDUE_CLEAN'] > 0).astype(int)

    # 9. Step 7: Process CNT_CREDIT_PROLONG
    df['BUREAU_IS_PROLONGED'] = (df['CNT_CREDIT_PROLONG'] > 0).astype(int)
    df['BUREAU_IS_MULTIPLE_PROLONGED'] = (df['CNT_CREDIT_PROLONG'] >= 2).astype(int)

    # 10. Step 9: Process AMT_CREDIT_SUM
    df['AMT_CREDIT_SUM'] = df['AMT_CREDIT_SUM'].fillna(0.0)
    df['BUREAU_CREDIT_SUM_IS_ZERO'] = (df['AMT_CREDIT_SUM'] == 0.0).astype(int)

    # 11. Step 10: Process AMT_CREDIT_SUM_DEBT
    df['BUREAU_DEBT_IS_NA'] = df['AMT_CREDIT_SUM_DEBT'].isna().astype(int)
    df['AMT_CREDIT_SUM_DEBT'] = df['AMT_CREDIT_SUM_DEBT'].fillna(0.0).clip(lower=0.0)
    df['BUREAU_DEBT_RATIO'] = df['AMT_CREDIT_SUM_DEBT'] / (df['AMT_CREDIT_SUM'] + 1e-5)
    df['BUREAU_IS_DEBT_FREE'] = (df['AMT_CREDIT_SUM_DEBT'] == 0.0).astype(int)

    # 12. Step 11: Process AMT_CREDIT_SUM_LIMIT
    df['BUREAU_LIMIT_IS_NA'] = df['AMT_CREDIT_SUM_LIMIT'].isna().astype(int)
    df['BUREAU_IS_OVER_LIMIT'] = (df['AMT_CREDIT_SUM_LIMIT'] < 0.0).astype(int)
    df['AMT_CREDIT_SUM_LIMIT'] = df['AMT_CREDIT_SUM_LIMIT'].fillna(0.0).clip(lower=0.0)
    df['BUREAU_HAS_AVAILABLE_LIMIT'] = (df['AMT_CREDIT_SUM_LIMIT'] > 0.0).astype(int)

    # 13. Step 12: Process AMT_CREDIT_SUM_OVERDUE
    df['AMT_CREDIT_SUM_OVERDUE'] = df['AMT_CREDIT_SUM_OVERDUE'].clip(lower=0.0)
    df['BUREAU_HAS_SUM_OVERDUE'] = (df['AMT_CREDIT_SUM_OVERDUE'] > 0.0).astype(int)
    df['BUREAU_OVERDUE_TO_DEBT_RATIO'] = df['AMT_CREDIT_SUM_OVERDUE'] / (df['AMT_CREDIT_SUM_DEBT'] + 1e-5)

    # 14. Step 13: Process CREDIT_TYPE (One-Hot Encoding)
    top_credit_types = ['Consumer credit', 'Credit card', 'Car loan', 'Mortgage', 'Microloan']
    df['CREDIT_TYPE_CLEAN'] = df['CREDIT_TYPE'].apply(lambda x: x if x in top_credit_types else 'Other')
    type_dummies = pd.get_dummies(df['CREDIT_TYPE_CLEAN'], prefix='BUREAU_TYPE').astype(int)
    df = pd.concat([df, type_dummies], axis=1)
    df.drop(columns=['CREDIT_TYPE', 'CREDIT_TYPE_CLEAN'], inplace=True)

    # 15. Step 14: Process DAYS_CREDIT_UPDATE
    anom_update_mask = (df['DAYS_CREDIT_UPDATE'] < -3652.5) | (df['DAYS_CREDIT_UPDATE'] > 0)
    df['BUREAU_UPDATE_ANOM'] = anom_update_mask.astype(int)
    df.loc[anom_update_mask, 'DAYS_CREDIT_UPDATE'] = np.nan
    df['BUREAU_UPDATED_RECENT_30D'] = (df['DAYS_CREDIT_UPDATE'] >= -30).astype(int)
    df['BUREAU_UPDATED_RECENT_90D'] = (df['DAYS_CREDIT_UPDATE'] >= -90).astype(int)

    # 16. Step 15A & 15B: Cleanup Anomaly Columns & Derive Repayment Metrics
    raw_to_remove = ['DAYS_CREDIT_ENDDATE', 'DAYS_ENDDATE_FACT', 'AMT_CREDIT_MAX_OVERDUE']
    df.drop(columns=[c for c in raw_to_remove if c in df.columns], inplace=True)

    df['BUREAU_CREDIT_PAID_AMOUNT'] = (df['AMT_CREDIT_SUM'] - df['AMT_CREDIT_SUM_DEBT']).clip(lower=0.0)
    df['BUREAU_PAID_RATIO'] = df['BUREAU_CREDIT_PAID_AMOUNT'] / (df['AMT_CREDIT_SUM'] + 1e-5)

    # 17. Rename Remaining Columns to Ensure Uniform BUREAU_ Prefix
    rename_map = {
        'DAYS_CREDIT': 'BUREAU_DAYS_CREDIT',
        'DAYS_CREDIT_UPDATE': 'BUREAU_DAYS_CREDIT_UPDATE',
        'DAYS_CREDIT_ENDDATE_CLEAN': 'BUREAU_DAYS_CREDIT_ENDDATE_CLEAN',
        'DAYS_ENDDATE_FACT_CLEAN': 'BUREAU_DAYS_ENDDATE_FACT_CLEAN',
        'AMT_CREDIT_SUM': 'BUREAU_AMT_CREDIT_SUM',
        'AMT_CREDIT_SUM_DEBT': 'BUREAU_AMT_CREDIT_SUM_DEBT',
        'AMT_CREDIT_SUM_LIMIT': 'BUREAU_AMT_CREDIT_SUM_LIMIT',
        'AMT_CREDIT_SUM_OVERDUE': 'BUREAU_AMT_CREDIT_SUM_OVERDUE',
        'AMT_CREDIT_MAX_OVERDUE_CLEAN': 'BUREAU_AMT_CREDIT_MAX_OVERDUE_CLEAN',
        'CREDIT_DAY_OVERDUE': 'BUREAU_CREDIT_DAY_OVERDUE',
        'CNT_CREDIT_PROLONG': 'BUREAU_CNT_CREDIT_PROLONG'
    }
    df.rename(columns=rename_map, inplace=True)

    # 18. Build Aggregation Dictionary
    agg_dict = {
        'BUREAU_DAYS_CREDIT': ['min', 'max', 'mean', 'var'],
        'BUREAU_DAYS_CREDIT_UPDATE': ['max', 'mean'],
        'BUREAU_DAYS_CREDIT_ENDDATE_CLEAN': ['min', 'max', 'mean'],
        'BUREAU_DAYS_ENDDATE_FACT_CLEAN': ['min', 'max', 'mean'],
        'BUREAU_CREDIT_YEARS': ['max', 'mean'],
        'BUREAU_LOAN_DURATION_DAYS': ['max', 'mean'],
        'BUREAU_SETTLEMENT_DIFF_DAYS': ['max', 'mean'],
        'BUREAU_AMT_CREDIT_SUM': ['sum', 'mean', 'max'],
        'BUREAU_AMT_CREDIT_SUM_DEBT': ['sum', 'mean', 'max'],
        'BUREAU_AMT_CREDIT_SUM_LIMIT': ['sum', 'mean', 'max'],
        'BUREAU_AMT_CREDIT_SUM_OVERDUE': ['sum', 'mean', 'max'],
        'BUREAU_AMT_CREDIT_MAX_OVERDUE_CLEAN': ['max', 'mean'],
        'BUREAU_CREDIT_PAID_AMOUNT': ['sum', 'mean', 'max'],
        'BUREAU_CREDIT_DAY_OVERDUE': ['max', 'mean'],
        'BUREAU_CNT_CREDIT_PROLONG': ['sum', 'max'],
        'BUREAU_DEBT_RATIO': ['max', 'mean'],
        'BUREAU_OVERDUE_TO_DEBT_RATIO': ['max', 'mean'],
        'BUREAU_PAID_RATIO': ['max', 'mean'],
        'BUREAU_IS_CLOSED': ['sum', 'mean'],
        'BUREAU_IS_ACTIVE': ['sum', 'mean'],
        'BUREAU_IS_SOLD': ['sum', 'mean'],
        'BUREAU_IS_BAD_DEBT': ['sum', 'mean'],
        'BUREAU_IS_BAD_OR_SOLD': ['sum', 'mean'],
        'BUREAU_IS_RECENT_1Y': ['sum', 'mean'],
        'BUREAU_IS_RECENT_6M': ['sum', 'mean'],
        'BUREAU_IS_OVERDUE': ['sum', 'mean'],
        'BUREAU_DPD_GR2': ['sum', 'mean'],
        'BUREAU_DPD_GR3': ['sum', 'mean'],
        'BUREAU_DPD_GR4': ['sum', 'mean'],
        'BUREAU_DPD_GR5': ['sum', 'mean'],
        'BUREAU_IS_NPL': ['sum', 'mean'],
        'BUREAU_ENDDATE_ANOM': ['sum', 'mean'],
        'BUREAU_IS_FUTURE_OBLIGATION': ['sum', 'mean'],
        'BUREAU_IS_LONG_TERM': ['sum', 'mean'],
        'BUREAU_FACT_ANOM': ['sum', 'mean'],
        'BUREAU_IS_EARLY_SETTLED': ['sum', 'mean'],
        'BUREAU_IS_LATE_SETTLED': ['sum', 'mean'],
        'BUREAU_MAX_OVERDUE_IS_NA': ['sum', 'mean'],
        'BUREAU_HAS_MAX_OVERDUE': ['sum', 'mean'],
        'BUREAU_IS_PROLONGED': ['sum', 'mean'],
        'BUREAU_IS_MULTIPLE_PROLONGED': ['sum', 'mean'],
        'BUREAU_CREDIT_SUM_IS_ZERO': ['sum', 'mean'],
        'BUREAU_DEBT_IS_NA': ['sum', 'mean'],
        'BUREAU_IS_DEBT_FREE': ['sum', 'mean'],
        'BUREAU_LIMIT_IS_NA': ['sum', 'mean'],
        'BUREAU_IS_OVER_LIMIT': ['sum', 'mean'],
        'BUREAU_HAS_AVAILABLE_LIMIT': ['sum', 'mean'],
        'BUREAU_HAS_SUM_OVERDUE': ['sum', 'mean'],
        'BUREAU_TYPE_Car loan': ['sum', 'mean'],
        'BUREAU_TYPE_Consumer credit': ['sum', 'mean'],
        'BUREAU_TYPE_Credit card': ['sum', 'mean'],
        'BUREAU_TYPE_Microloan': ['sum', 'mean'],
        'BUREAU_TYPE_Mortgage': ['sum', 'mean'],
        'BUREAU_TYPE_Other': ['sum', 'mean'],
        'BUREAU_UPDATE_ANOM': ['sum', 'mean'],
        'BUREAU_UPDATED_RECENT_30D': ['sum', 'mean'],
        'BUREAU_UPDATED_RECENT_90D': ['sum', 'mean']
    }
    valid_aggs = {c: a for c, a in agg_dict.items() if c in df.columns}

    # 19. Execute Hierarchical Aggregations (Overall, Active, Closed)
    print("🔄 Grouping and aggregating overall bureau loans...")
    bureau_agg = df.groupby('SK_ID_CURR').agg(valid_aggs)
    bureau_agg.columns = [f"{col}_{stat.upper()}" for col, stat in bureau_agg.columns]
    bureau_agg['BUREAU_TOTAL_LOAN_COUNT'] = df.groupby('SK_ID_CURR').size()

    # Active loans
    if 'BUREAU_IS_ACTIVE' in df.columns:
        print("🔄 Grouping active loans...")
        active_mask = df['BUREAU_IS_ACTIVE'] == 1
        active_agg = df[active_mask].groupby('SK_ID_CURR').agg(valid_aggs)
        active_agg.columns = [f"BUREAU_ACTIVE_{col[7:]}_{stat.upper()}" for col, stat in active_agg.columns]
        active_agg['BUREAU_ACTIVE_LOAN_COUNT'] = df[active_mask].groupby('SK_ID_CURR').size()
        bureau_agg = bureau_agg.join(active_agg, how='left')

    # Closed loans
    if 'BUREAU_IS_CLOSED' in df.columns:
        print("🔄 Grouping closed loans...")
        closed_mask = df['BUREAU_IS_CLOSED'] == 1
        closed_agg = df[closed_mask].groupby('SK_ID_CURR').agg(valid_aggs)
        closed_agg.columns = [f"BUREAU_CLOSED_{col[7:]}_{stat.upper()}" for col, stat in closed_agg.columns]
        closed_agg['BUREAU_CLOSED_LOAN_COUNT'] = df[closed_mask].groupby('SK_ID_CURR').size()
        bureau_agg = bureau_agg.join(closed_agg, how='left')

    bureau_agg.reset_index(inplace=True)

    # 20. Optional Persistence & Cleanup
    if output_parquet_path:
        os.makedirs(os.path.dirname(output_parquet_path), exist_ok=True)
        bureau_agg.to_parquet(output_parquet_path, index=False)
        print(f"💾 Saved aggregated bureau data to: {output_parquet_path}")

    print(f"✅ Finished Bureau Pipeline. Final shape: {bureau_agg.shape[0]:,} clients | {bureau_agg.shape[1]} features.")

    del df
    gc.collect()
    return bureau_agg


if __name__ == "__main__":
    RAW_PATH = "/Users/nguyenminhtri/FinalYearPro/data/raw/bureau.csv"
    OUTPUT_PATH = "/Users/nguyenminhtri/FinalYearPro/data/preprocess/df_bureau_clean_fe.parquet"
    process_bureau_pipeline(RAW_PATH, OUTPUT_PATH)