from src.data_processing.feature_engineering import *


def process_table(df, table_name, group_col='SK_ID_CURR', config=None):
    """
    config: dict chứa các cột cần xử lý cho từng hàm
    """
    features_list = []

    if 'freq_date_col' in config:
        features_list.append(get_freq_and_tenure(df, group_col, config['freq_date_col']))

    if 'vol_col' in config:
        features_list.append(get_volatility_features(df, group_col, config['vol_col']))

    if 'mag_cols' in config:
        features_list.append(get_magnitude_features(df, group_col, config['mag_cols']))

    # Gộp tất cả
    final_df = pd.concat(features_list, axis=1)
    return apply_table_prefix(final_df, table_name)