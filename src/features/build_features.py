"""
Main feature engineering orchestrator: combines all feature modules.
"""

import pandas as pd
import numpy as np
from typing import List, Optional

from src.features.time_features import TimeFeatureBuilder
from src.features.pricing_features import PricingFeatureBuilder
from src.features.inventory_features import InventoryFeatureBuilder
from src.utils.logger import get_logger
from src.utils.config import ROLLING_WINDOWS, LAG_PERIODS

logger = get_logger(__name__)


class FeatureBuilder:
    """Orchestrate all feature engineering steps."""

    def __init__(
        self,
        rolling_windows: Optional[List[int]] = None,
        lag_periods: Optional[List[int]] = None,
    ):
        self.rolling_windows = rolling_windows or ROLLING_WINDOWS
        self.lag_periods = lag_periods or LAG_PERIODS
        self.time_builder = TimeFeatureBuilder()
        self.pricing_builder = PricingFeatureBuilder()
        self.inventory_builder = InventoryFeatureBuilder()
        self.feature_names: List[str] = []

    def build_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run the full feature engineering pipeline."""
        logger.info(f"Starting feature engineering on {len(df):,} rows...")

        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["product_id", "date"]).reset_index(drop=True)

        # Time features
        logger.info("Building time features...")
        df = self.time_builder.build(df)

        # Pricing features
        logger.info("Building pricing features...")
        df = self.pricing_builder.build(df, self.rolling_windows, self.lag_periods)

        # Inventory features
        logger.info("Building inventory features...")
        df = self.inventory_builder.build(df, self.rolling_windows)

        # Demand lag features
        logger.info("Building demand lag features...")
        df = self._build_demand_lags(df)

        # Interaction features
        logger.info("Building interaction features...")
        df = self._build_interactions(df)

        # Track feature names
        self.feature_names = [c for c in df.columns if c not in [
            "date", "product_id", "product_name", "units_sold", "revenue",
            "profit", "cost_of_goods", "channel", "day_of_week",
        ]]

        logger.info(f"Feature engineering complete: {df.shape[1]} total columns, "
                     f"{len(self.feature_names)} feature columns")
        return df

    def _build_demand_lags(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create lagged demand features per product."""
        for lag in self.lag_periods:
            df[f"demand_lag_{lag}d"] = df.groupby("product_id")["units_sold"].shift(lag)

        for window in self.rolling_windows:
            col = f"demand_rolling_mean_{window}d"
            df[col] = (
                df.groupby("product_id")["units_sold"]
                .transform(lambda x: x.rolling(window, min_periods=1).mean())
                .round(2)
            )
            col_std = f"demand_rolling_std_{window}d"
            df[col_std] = (
                df.groupby("product_id")["units_sold"]
                .transform(lambda x: x.rolling(window, min_periods=2).std())
                .round(2)
            )

        # Demand velocity (rate of change)
        df["demand_velocity_7d"] = (
            df.groupby("product_id")["units_sold"]
            .transform(lambda x: x.rolling(7, min_periods=2).apply(
                lambda w: np.polyfit(range(len(w)), w, 1)[0] if len(w) > 1 else 0, raw=True
            ))
            .round(4)
        )
        return df

    def _build_interactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction features between key variables."""
        # Price × promotion
        if "is_promotion" in df.columns:
            df["price_x_promo"] = df["price"] * df["is_promotion"].astype(int)

        # Price × weekend
        if "is_weekend" in df.columns:
            df["price_x_weekend"] = df["price"] * df["is_weekend"].astype(int)

        # Price × holiday
        if "is_holiday" in df.columns:
            df["price_x_holiday"] = df["price"] * df["is_holiday"].astype(int)

        # Stock × price ratio
        if "stock_level" in df.columns and "price_to_base_ratio" in df.columns:
            df["stock_x_price_ratio"] = (
                df["stock_level"] * df["price_to_base_ratio"]
            ).round(2)

        # Competition gap × promotion
        if "price_vs_competition" in df.columns and "is_promotion" in df.columns:
            df["comp_gap_x_promo"] = (
                df["price_vs_competition"] * df["is_promotion"].astype(int)
            ).round(4)

        return df

    def get_feature_names(self) -> List[str]:
        """Return list of engineered feature column names."""
        return self.feature_names

    def get_numeric_features(self, df: pd.DataFrame) -> List[str]:
        """Return only numeric feature columns."""
        return [c for c in self.feature_names if pd.api.types.is_numeric_dtype(df[c])]

    def get_categorical_features(self, df: pd.DataFrame) -> List[str]:
        """Return only categorical feature columns."""
        return [c for c in self.feature_names if not pd.api.types.is_numeric_dtype(df[c])]
