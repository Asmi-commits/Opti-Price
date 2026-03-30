"""
Data transformation: merge datasets, aggregate, reshape for modeling.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataTransformer:
    """Transform and merge cleaned datasets into analysis-ready format."""

    def merge_sales_with_catalog(
        self, sales: pd.DataFrame, catalog: pd.DataFrame
    ) -> pd.DataFrame:
        """Enrich sales data with product catalog attributes."""
        logger.info("Merging sales with catalog...")
        merged = sales.merge(
            catalog[["product_id", "base_price", "cost", "brand_tier",
                      "subcategory", "rating", "review_count", "elasticity_estimate"]],
            on="product_id",
            how="left",
            suffixes=("", "_catalog"),
        )
        merged["price_to_base_ratio"] = (merged["price"] / merged["base_price"]).round(4)
        merged["margin_pct"] = ((merged["price"] - merged["cost_catalog"]) / merged["price"]).round(4)
        logger.info(f"Merged dataset: {len(merged):,} rows, {merged.shape[1]} columns")
        return merged

    def add_competitor_summary(
        self, sales: pd.DataFrame, competitors: pd.DataFrame
    ) -> pd.DataFrame:
        """Add aggregated competitor pricing info to sales data."""
        logger.info("Adding competitor price summary...")
        comp_agg = competitors.groupby(["date", "product_id"]).agg(
            avg_competitor_price=("competitor_price", "mean"),
            min_competitor_price=("competitor_price", "min"),
            max_competitor_price=("competitor_price", "max"),
            num_competitors_in_stock=("in_stock", "sum"),
            any_competitor_promo=("has_promotion", "any"),
        ).reset_index()

        merged = sales.merge(comp_agg, on=["date", "product_id"], how="left")
        # Forward-fill missing competitor data (not sampled every day)
        comp_cols = ["avg_competitor_price", "min_competitor_price",
                     "max_competitor_price", "num_competitors_in_stock"]
        merged[comp_cols] = merged.groupby("product_id")[comp_cols].ffill()
        merged["price_vs_competition"] = (
            (merged["price"] - merged["avg_competitor_price"]) / merged["avg_competitor_price"]
        ).round(4)
        return merged

    def add_inventory_features(
        self, sales: pd.DataFrame, inventory: pd.DataFrame
    ) -> pd.DataFrame:
        """Add inventory-based features."""
        logger.info("Adding inventory features...")
        inv_daily = inventory.groupby(["date", "product_id"]).agg(
            stock_level=("stock_level", "mean"),
            days_of_supply=("days_of_supply", "mean"),
        ).reset_index()

        merged = sales.merge(inv_daily, on=["date", "product_id"], how="left")
        merged[["stock_level", "days_of_supply"]] = (
            merged.groupby("product_id")[["stock_level", "days_of_supply"]].ffill()
        )
        merged["low_stock_flag"] = (merged["days_of_supply"] < 7).astype(int)
        return merged

    def add_holiday_flags(
        self, sales: pd.DataFrame, holidays: pd.DataFrame
    ) -> pd.DataFrame:
        """Flag holiday and near-holiday periods."""
        logger.info("Adding holiday flags...")
        high_dates = set(
            holidays[holidays["impact_level"] == "high"]["date"].dt.strftime("%Y-%m-%d")
        )
        all_dates = set(holidays["date"].dt.strftime("%Y-%m-%d"))

        sales_dates = sales["date"].dt.strftime("%Y-%m-%d")
        sales["is_holiday"] = sales_dates.isin(all_dates).astype(int)
        sales["is_major_holiday"] = sales_dates.isin(high_dates).astype(int)

        # Near-holiday window (3 days before/after)
        holiday_dates_dt = pd.to_datetime(list(all_dates))
        near_holiday = set()
        for hd in holiday_dates_dt:
            for offset in range(-3, 4):
                near_holiday.add((hd + pd.Timedelta(days=offset)).strftime("%Y-%m-%d"))
        sales["near_holiday"] = sales_dates.isin(near_holiday).astype(int)
        return sales

    def create_daily_product_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate to daily product-level summary (across channels)."""
        logger.info("Creating daily product summary...")
        agg = df.groupby(["date", "product_id", "category"]).agg(
            total_units=("units_sold", "sum"),
            total_revenue=("revenue", "sum"),
            total_profit=("profit", "sum"),
            avg_price=("price", "mean"),
            max_price=("price", "max"),
            min_price=("price", "min"),
            num_channels=("channel", "nunique"),
            any_promotion=("is_promotion", "any"),
        ).reset_index()
        return agg

    def build_master_dataset(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Build the full master dataset from all sources."""
        logger.info("Building master dataset...")
        df = self.merge_sales_with_catalog(data["sales"], data["catalog"])
        df = self.add_competitor_summary(df, data["competitors"])
        df = self.add_inventory_features(df, data["inventory"])
        df = self.add_holiday_flags(df, data["holidays"])
        logger.info(f"Master dataset: {len(df):,} rows, {df.shape[1]} columns")
        return df