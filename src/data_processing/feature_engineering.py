import pandas as pd

def get_freq_and_tenure(df, group_col, date_col):
    agg = df.groupby(group_col).agg({date_col: ['count', 'min']})
    agg.columns = ['COUNT_EVENTS', 'MIN_MONTH']
    agg['TENURE'] = -agg['MIN_MONTH']
    return agg.drop(columns=['MIN_MONTH'])

def get_volatility_features(df, group_col, target_col):
    return df.groupby(group_col)[target_col].std().to_frame('VOLATILITY').fillna(0)

def get_magnitude_features(df, group_col, cols_to_agg):
    agg = df.groupby(group_col)[cols_to_agg].agg(['min', 'max', 'mean'])
    agg.columns = [f"{col}_{stat}" for col, stat in agg.columns]
    return agg

def apply_table_prefix(df, table_name):
    df.columns = [f"{table_name}_{col}" for col in df.columns]
    return df