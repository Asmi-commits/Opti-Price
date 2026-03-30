"""
Centralized configuration for the dynamic pricing optimization project.
"""

import os
from pathlib import Path

# ── Project Paths ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXTERNAL_DIR = DATA_DIR / "external"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results"

# ── Data Files ─────────────────────────────────────────────────────────
SALES_FILE = RAW_DIR / "sales_data.csv"
CATALOG_FILE = RAW_DIR / "product_catalog.csv"
COMPETITOR_FILE = RAW_DIR / "competitor_prices.csv"
INVENTORY_FILE = RAW_DIR / "inventory_data.csv"
HOLIDAYS_FILE = EXTERNAL_DIR / "holidays_calendar.csv"
CLEANED_FILE = PROCESSED_DIR / "cleaned_data.csv"
FEATURES_FILE = PROCESSED_DIR / "feature_engineered.csv"
SPLIT_FILE = PROCESSED_DIR / "train_test_split.csv"

# ── Model Parameters ──────────────────────────────────────────────────
RANDOM_SEED = 42
TEST_START_DATE = "2024-10-01"
TRAIN_END_DATE = "2024-09-30"

# ── Feature Engineering ───────────────────────────────────────────────
ROLLING_WINDOWS = [7, 14, 30, 60]
LAG_PERIODS = [1, 7, 14, 28]
PRICE_BINS = [0, 10, 25, 50, 100, 250, 500, 1000, float("inf")]
PRICE_BIN_LABELS = ["0-10", "10-25", "25-50", "50-100", "100-250", "250-500", "500-1000", "1000+"]

# ── Model Training ────────────────────────────────────────────────────
DEMAND_MODEL_PARAMS = {
    "n_estimators": 500,
    "max_depth": 8,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 5,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
}

ELASTICITY_MODEL_PARAMS = {
    "alpha": 1.0,  # Ridge regularization
    "fit_intercept": True,
}

# ── Pricing Optimization ──────────────────────────────────────────────
MIN_MARGIN_PCT = 0.05  # Minimum 5% margin
MAX_PRICE_CHANGE_PCT = 0.20  # Max 20% price change per period
PRICE_STEP_SIZE = 0.01  # 1% increments for grid search
OPTIMIZATION_OBJECTIVE = "profit"  # "profit" or "revenue"

# ── API ───────────────────────────────────────────────────────────────
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_VERSION = "v1"

# ── Logging ───────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
<<<<<<< HEAD
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
=======
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
