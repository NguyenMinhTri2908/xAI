import os
from pathlib import Path

# 1. Base Project & Source Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = Path(__file__).resolve().parent.parent

# 2. Metadata & Config Directory (Single Source of Truth)
METADATA_DIR = os.path.join(SRC_DIR, "config", "metadata")

CONFIG_PATH = os.path.join(METADATA_DIR, "feature_constraints.json")
BENCHMARK_PATH = os.path.join(METADATA_DIR, "train_benchmarks.json")
SCHEMA_PATH = os.path.join(METADATA_DIR, "feature_metadata.json")
FEATURE_DICT_PATH = os.path.join(METADATA_DIR, "feature_dictionary.json")

# Aliases chuẩn hóa
FEATURE_CONSTRAINTS_PATH = CONFIG_PATH
FEATURE_METADATA_PATH = SCHEMA_PATH
TRAIN_BENCHMARKS_PATH = BENCHMARK_PATH

# 3. Model Directory: Lưu TRỌNG SỐ NHỊ PHÂN trong src/models/
MODEL_DIR = os.path.join(SRC_DIR, "models")

# 4. Data Directories
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PREPROCESS_DIR = os.path.join(BASE_DIR, "data", "preprocess", "table")
DATA_PRODUCTION_DIR = os.path.join(BASE_DIR, "data", "production")

# 5. Production Serving Outputs
MASTER_TEST_PARQUET = os.path.join(DATA_PRODUCTION_DIR, "test_features_master.parquet")
DEMO_SAMPLES_PARQUET = os.path.join(DATA_PRODUCTION_DIR, "demo_samples.parquet")

