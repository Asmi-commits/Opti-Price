"""
Inventory-based feature engineering: stock levels, supply risk, restock patterns.
"""

import pandas as pd
import numpy as np
from typing import List

from src.utils.logger import get_logger

logger = get_logger(__name__)


class InventoryFeatureBuilder:
    """Build inventory-related features."""

    def build(self, df: pd.DataFrame, rolling_windows: List[int]) -> pd.DataFrame:
        """Add all inventory features."""
        if "stock_level" not in df.columns:
            logger.warning("No stock_level column found; skipping inventory features")
            return df

        df = self._stock_status(df)
        df = self._stock_dynamics(df, rolling_windows)
        df = self._supply_risk(df)
        return df

    def _stock_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """Current stock status indicators."""
        df["low_stock_flag"] = (df["days_of_supply"] < 7).astype(int) if "days_of_supply" in df.columns else 0
        df["out_of_stock_flag"] = (df["stock_level"] <= 0).astype(int)

        # Stock level buckets
        df["stock_bucket"] = pd.cut(
            df["stock_level"],
            bins=[-1, 0, 50, 200, 500, float("inf")],
            labels=["out_of_stock", "critical", "low", "adequate", "high"],
        )

        # Stock to demand ratio
        demand_7d = df.get("demand_rolling_mean_7d", df.get("rolling_7d_sales"))
        if demand_7d is not None:
            df["stock_to_demand_ratio"] = (
                df["stock_level"] / demand_7d.replace(0, np.nan)
            ).round(2)
        return df

    def _stock_dynamics(self, df: pd.DataFrame, rolling_windows: List[int]) -> pd.DataFrame:
        """Stock level change patterns."""
        grp = df.groupby("product_id")["stock_level"]

        df["stock_change_1d"] = grp.diff()
        df["stock_change_pct_1d"] = (grp.pct_change()).round(4)

        for window in rolling_windows:
            df[f"stock_rolling_mean_{window}d"] = (
                grp.transform(lambda x: x.rolling(window, min_periods=1).mean()).round(1)
            )
            df[f"stock_rolling_min_{window}d"] = (
                grp.transform(lambda x: x.rolling(window, min_periods=1).min())
            )

        # Restock detection (large positive stock change)
        df["possible_restock"] = (df["stock_change_1d"] > 50).astype(int)
        return df

    def _supply_risk(self, df: pd.DataFrame) -> pd.DataFrame:
        """Supply risk scoring."""
        risk_score = np.zeros(len(df))

        # Low days of supply
        if "days_of_supply" in df.columns:
            risk_score += np.where(df["days_of_supply"] < 3, 3, 0)
            risk_score += np.where(df["days_of_supply"].between(3, 7), 2, 0)
            risk_score += np.where(df["days_of_supply"].between(7, 14), 1, 0)

        # Stock declining rapidly
        if "stock_change_pct_1d" in df.columns:
            risk_score += np.where(df["stock_change_pct_1d"] < -0.2, 2, 0)

        # Low absolute stock
        risk_score += np.where(df["stock_level"] < 20, 2, 0)
        risk_score += np.where(df["stock_level"] < 50, 1, 0)

        df["supply_risk_score"] = risk_score.astype(int)
        df["supply_risk_level"] = pd.cut(
            df["supply_risk_score"],
            bins=[-1, 2, 4, float("inf")],
            labels=["low", "medium", "high"],
        )
<<<<<<< HEAD
        return df
=======
        return df
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
