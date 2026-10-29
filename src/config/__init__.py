"""
TẬP TRUNG TOÀN BỘ CẤU HÌNH & ĐƯỜNG DẪN HỆ THỐNG (SINGLE SOURCE OF TRUTH)
=======================================================================
Re-export toàn bộ hằng số đường dẫn (paths) và tham số định giá (pricing_config).
"""

from .paths import (
    BASE_DIR,
    SRC_DIR,
    METADATA_DIR,
    CONFIG_PATH,
    BENCHMARK_PATH,
    SCHEMA_PATH,
    FEATURE_DICT_PATH,
    FEATURE_CONSTRAINTS_PATH,
    FEATURE_METADATA_PATH,
    TRAIN_BENCHMARKS_PATH,
    MODEL_DIR,
    DATA_RAW_DIR,
    DATA_PREPROCESS_DIR,
    DATA_PRODUCTION_DIR,
    MASTER_TEST_PARQUET,
    DEMO_SAMPLES_PARQUET,
)
from .pricing_config import RetailPricingConfig, retail_pricing_config

__all__ = [
    # Thư mục cơ sở
    "BASE_DIR",
    "SRC_DIR",
    # Metadata & Config paths
    "METADATA_DIR",
    "CONFIG_PATH",
    "BENCHMARK_PATH",
    "SCHEMA_PATH",
    "FEATURE_DICT_PATH",
    "FEATURE_CONSTRAINTS_PATH",
    "FEATURE_METADATA_PATH",
    "TRAIN_BENCHMARKS_PATH",
    # Model binary directory
    "MODEL_DIR",
    # Data pipeline directories
    "DATA_RAW_DIR",
    "DATA_PREPROCESS_DIR",
    "DATA_PRODUCTION_DIR",
    # Serving outputs
    "MASTER_TEST_PARQUET",
    "DEMO_SAMPLES_PARQUET",
    # Pricing configuration
    "RetailPricingConfig",
    "retail_pricing_config",
]
