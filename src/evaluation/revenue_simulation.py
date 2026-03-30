"""
Revenue simulation: project financial impact of pricing changes over time.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

from src.models.elasticity_model import ElasticityModel
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RevenueSimulator:
    """Simulate revenue/profit impact of pricing strategies."""

    def __init__(self, elasticity_model: ElasticityModel):
        self.elasticity_model = elasticity_model

    def simulate_price_change(
        self,
        product_id: str,
        current_price: float,
        current_demand: float,
        cost: float,
        price_changes: List[float],
        category: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Simulate revenue/profit at different price points.
        
        price_changes: list of % changes, e.g. [-0.20, -0.10, 0, 0.10, 0.20]
        """
        elasticity = self.elasticity_model.get_elasticity(product_id, category)
        results = []

        for pct_change in price_changes:
            new_price = current_price * (1 + pct_change)
            new_demand = self.elasticity_model.predict_demand_at_price(
                current_price, current_demand, new_price, elasticity
            )
            revenue = new_price * new_demand
            profit = (new_price - cost) * new_demand

            results.append({
                "price_change_pct": round(pct_change * 100, 1),
                "price": round(new_price, 2),
                "predicted_demand": round(new_demand, 1),
                "revenue": round(revenue, 2),
                "profit": round(profit, 2),
                "margin_pct": round((new_price - cost) / new_price * 100, 1),
                "revenue_vs_current": round(revenue - current_price * current_demand, 2),
                "profit_vs_current": round(profit - (current_price - cost) * current_demand, 2),
            })

        return pd.DataFrame(results)

    def simulate_portfolio_scenario(
        self,
        portfolio: pd.DataFrame,
        scenario_name: str,
        price_adjustment_fn,
    ) -> Dict:
        """
        Apply a pricing scenario to the whole portfolio.
        
        price_adjustment_fn: callable(row) -> new_price
        """
        logger.info(f"Running scenario: {scenario_name}")

        total_current_rev = 0
        total_new_rev = 0
        total_current_profit = 0
        total_new_profit = 0
        product_results = []

        for _, row in portfolio.iterrows():
            current_price = row["current_price"]
            current_demand = row["current_demand"]
            cost = row["cost"]
            new_price = price_adjustment_fn(row)

            elasticity = self.elasticity_model.get_elasticity(
                row["product_id"], row.get("category")
            )
            new_demand = self.elasticity_model.predict_demand_at_price(
                current_price, current_demand, new_price, elasticity
            )

            curr_rev = current_price * current_demand
            new_rev = new_price * new_demand
            curr_profit = (current_price - cost) * current_demand
            new_profit = (new_price - cost) * new_demand

            total_current_rev += curr_rev
            total_new_rev += new_rev
            total_current_profit += curr_profit
            total_new_profit += new_profit

            product_results.append({
                "product_id": row["product_id"],
                "current_price": current_price,
                "new_price": round(new_price, 2),
                "current_demand": current_demand,
                "new_demand": round(new_demand, 1),
                "revenue_change": round(new_rev - curr_rev, 2),
                "profit_change": round(new_profit - curr_profit, 2),
            })

        summary = {
            "scenario": scenario_name,
            "total_current_revenue": round(total_current_rev, 2),
            "total_new_revenue": round(total_new_rev, 2),
            "revenue_change": round(total_new_rev - total_current_rev, 2),
            "revenue_change_pct": round((total_new_rev - total_current_rev) / max(total_current_rev, 1) * 100, 2),
            "total_current_profit": round(total_current_profit, 2),
            "total_new_profit": round(total_new_profit, 2),
            "profit_change": round(total_new_profit - total_current_profit, 2),
            "profit_change_pct": round((total_new_profit - total_current_profit) / max(total_current_profit, 1) * 100, 2),
            "product_details": pd.DataFrame(product_results),
        }
        logger.info(f"  Revenue change: {summary['revenue_change_pct']:+.1f}%, "
                     f"Profit change: {summary['profit_change_pct']:+.1f}%")
        return summary

    def compare_scenarios(
        self, portfolio: pd.DataFrame, scenarios: Dict[str, callable]
    ) -> pd.DataFrame:
        """Run multiple pricing scenarios and compare."""
        results = []
        for name, fn in scenarios.items():
            summary = self.simulate_portfolio_scenario(portfolio, name, fn)
            results.append({
                "scenario": name,
                "revenue_change_pct": summary["revenue_change_pct"],
                "profit_change_pct": summary["profit_change_pct"],
                "total_new_revenue": summary["total_new_revenue"],
                "total_new_profit": summary["total_new_profit"],
            })
<<<<<<< HEAD
        return pd.DataFrame(results).sort_values("profit_change_pct", ascending=False)
=======
        return pd.DataFrame(results).sort_values("profit_change_pct", ascending=False)
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
