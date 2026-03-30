"""
Time-based feature engineering: calendar features, seasonality, trends.
"""

import pandas as pd
import numpy as np

from src.utils.logger import get_logger

logger = get_logger(__name__)


class TimeFeatureBuilder:
    """Extract time-based features from date columns."""

    def build(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add all time features."""
        df = self._calendar_features(df)
        df = self._cyclical_encoding(df)
        df = self._trend_features(df)
        return df

    def _calendar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Basic calendar decomposition."""
        dt = df["date"].dt
        df["day_of_week_num"] = dt.dayofweek
        df["day_of_month"] = dt.day
        df["week_of_year"] = dt.isocalendar().week.astype(int)
        df["month"] = dt.month
        df["quarter"] = dt.quarter
        df["year"] = dt.year
        df["is_weekend"] = (dt.dayofweek >= 5).astype(int)
        df["is_month_start"] = dt.is_month_start.astype(int)
        df["is_month_end"] = dt.is_month_end.astype(int)
        df["is_quarter_start"] = dt.is_quarter_start.astype(int)
        df["is_quarter_end"] = dt.is_quarter_end.astype(int)
        df["days_in_month"] = dt.days_in_month

        # Pay-cycle proxy: days near 1st and 15th
        df["near_payday"] = ((df["day_of_month"] <= 3) | 
                             (df["day_of_month"].between(14, 17))).astype(int)
        return df

    def _cyclical_encoding(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode cyclical features using sin/cos transformations."""
        # Day of week (period = 7)
        df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week_num"] / 7).round(6)
        df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week_num"] / 7).round(6)
        # Month (period = 12)
        df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12).round(6)
        df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12).round(6)
        # Day of month (period = 31)
        df["dom_sin"] = np.sin(2 * np.pi * df["day_of_month"] / 31).round(6)
        df["dom_cos"] = np.cos(2 * np.pi * df["day_of_month"] / 31).round(6)
        # Week of year (period = 52)
        df["woy_sin"] = np.sin(2 * np.pi * df["week_of_year"] / 52).round(6)
        df["woy_cos"] = np.cos(2 * np.pi * df["week_of_year"] / 52).round(6)
        return df

    def _trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Time-based trend features."""
        min_date = df["date"].min()
        df["days_since_start"] = (df["date"] - min_date).dt.days
        df["weeks_since_start"] = (df["days_since_start"] / 7).round(1)

        # Product age (days since first appearance in data)
        first_seen = df.groupby("product_id")["date"].transform("min")
        df["product_age_days"] = (df["date"] - first_seen).dt.days
        return df
