"""
Shared model utilities: train/test split, encoding, cross-validation helpers.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder, StandardScaler
import pickle
from pathlib import Path

from src.utils.config import TEST_START_DATE, RANDOM_SEED
from src.utils.logger import get_logger

logger = get_logger(__name__)


def temporal_train_test_split(
    df: pd.DataFrame,
    date_col: str = "date",
    test_start: str = TEST_START_DATE,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split data temporally (no leakage)."""
    df[date_col] = pd.to_datetime(df[date_col])
    train = df[df[date_col] < test_start].copy()
    test = df[df[date_col] >= test_start].copy()
    logger.info(f"Train: {len(train):,} rows ({train[date_col].min()} to {train[date_col].max()})")
    logger.info(f"Test:  {len(test):,} rows ({test[date_col].min()} to {test[date_col].max()})")
    return train, test


def get_time_series_cv(n_splits: int = 5, gap: int = 7) -> TimeSeriesSplit:
    """Get time-series cross-validation splitter."""
    return TimeSeriesSplit(n_splits=n_splits, gap=gap)


def encode_categoricals(
    train: pd.DataFrame,
    test: pd.DataFrame,
    cat_cols: List[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, LabelEncoder]]:
    """Label-encode categorical columns (fit on train, transform both)."""
    encoders = {}
    for col in cat_cols:
        if col in train.columns:
            le = LabelEncoder()
            train[col] = le.fit_transform(train[col].astype(str))
            # Handle unseen categories in test
            test_vals = test[col].astype(str)
            known = set(le.classes_)
            test_vals = test_vals.map(lambda x: x if x in known else le.classes_[0])
            test[col] = le.transform(test_vals)
            encoders[col] = le
    return train, test, encoders


def scale_features(
    train: pd.DataFrame,
    test: pd.DataFrame,
    num_cols: List[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, StandardScaler]:
    """Standard-scale numeric features."""
    scaler = StandardScaler()
    existing = [c for c in num_cols if c in train.columns]
    train[existing] = scaler.fit_transform(train[existing])
    test[existing] = scaler.transform(test[existing])
    return train, test, scaler


def save_model(model, filepath: str) -> None:
    """Serialize model to disk."""
    fp = Path(filepath)
    fp.parent.mkdir(parents=True, exist_ok=True)
    with open(fp, "wb") as f:
        pickle.dump(model, f)
    logger.info(f"Model saved to {fp}")


def load_model(filepath: str):
    """Deserialize model from disk."""
    with open(filepath, "rb") as f:
        return pickle.load(f)


def prepare_features(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str,
    drop_na: bool = True,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Extract X, y from dataframe, handling missing values."""
    existing = [c for c in feature_cols if c in df.columns]
    missing = set(feature_cols) - set(existing)
    if missing:
        logger.warning(f"Missing feature columns: {missing}")

    subset = df[existing + [target_col]].copy()
    if drop_na:
        before = len(subset)
        subset = subset.dropna()
        dropped = before - len(subset)
        if dropped > 0:
            logger.info(f"Dropped {dropped:,} rows with NaN values")

    X = subset[existing]
    y = subset[target_col]
<<<<<<< HEAD
    return X, y
=======
    return X, y
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
