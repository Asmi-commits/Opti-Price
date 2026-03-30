"""
Pricing-specific feature engineering: price ratios, volatility, elasticity proxies.
"""

import pandas as pd
import numpy as np
from typing import List

from src.utils.logger import get_logger
from src.utils.config import PRICE_BINS, PRICE_BIN_LABELS

logger = get_logger(__name__)


class PricingFeatureBuilder:
    """Build pricing-related features."""

    def build(
        self, df: pd.DataFrame,
        rolling_windows: List[int],
        lag_periods: List[int],
    ) -> pd.DataFrame:
        """Add all pricing features."""
        df = self._price_ratios(df)
        df = self._price_dynamics(df, rolling_windows, lag_periods)
        df = self._competitor_features(df)
        df = self._promotion_features(df, rolling_windows)
        df = self._price_bins(df)
        return df

    def _price_ratios(self, df: pd.DataFrame) -> pd.DataFrame:
        """Price relative to reference points."""
        if "base_price" in df.columns:
            df["price_to_base_ratio"] = (df["price"] / df["base_price"]).round(4)
            df["discount_depth"] = ((df["base_price"] - df["price"]) / df["base_price"]).round(4)

        if "cost" in df.columns or "cost_catalog" in df.columns:
            cost_col = "cost_catalog" if "cost_catalog" in df.columns else "cost"
            df["markup_ratio"] = (df["price"] / df[cost_col]).round(4)
            df["margin_pct"] = ((df["price"] - df[cost_col]) / df["price"]).round(4)

        return df

    def _price_dynamics(
        self, df: pd.DataFrame,
        rolling_windows: List[int],
        lag_periods: List[int],
    ) -> pd.DataFrame:
        """Price change and volatility features."""
        grp = df.groupby("product_id")["price"]

        # Price lags
        for lag in lag_periods:
            df[f"price_lag_{lag}d"] = grp.shift(lag)
            df[f"price_change_{lag}d"] = (
                (df["price"] - df[f"price_lag_{lag}d"]) / df[f"price_lag_{lag}d"]
            ).round(6)

        # Rolling price stats
        for window in rolling_windows:
            df[f"price_rolling_mean_{window}d"] = (
                grp.transform(lambda x: x.rolling(window, min_periods=1).mean()).round(2)
            )
            df[f"price_rolling_std_{window}d"] = (
                grp.transform(lambda x: x.rolling(window, min_periods=2).std()).round(4)
            )
            df[f"price_volatility_{window}d"] = (
                df[f"price_rolling_std_{window}d"] / df[f"price_rolling_mean_{window}d"]
            ).round(6)
            df[f"price_rolling_min_{window}d"] = (
                grp.transform(lambda x: x.rolling(window, min_periods=1).min()).round(2)
            )
            df[f"price_rolling_max_{window}d"] = (
                grp.transform(lambda x: x.rolling(window, min_periods=1).max()).round(2)
            )
            # Where current price sits in recent range
            rng = df[f"price_rolling_max_{window}d"] - df[f"price_rolling_min_{window}d"]
            df[f"price_position_{window}d"] = np.where(
                rng > 0,
                ((df["price"] - df[f"price_rolling_min_{window}d"]) / rng).round(4),
                0.5,
            )

        # Price momentum
        if "price_rolling_mean_7d" in df.columns and "price_rolling_mean_30d" in df.columns:
            df["price_momentum"] = (
                (df["price_rolling_mean_7d"] - df["price_rolling_mean_30d"])
                / df["price_rolling_mean_30d"]
            ).round(6)

        return df

    def _competitor_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Features based on competitor pricing."""
        if "avg_competitor_price" not in df.columns:
            return df

        df["price_vs_competition"] = (
            (df["price"] - df["avg_competitor_price"]) / df["avg_competitor_price"]
        ).round(4)
        df["is_cheapest"] = (df["price"] <= df["min_competitor_price"]).astype(int)
        df["is_most_expensive"] = (df["price"] >= df["max_competitor_price"]).astype(int)
        df["competitor_price_spread"] = (
            (df["max_competitor_price"] - df["min_competitor_price"]) / df["avg_competitor_price"]
        ).round(4)

        return df

    def _promotion_features(self, df: pd.DataFrame, rolling_windows: List[int]) -> pd.DataFrame:
        """Promotion-related features."""
        if "is_promotion" not in df.columns:
            return df

        promo_int = df["is_promotion"].astype(int)
        for window in rolling_windows:
            df[f"promo_frequency_{window}d"] = (
                df.groupby("product_id")["is_promotion"]
                .transform(lambda x: x.astype(int).rolling(window, min_periods=1).mean())
                .round(4)
            )

        # Days since last promotion
        df["days_since_promo"] = (
            df.groupby("product_id")["is_promotion"]
            .transform(lambda x: x.astype(int)
                       .replace(0, np.nan)
                       .groupby(x.astype(int).cumsum())
                       .cumcount())
        )

        if "promotion_discount_pct" in df.columns:
            df["promo_discount_depth"] = df["promotion_discount_pct"] / 100.0
        return df

    def _price_bins(self, df: pd.DataFrame) -> pd.DataFrame:
        """Categorize prices into bins."""
        df["price_bin"] = pd.cut(
            df["price"], bins=PRICE_BINS, labels=PRICE_BIN_LABELS, right=False
        )
        return df
