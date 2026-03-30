"""
Demand forecasting model using Gradient Boosted Trees.
Predicts units_sold given pricing, time, inventory, and competitor features.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.models.model_utils import (
    temporal_train_test_split, prepare_features, save_model, load_model,
    encode_categoricals, get_time_series_cv,
)
from src.utils.config import DEMAND_MODEL_PARAMS, RANDOM_SEED
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DemandForecaster:
    """Predict product demand (units sold) using ensemble methods."""

    FEATURE_COLS = [
        # Time features
        "day_of_week_num", "month", "quarter", "is_weekend",
        "month_sin", "month_cos", "dow_sin", "dow_cos",
        "days_since_start", "product_age_days",
        "is_month_start", "is_month_end", "near_payday",
        # Pricing features
        "price", "price_to_base_ratio", "discount_depth", "margin_pct",
        "price_change_1d", "price_rolling_mean_7d", "price_rolling_mean_30d",
        "price_volatility_7d", "price_momentum",
        # Demand lags
        "demand_lag_1d", "demand_lag_7d", "demand_lag_14d", "demand_lag_28d",
        "demand_rolling_mean_7d", "demand_rolling_mean_30d",
        "demand_rolling_std_7d", "demand_velocity_7d",
        # Inventory
        "stock_level", "days_of_supply", "low_stock_flag", "supply_risk_score",
        # Competition
        "price_vs_competition", "is_cheapest", "competitor_price_spread",
        # Promotions
        "is_promotion", "promotion_discount_pct",
        "promo_frequency_7d", "promo_frequency_30d",
        # Holidays
        "is_holiday", "is_major_holiday", "near_holiday",
        # Interactions
        "price_x_promo", "price_x_weekend", "price_x_holiday",
    ]

    def __init__(self, model_type: str = "gbr", params: Optional[Dict] = None):
        self.model_type = model_type
        self.params = params or DEMAND_MODEL_PARAMS
        self.model = None
        self.feature_importance: Optional[pd.DataFrame] = None
        self.metrics: Dict = {}

    def build_model(self):
        """Initialize the model."""
        if self.model_type == "gbr":
            self.model = GradientBoostingRegressor(
                random_state=RANDOM_SEED, **self.params
            )
        elif self.model_type == "rf":
            self.model = RandomForestRegressor(
                n_estimators=self.params.get("n_estimators", 500),
                max_depth=self.params.get("max_depth", 8),
                random_state=RANDOM_SEED,
                n_jobs=-1,
            )
        elif self.model_type == "ridge":
            self.model = Ridge(alpha=1.0)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        logger.info(f"Initialized {self.model_type} model")

    def train(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """Fit the model on training data."""
        if self.model is None:
            self.build_model()

        logger.info(f"Training on {len(X_train):,} samples, {X_train.shape[1]} features")
        self.model.fit(X_train, y_train)

        # Feature importance
        if hasattr(self.model, "feature_importances_"):
            self.feature_importance = pd.DataFrame({
                "feature": X_train.columns,
                "importance": self.model.feature_importances_,
            }).sort_values("importance", ascending=False)
            logger.info(f"Top 10 features:\n{self.feature_importance.head(10).to_string()}")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate predictions."""
        preds = self.model.predict(X)
        return np.maximum(preds, 0).round(0)  # Demand can't be negative

    def evaluate(self, X_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
        """Evaluate model on test set."""
        preds = self.predict(X_test)
        self.metrics = {
            "mae": mean_absolute_error(y_test, preds),
            "rmse": np.sqrt(mean_squared_error(y_test, preds)),
            "mape": np.mean(np.abs((y_test - preds) / np.maximum(y_test, 1))) * 100,
            "r2": r2_score(y_test, preds),
            "median_ae": np.median(np.abs(y_test - preds)),
            "n_samples": len(y_test),
        }
        logger.info(f"Evaluation metrics: MAE={self.metrics['mae']:.2f}, "
                     f"RMSE={self.metrics['rmse']:.2f}, "
                     f"MAPE={self.metrics['mape']:.1f}%, "
                     f"R²={self.metrics['r2']:.4f}")
        return self.metrics

    def cross_validate(
        self, X: pd.DataFrame, y: pd.Series, n_splits: int = 5
    ) -> Dict[str, List[float]]:
        """Time-series cross-validation."""
        tscv = get_time_series_cv(n_splits=n_splits)
        cv_results = {"mae": [], "rmse": [], "r2": []}

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_tr, y_val = y.iloc[train_idx], y.iloc[val_idx]

            self.build_model()
            self.model.fit(X_tr, y_tr)
            preds = self.predict(X_val)

            cv_results["mae"].append(mean_absolute_error(y_val, preds))
            cv_results["rmse"].append(np.sqrt(mean_squared_error(y_val, preds)))
            cv_results["r2"].append(r2_score(y_val, preds))

            logger.info(f"Fold {fold+1}: MAE={cv_results['mae'][-1]:.2f}, R²={cv_results['r2'][-1]:.4f}")

        logger.info(f"CV Mean MAE: {np.mean(cv_results['mae']):.2f} ± {np.std(cv_results['mae']):.2f}")
        return cv_results

    def save(self, filepath: str) -> None:
        save_model(self.model, filepath)

    def load(self, filepath: str) -> None:
<<<<<<< HEAD
        self.model = load_model(filepath)
=======
        self.model = load_model(filepath)
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
