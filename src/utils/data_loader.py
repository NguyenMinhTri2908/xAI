import os
import pandas as pd



# [1] Cấu hình thư mục gốc
DATA_DIR = "/Users/nguyenminhtri/FinalYearPro/data/raw"

# Nhóm Bảng chính (Main Tables)
MAIN_TRAIN_FILE = os.path.join(DATA_DIR, "application_train.csv")
MAIN_TEST_FILE  = os.path.join(DATA_DIR, "application_test.csv")

# Nhóm Luồng lịch sử BÊN NGOÀI Home Credit (Credit Bureau Stream)
BUREAU_FILE      = os.path.join(DATA_DIR, "bureau.csv")
BUREAU_BAL_FILE  = os.path.join(DATA_DIR, "bureau_balance.csv")

# Nhóm Luồng lịch sử BÊN TRONG Home Credit (Internal Behavioral Stream)
PREV_APP_FILE    = os.path.join(DATA_DIR, "previous_application.csv")
INS_PAYMENT_FILE = os.path.join(DATA_DIR, "installments_payments.csv")
POS_CASH_FILE    = os.path.join(DATA_DIR, "POS_CASH_balance.csv")
CREDIT_CARD_FILE = os.path.join(DATA_DIR, "credit_card_balance.csv")

# File phụ bổ sung thông tin mô tả
COL_DESC_FILE    = os.path.join(DATA_DIR, "HomeCredit_columns_description.csv")