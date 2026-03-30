"""
Prepare aggregated data for dashboards (Streamlit, Power BI, Tableau).
"""

import pandas as pd
import numpy as np
from typing import Dict

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DashboardDataPrep:
    """Prepare dashboard-ready aggregations."""

    def compute_kpis(self, sales: pd.DataFrame) -> Dict:
        """Compute high-level KPIs."""
        return {
            "total_revenue": round(sales["revenue"].sum(), 2),
            "total_profit": round(sales["profit"].sum(), 2),
            "total_units": int(sales["units_sold"].sum()),
            "avg_order_value": round(sales["revenue"].sum() / max(sales["units_sold"].sum(), 1), 2),
            "avg_margin_pct": round(
                (sales["profit"].sum() / max(sales["revenue"].sum(), 1)) * 100, 1
            ),
            "num_products": sales["product_id"].nunique(),
            "num_transactions": len(sales),
            "promo_pct": round(sales["is_promotion"].mean() * 100, 1),
        }

    def daily_summary(self, sales: pd.DataFrame) -> pd.DataFrame:
        """Daily aggregate metrics."""
        return sales.groupby("date").agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            units=("units_sold", "sum"),
            avg_price=("price", "mean"),
            num_products=("product_id", "nunique"),
            promo_rate=("is_promotion", "mean"),
        ).reset_index()

    def category_summary(self, sales: pd.DataFrame) -> pd.DataFrame:
        """Category-level summary."""
        return sales.groupby("category").agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            units=("units_sold", "sum"),
            avg_price=("price", "mean"),
            num_products=("product_id", "nunique"),
            avg_margin=("profit", lambda x: round(x.sum() / max(sales.loc[x.index, "revenue"].sum(), 1) * 100, 1)),
        ).reset_index().sort_values("revenue", ascending=False)

    def product_performance(self, sales: pd.DataFrame, top_n: int = 50) -> pd.DataFrame:
        """Top performing products."""
        perf = sales.groupby("product_id").agg(
            category=("category", "first"),
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            units=("units_sold", "sum"),
            avg_price=("price", "mean"),
            price_std=("price", "std"),
            promo_pct=("is_promotion", "mean"),
        ).reset_index()
        perf["margin_pct"] = (perf["profit"] / perf["revenue"].replace(0, np.nan) * 100).round(1)
        return perf.nlargest(top_n, "revenue")

    def channel_mix(self, sales: pd.DataFrame) -> pd.DataFrame:
        """Revenue by channel."""
        return sales.groupby("channel").agg(
            revenue=("revenue", "sum"),
            units=("units_sold", "sum"),
            avg_price=("price", "mean"),
        ).reset_index().sort_values("revenue", ascending=False)

    def promotion_analysis(self, sales: pd.DataFrame) -> pd.DataFrame:
        """Impact of promotions by category."""
        return sales.groupby(["category", "is_promotion"]).agg(
            avg_units=("units_sold", "mean"),
            avg_revenue=("revenue", "mean"),
            avg_price=("price", "mean"),
            count=("units_sold", "count"),
        ).reset_index()
