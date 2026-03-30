"""
Pricing optimizer: find revenue/profit-maximizing prices given demand model & constraints.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from src.models.elasticity_model import ElasticityModel
from src.utils.config import MIN_MARGIN_PCT, MAX_PRICE_CHANGE_PCT, PRICE_STEP_SIZE
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PricingConstraints:
    """Business constraints on pricing decisions."""
    min_margin_pct: float = MIN_MARGIN_PCT
    max_price_change_pct: float = MAX_PRICE_CHANGE_PCT
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price_step: float = PRICE_STEP_SIZE
    competitor_match: bool = False  # Whether to match competitor prices
    max_competitor_premium_pct: float = 0.10  # Max % above competitor


@dataclass
class PricingRecommendation:
    """Output of pricing optimization."""
    product_id: str
    current_price: float
    recommended_price: float
    price_change_pct: float
    expected_demand: float
    expected_revenue: float
    expected_profit: float
    current_revenue: float
    current_profit: float
    revenue_uplift_pct: float
    profit_uplift_pct: float
    elasticity_used: float
    confidence: str  # "high", "medium", "low"
    rationale: str


class PricingOptimizer:
    """
    Optimize product prices to maximize revenue or profit,
    subject to business constraints.
    """

    def __init__(
        self,
        elasticity_model: ElasticityModel,
        objective: str = "profit",
        constraints: Optional[PricingConstraints] = None,
    ):
        self.elasticity_model = elasticity_model
        self.objective = objective
        self.constraints = constraints or PricingConstraints()

    def optimize_product(
        self,
        product_id: str,
        current_price: float,
        current_demand: float,
        cost: float,
        category: Optional[str] = None,
        competitor_price: Optional[float] = None,
    ) -> PricingRecommendation:
        """Find the optimal price for a single product."""
        elasticity = self.elasticity_model.get_elasticity(product_id, category)

        # Define price search range
        min_price = max(
            cost * (1 + self.constraints.min_margin_pct),
            current_price * (1 - self.constraints.max_price_change_pct),
        )
        max_price = current_price * (1 + self.constraints.max_price_change_pct)

        if self.constraints.min_price:
            min_price = max(min_price, self.constraints.min_price)
        if self.constraints.max_price:
            max_price = min(max_price, self.constraints.max_price)

        # Competitor constraint
        if competitor_price and self.constraints.competitor_match:
            max_price = min(
                max_price,
                competitor_price * (1 + self.constraints.max_competitor_premium_pct),
            )

        # Grid search
        best_price = current_price
        best_objective = float("-inf")

        price_range = np.arange(
            min_price, max_price + 0.01,
            current_price * self.constraints.price_step
        )

        for candidate_price in price_range:
            demand = self.elasticity_model.predict_demand_at_price(
                current_price, current_demand, candidate_price, elasticity
            )
            revenue = candidate_price * demand
            profit = (candidate_price - cost) * demand

            obj_value = profit if self.objective == "profit" else revenue

            if obj_value > best_objective:
                best_objective = obj_value
                best_price = candidate_price

        # Calculate metrics at optimal price
        opt_demand = self.elasticity_model.predict_demand_at_price(
            current_price, current_demand, best_price, elasticity
        )
        opt_revenue = best_price * opt_demand
        opt_profit = (best_price - cost) * opt_demand
        curr_revenue = current_price * current_demand
        curr_profit = (current_price - cost) * current_demand

        # Confidence based on elasticity estimation quality
        if product_id in self.elasticity_model.product_elasticities:
            r2 = self.elasticity_model.product_elasticities[product_id].get("r2", 0)
            confidence = "high" if r2 > 0.3 else "medium" if r2 > 0.1 else "low"
        else:
            confidence = "low"

        price_change = (best_price - current_price) / current_price

        # Rationale
        if abs(price_change) < 0.01:
            rationale = "Current price is near-optimal"
        elif price_change > 0:
            rationale = f"Inelastic demand (ε={elasticity:.2f}) supports a {price_change*100:.1f}% price increase"
        else:
            rationale = f"Elastic demand (ε={elasticity:.2f}) suggests a {abs(price_change)*100:.1f}% price decrease to drive volume"

        return PricingRecommendation(
            product_id=product_id,
            current_price=round(current_price, 2),
            recommended_price=round(best_price, 2),
            price_change_pct=round(price_change * 100, 2),
            expected_demand=round(opt_demand, 1),
            expected_revenue=round(opt_revenue, 2),
            expected_profit=round(opt_profit, 2),
            current_revenue=round(curr_revenue, 2),
            current_profit=round(curr_profit, 2),
            revenue_uplift_pct=round((opt_revenue - curr_revenue) / max(curr_revenue, 1) * 100, 2),
            profit_uplift_pct=round((opt_profit - curr_profit) / max(curr_profit, 1) * 100, 2),
            elasticity_used=elasticity,
            confidence=confidence,
            rationale=rationale,
        )

    def optimize_portfolio(
        self,
        products_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Optimize prices across an entire product portfolio."""
        logger.info(f"Optimizing prices for {len(products_df):,} products...")

        recommendations = []
        for _, row in products_df.iterrows():
            rec = self.optimize_product(
                product_id=row["product_id"],
                current_price=row["current_price"],
                current_demand=row["current_demand"],
                cost=row["cost"],
                category=row.get("category"),
                competitor_price=row.get("avg_competitor_price"),
            )
            recommendations.append(vars(rec))

        results = pd.DataFrame(recommendations)

        # Summary
        total_rev_uplift = results["expected_revenue"].sum() - results["current_revenue"].sum()
        total_prof_uplift = results["expected_profit"].sum() - results["current_profit"].sum()
        n_increase = (results["price_change_pct"] > 1).sum()
        n_decrease = (results["price_change_pct"] < -1).sum()
        n_hold = len(results) - n_increase - n_decrease

        logger.info(f"Portfolio optimization complete:")
        logger.info(f"  Price increases: {n_increase}, Decreases: {n_decrease}, Hold: {n_hold}")
        logger.info(f"  Expected revenue uplift: ${total_rev_uplift:,.2f}")
        logger.info(f"  Expected profit uplift: ${total_prof_uplift:,.2f}")

<<<<<<< HEAD
        return results
=======
        return results
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
