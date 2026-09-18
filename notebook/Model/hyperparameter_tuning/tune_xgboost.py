import os
import time
import json
import optuna
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
import warnings

warnings.filterwarnings('ignore')

optuna.logging.set_verbosity(optuna.logging.WARNING)

# 1. ĐỌC DỮ LIỆU
file_path = '../../../data/processed/master_train_dataset_v4_clean.parquet'
print("=" * 75)
print(f"📂 [XGBOOST TUNING] Đang tải file: {file_path}")
print("=" * 75)

if not os.path.exists(file_path):
    raise FileNotFoundError(f"❌ Không tìm thấy file: {file_path}")

df = pd.read_parquet(file_path)
target_col = 'TARGET'
ignore_cols = ['SK_ID_CURR', target_col]
X = df.drop(columns=[c for c in ignore_cols if c in df.columns])
y = df[target_col]

cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
for col in cat_cols:
    X[col] = X[col].astype('category')

print(f"📊 Dữ liệu: {X.shape[0]:,} dòng | {X.shape[1]} đặc trưng")

# 2. STRATIFIED 3-FOLD NỘI BỘ
cv_search = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)


# 3. OBJECTIVE FUNCTION
def objective(trial):
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'tree_method': 'hist',
        'enable_categorical': True,
        'random_state': 42,
        'n_jobs': -1,

        # Tham số cần tinh chỉnh
        'learning_rate': trial.suggest_float('learning_rate', 0.02, 0.06, log=True),
        'max_depth': trial.suggest_int('max_depth', 5, 9),
        'min_child_weight': trial.suggest_int('min_child_weight', 20, 200),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 0.85),
        'subsample': trial.suggest_float('subsample', 0.7, 0.95),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.01, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.01, 10.0, log=True)
    }

    fold_aucs = []
    for train_idx, val_idx in cv_search.split(X, y):
        X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
        X_va, y_va = X.iloc[val_idx], y.iloc[val_idx]

        model = xgb.XGBClassifier(**params, n_estimators=1000, early_stopping_rounds=50)
        model.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], verbose=False)

        preds = model.predict_proba(X_va)[:, 1]
        fold_aucs.append(roc_auc_score(y_va, preds))

    return np.mean(fold_aucs)


# 4. CHẠY TUNING
if __name__ == '__main__':
    N_TRIALS = 30
    print(f"\n🚀 Bắt đầu tối ưu hóa XGBoost ({N_TRIALS} trials)...")

    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction='maximize', sampler=sampler)

    # "Mớm" bộ tham số mặc định ban đầu của bạn vào Trial 0 làm mốc chuẩn
    study.enqueue_trial({
        'learning_rate': 0.05,
        'max_depth': 6,
        'min_child_weight': 50,
        'colsample_bytree': 0.8,
        'subsample': 0.8,
        'reg_alpha': 0.1,
        'reg_lambda': 0.1
    })

    start_time = time.time()
    study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=True)
    duration = time.time() - start_time

    print("\n" + "=" * 60)
    print("🏆 KẾT QUẢ TỐI ƯU XGBOOST THÀNH CÔNG")
    print("=" * 60)
    print(f"⏱️ Thời gian thực thi: {duration / 60:.1f} phút")
    print(f"🎯 Best ROC-AUC (3-Fold CV): {study.best_value:.5f}")
    print(f"📌 Best Trial: #{study.best_trial.number}")
    print("\n📋 Cấu hình tham số tối ưu (best_params):")
    for k, v in study.best_params.items():
        print(f"   '{k}': {v},")
    print("=" * 60)

    # Lưu kết quả ra file json
    output_path = 'best_params_xgboost.json'
    with open(output_path, 'w') as f:
        json.dump(study.best_params, f, indent=4)
    print(f"💾 Đã lưu cấu hình vào: {output_path}")
