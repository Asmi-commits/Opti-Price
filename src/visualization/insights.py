"""
Automated insights generation from pricing and demand data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List

from src.utils.logger import get_logger

logger = get_logger(__name__)


class InsightsGenerator:
    """Generate automated business insights from data."""

    def generate_all(self, sales: pd.DataFrame, catalog: pd.DataFrame) -> List[Dict]:
        """Generate a comprehensive set of insights."""
        insights = []
        insights.extend(self._revenue_trends(sales))
        insights.extend(self._pricing_insights(sales, catalog))
        insights.extend(self._promotion_effectiveness(sales))
        insights.extend(self._category_insights(sales))
        insights.extend(self._channel_insights(sales))
        return insights

    def _revenue_trends(self, df: pd.DataFrame) -> List[Dict]:
        """Identify revenue trends and anomalies."""
        insights = []
        df["date"] = pd.to_datetime(df["date"])
        monthly = df.set_index("date")["revenue"].resample("ME").sum()

        # Month-over-month growth
        mom_growth = monthly.pct_change().dropna()
        best_month = mom_growth.idxmax()
        worst_month = mom_growth.idxmin()

        insights.append({
            "category": "revenue",
            "type": "trend",
            "title": "Best Growth Month",
            "description": f"Highest MoM revenue growth of {mom_growth[best_month]*100:.1f}% in {best_month.strftime('%B %Y')}",
            "impact": "positive",
        })

        if mom_growth[worst_month] < -0.05:
            insights.append({
                "category": "revenue",
                "type": "alert",
                "title": "Revenue Decline Alert",
                "description": f"Revenue declined {abs(mom_growth[worst_month])*100:.1f}% in {worst_month.strftime('%B %Y')}",
                "impact": "negative",
            })

        return insights

    def _pricing_insights(self, sales: pd.DataFrame, catalog: pd.DataFrame) -> List[Dict]:
        """Pricing-related insights."""
        insights = []
        merged = sales.merge(catalog[["product_id", "base_price"]], on="product_id", how="left")
        merged["discount_pct"] = ((merged["base_price"] - merged["price"]) / merged["base_price"]).clip(0, 1)

        # Heavily discounted categories
        cat_discount = merged.groupby("category")["discount_pct"].mean().sort_values(ascending=False)
        top_discount_cat = cat_discount.index[0]
        insights.append({
            "category": "pricing",
            "type": "observation",
            "title": "Deepest Average Discounts",
            "description": f"{top_discount_cat} has the deepest avg discounts at {cat_discount.iloc[0]*100:.1f}% off base price",
            "impact": "neutral",
        })

        # Price consistency
        price_cv = sales.groupby("product_id")["price"].agg(lambda x: x.std() / x.mean())
        volatile = (price_cv > 0.15).sum()
        if volatile > 0:
            insights.append({
                "category": "pricing",
                "type": "recommendation",
                "title": "Price Volatility",
                "description": f"{volatile} products have price coefficient of variation > 15%. Consider more stable pricing for brand perception.",
                "impact": "actionable",
            })
        return insights

    def _promotion_effectiveness(self, sales: pd.DataFrame) -> List[Dict]:
        """Promotion impact insights."""
        insights = []
        promo = sales[sales["is_promotion"]]
        no_promo = sales[~sales["is_promotion"]]

        lift = promo["units_sold"].mean() / max(no_promo["units_sold"].mean(), 1)
        margin_promo = promo["profit"].sum() / max(promo["revenue"].sum(), 1)
        margin_no_promo = no_promo["profit"].sum() / max(no_promo["revenue"].sum(), 1)

        insights.append({
            "category": "promotions",
            "type": "analysis",
            "title": "Promotion Volume Lift",
            "description": f"Promotions drive {lift:.1f}x volume lift on average, but margins are {(margin_no_promo - margin_promo)*100:.1f}pp lower",
            "impact": "mixed",
        })
        return insights

    def _category_insights(self, sales: pd.DataFrame) -> List[Dict]:
        """Category-level insights."""
        insights = []
        cat_perf = sales.groupby("category").agg(
            revenue=("revenue", "sum"),
            profit=("profit", "sum"),
            units=("units_sold", "sum"),
        )
        cat_perf["margin"] = cat_perf["profit"] / cat_perf["revenue"]

        best_margin = cat_perf["margin"].idxmax()
        worst_margin = cat_perf["margin"].idxmin()

        insights.append({
            "category": "category",
            "type": "comparison",
            "title": "Margin Leaders & Laggards",
            "description": f"{best_margin} has the highest margin ({cat_perf.loc[best_margin, 'margin']*100:.1f}%) while {worst_margin} has the lowest ({cat_perf.loc[worst_margin, 'margin']*100:.1f}%)",
            "impact": "neutral",
        })
        return insights

    def _channel_insights(self, sales: pd.DataFrame) -> List[Dict]:
        """Channel performance insights."""
        insights = []
        chan = sales.groupby("channel").agg(
            revenue=("revenue", "sum"),
            avg_price=("price", "mean"),
        )
        top_channel = chan["revenue"].idxmax()
        top_pct = chan.loc[top_channel, "revenue"] / chan["revenue"].sum() * 100

        insights.append({
            "category": "channel",
            "type": "observation",
            "title": "Dominant Sales Channel",
            "description": f"{top_channel} accounts for {top_pct:.1f}% of total revenue",
            "impact": "neutral",
        })
        return insights
