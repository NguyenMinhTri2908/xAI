import pandas as pd


def process_table(df, table_name, group_col='SK_ID_CURR', config=None):
    """
    Hàm điều phối: Tự động gom nhóm, tính toán feature và đặt prefix.
    """
    if config is None: config = {}
    features_list = []

    # 1. Kiểm tra và thực thi các hàm feature engineering
    if 'freq_date_col' in config:
        features_list.append(get_freq_and_tenure(df, group_col, config['freq_date_col']))

    if 'vol_col' in config:
        features_list.append(get_volatility_features(df, group_col, config['vol_col']))

    if 'mag_cols' in config:
        features_list.append(get_magnitude_features(df, group_col, config['mag_cols']))

    # 2. Xử lý logic gộp an toàn
    if not features_list:
        return pd.DataFrame(index=df[group_col].unique())

    # Dùng reduce để merge liên tục thay vì concat (an toàn hơn cho index SK_ID_CURR)
    from functools import reduce
    final_df = reduce(lambda left, right: pd.merge(left, right, on=group_col, how='outer'), features_list)

    # 3. Đặt prefix chuyên nghiệp
    return apply_table_prefix(final_df, table_name)