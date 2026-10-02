import os
from pathlib import Path

# 1. Base Project & Source Directory
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent

# 2. Model Directory: Lưu TRỰC TIẾP trong src/models/
MODEL_DIR = os.path.join(SRC_DIR, "models")

CONFIG_PATH = os.path.join(MODEL_DIR, "feature_constraints.json")
BENCHMARK_PATH = os.path.join(MODEL_DIR, "train_benchmarks.json")
SCHEMA_PATH = os.path.join(MODEL_DIR, "feature_metadata.json")

# 3. Data Directories
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PREPROCESS_DIR = os.path.join(BASE_DIR, "data", "preprocess", "table")
DATA_PRODUCTION_DIR = os.path.join(BASE_DIR, "data", "production")

# 4. Production Serving Outputs
MASTER_TEST_PARQUET = os.path.join(DATA_PRODUCTION_DIR, "test_features_master.parquet")
DEMO_SAMPLES_PARQUET = os.path.join(DATA_PRODUCTION_DIR, "demo_samples.parquet")