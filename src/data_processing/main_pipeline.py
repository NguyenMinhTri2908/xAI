import os
import json
import numpy as np
import pandas as pd

# Load benchmarks from pre-extracted JSON artifact
BENCHMARK_PATH = "/Users/nguyenminhtri/FinalYearPro/Model/fair/train_benchmarks.json"

FAIR_PROHIBITED_COLUMNS = [
    'CODE_GENDER', 'NAME_FAMILY_STATUS', 'CNT_CHILDREN', 'CNT_FAM_MEMBERS',
    'INCOME_PER_PERSON', 'OBS_30_CNT_SOCIAL_CIRCLE', 'DEF_30_CNT_SOCIAL_CIRCLE',
    'OBS_60_CNT_SOCIAL_CIRCLE', 'DEF_60_CNT_SOCIAL_CIRCLE',
    'DEF_TO_OBS_30', 'DEF_TO_OBS_60'
]

def load_benchmarks(path: str = BENCHMARK_PATH) -> dict:
    """Loads pre-computed training benchmarks to prevent data leakage during inference."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Artifact not found: {path}. Please run extraction first.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def transform_application_for_inference(df_raw: pd.DataFrame, benchmarks: dict = None) -> pd.DataFrame:
    """Production transformation engine: Cleans, engineers features, and enforces

    fair-lending compliance without referencing training raw data.
    """
    if benchmarks is None:
        benchmarks = load_benchmarks()

    df = df_raw.copy()
    eps = 1e-5
    fallback_income = benchmarks.get('overall_median_income', 150000.0)

    # 1. Base Cleaning with benchmark-driven parameters
    if 'AMT_INCOME_TOTAL' in df.columns:
        df['AMT_INCOME_TOTAL'] = df['AMT_INCOME_TOTAL'].clip(upper=benchmarks['income_cap_999'])

    if 'AMT_ANNUITY' in df.columns:
        df['AMT_ANNUITY'] = df['AMT_ANNUITY'].fillna(benchmarks['annuity_median'])

    if 'AMT_GOODS_PRICE' in df.columns and 'AMT_CREDIT' in df.columns:
        df['AMT_GOODS_PRICE'] = df['AMT_GOODS_PRICE'].fillna(df['AMT_CREDIT'])

    if 'DAYS_EMPLOYED' in df.columns:
        df['DAYS_EMPLOYED'] = df['DAYS_EMPLOYED'].replace(365243, np.nan)

    if 'OCCUPATION_TYPE' in df.columns:
        df['OCCUPATION_TYPE'] = df['OCCUPATION_TYPE'].fillna('Missing')

    if 'NAME_INCOME_TYPE' in df.columns:
        rare_income_types = ['Unemployed', 'Student', 'Businessman', 'Maternity leave']
        df['NAME_INCOME_TYPE'] = df['NAME_INCOME_TYPE'].replace(rare_income_types, 'Other')

    if 'ORGANIZATION_TYPE' in df.columns:
        df['ORGANIZATION_TYPE'] = df['ORGANIZATION_TYPE'].replace('XNA', 'Missing')

    # 2. Financial ratios
    df['CREDIT_TO_INCOME'] = df['AMT_CREDIT'] / (df['AMT_INCOME_TOTAL'] + eps)
    df['ANNUITY_TO_INCOME'] = df['AMT_ANNUITY'] / (df['AMT_INCOME_TOTAL'] + eps)
    df['CREDIT_TO_ANNUITY'] = df['AMT_CREDIT'] / (df['AMT_ANNUITY'] + eps)
    df['CREDIT_TO_GOODS_RATIO'] = df['AMT_CREDIT'] / (df['AMT_GOODS_PRICE'] + eps)
    df['GOODS_CREDIT_DIFF'] = df['AMT_GOODS_PRICE'] - df['AMT_CREDIT']
    df['ANNUITY_TO_GOODS_RATIO'] = df['AMT_ANNUITY'] / (df['AMT_GOODS_PRICE'] + eps)

    # 3. Demographics and tenure
    if 'DAYS_EMPLOYED' in df.columns:
        df['DAYS_EMPLOYED_ANOM'] = df['DAYS_EMPLOYED'].isna().astype(int)
        df['EMPLOYED_YEARS'] = df['DAYS_EMPLOYED'].abs() / 365.25
    else:
        df['DAYS_EMPLOYED_ANOM'] = 0
        df['EMPLOYED_YEARS'] = 0.0

    if 'DAYS_BIRTH' in df.columns:
        df['AGE_YEARS'] = df['DAYS_BIRTH'].abs() / 365.25
        df['EMPLOYED_TO_AGE_RATIO'] = df['EMPLOYED_YEARS'] / (df['AGE_YEARS'] + eps)
    else:
        df['AGE_YEARS'] = np.nan
        df['EMPLOYED_TO_AGE_RATIO'] = np.nan

    df['INCOME_PER_EMPLOYED_YEAR'] = df['AMT_INCOME_TOTAL'] / (df['EMPLOYED_YEARS'] + eps)

    # 4. External score combinations
    ext_cols = [c for c in ['EXT_SOURCE_1', 'EXT_SOURCE_2', 'EXT_SOURCE_3'] if c in df.columns]
    if ext_cols:
        df['EXT_SOURCE_MEAN'] = df[ext_cols].mean(axis=1)
        df['EXT_SOURCE_STD'] = df[ext_cols].std(axis=1).fillna(0)
        df['EXT_SOURCE_PROD'] = df[ext_cols].prod(axis=1)
    else:
        df['EXT_SOURCE_MEAN'] = np.nan
        df['EXT_SOURCE_STD'] = 0.0
        df['EXT_SOURCE_PROD'] = np.nan

    # 5. Group benchmark mapping (Zero Data-Leakage)
    occ_means = df['OCCUPATION_TYPE'].map(benchmarks['occ_income_means']).fillna(fallback_income)
    df['INCOME_RATIO_BY_OCCUPATION'] = df['AMT_INCOME_TOTAL'] / (occ_means + eps)
    df['INCOME_DIFF_BY_OCCUPATION'] = df['AMT_INCOME_TOTAL'] - occ_means

    edu_means = df['NAME_EDUCATION_TYPE'].map(benchmarks['edu_income_means']).fillna(fallback_income)
    df['INCOME_RATIO_BY_EDUCATION'] = df['AMT_INCOME_TOTAL'] / (edu_means + eps)
    df['INCOME_DIFF_BY_EDUCATION'] = df['AMT_INCOME_TOTAL'] - edu_means

    inc_type_means = df['NAME_INCOME_TYPE'].map(benchmarks['inc_type_income_means']).fillna(fallback_income)
    df['INCOME_RATIO_BY_INCOMETYPE'] = df['AMT_INCOME_TOTAL'] / (inc_type_means + eps)
    df['INCOME_DIFF_BY_INCOMETYPE'] = df['AMT_INCOME_TOTAL'] - inc_type_means

    # 6. Fair Lending: Drop prohibited attributes
    drop_targets = [c for c in FAIR_PROHIBITED_COLUMNS if c in df.columns]
    df = df.drop(columns=drop_targets)

    return df

if __name__ == "__main__":
    # Smoke test with raw test data
    RAW_TEST_PATH = "/Users/nguyenminhtri/FinalYearPro/data/raw/application_test.csv"
    if os.path.exists(RAW_TEST_PATH):
        print(f"Executing inference test on raw application_test sample: {RAW_TEST_PATH}")
        df_sample = pd.read_csv(RAW_TEST_PATH, nrows=5)
        df_transformed = transform_application_for_inference(df_sample)
        print("Transformation successful. Transformed shape:", df_transformed.shape)
        print("Verified prohibited columns excluded:", not any(col in df_transformed.columns for col in FAIR_PROHIBITED_COLUMNS))