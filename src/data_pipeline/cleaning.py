"""
Data cleaning: handle missing values, outliers, type conversions, deduplication.
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataCleaner:
    """Clean and standardize raw data."""

    def __init__(self, outlier_method: str = "iqr", outlier_factor: float = 3.0):
        self.outlier_method = outlier_method
        self.outlier_factor = outlier_factor
        self.cleaning_report = {}

    def clean_sales(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean sales data."""
        logger.info("Cleaning sales data...")
        original_len = len(df)

        # Remove duplicates
        df = df.drop_duplicates(subset=["date", "product_id", "channel"])
        dupes = original_len - len(df)
        logger.info(f"Removed {dupes:,} duplicate rows")

        # Ensure proper types
        df["date"] = pd.to_datetime(df["date"])
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce").fillna(0).astype(int)
        df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
        df["is_promotion"] = df["is_promotion"].astype(bool)

        # Remove negative prices/units
        neg_mask = (df["price"] <= 0) | (df["units_sold"] < 0)
        df = df[~neg_mask]
        logger.info(f"Removed {neg_mask.sum():,} rows with invalid price/units")

        # Handle outliers in units_sold per product
        if self.outlier_method == "iqr":
            df = self._remove_iqr_outliers(df, "units_sold", group_col="product_id")

        # Recalculate derived columns
        df["revenue"] = (df["price"] * df["units_sold"]).round(2)
        df["profit"] = (df["revenue"] - df["cost_of_goods"]).round(2)

        # Sort
        df = df.sort_values(["product_id", "date"]).reset_index(drop=True)

        self.cleaning_report["sales"] = {
            "original_rows": original_len,
            "cleaned_rows": len(df),
            "rows_removed": original_len - len(df),
            "duplicates_removed": dupes,
        }
        logger.info(f"Sales cleaning complete: {len(df):,} rows retained")
        return df

    def clean_catalog(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean product catalog."""
        logger.info("Cleaning product catalog...")
        df = df.drop_duplicates(subset=["product_id"])
        df["base_price"] = pd.to_numeric(df["base_price"], errors="coerce")
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
        df["rating"] = df["rating"].clip(1.0, 5.0)
        df["review_count"] = df["review_count"].clip(lower=0)
        return df

    def clean_competitors(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean competitor price data."""
        logger.info("Cleaning competitor data...")
        df["date"] = pd.to_datetime(df["date"])
        df["competitor_price"] = pd.to_numeric(df["competitor_price"], errors="coerce")
        df = df.dropna(subset=["competitor_price"])
        df = df[df["competitor_price"] > 0]
        return df.sort_values(["product_id", "date", "competitor"]).reset_index(drop=True)

    def clean_inventory(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean inventory data."""
        logger.info("Cleaning inventory data...")
        df["date"] = pd.to_datetime(df["date"])
        df["stock_level"] = df["stock_level"].clip(lower=0)
        df["days_of_supply"] = df["days_of_supply"].clip(lower=0)
        return df.sort_values(["product_id", "date"]).reset_index(drop=True)

    def _remove_iqr_outliers(
        self, df: pd.DataFrame, col: str, group_col: Optional[str] = None
    ) -> pd.DataFrame:
        """Remove outliers using IQR method, optionally per group."""
        if group_col:
            q1 = df.groupby(group_col)[col].transform("quantile", 0.25)
            q3 = df.groupby(group_col)[col].transform("quantile", 0.75)
        else:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)

        iqr = q3 - q1
        lower = q1 - self.outlier_factor * iqr
        upper = q3 + self.outlier_factor * iqr
        mask = (df[col] >= lower) & (df[col] <= upper)
        removed = (~mask).sum()
        logger.info(f"Outlier removal ({col}): {removed:,} rows removed")
        return df[mask].copy()
