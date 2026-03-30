"""
Price elasticity estimation: log-log demand models, category-level and product-level.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.metrics import r2_score

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ElasticityModel:
    """
    Estimate price elasticity of demand using log-log regression.
    
    Model: ln(Q) = α + ε·ln(P) + β·X + error
    Where ε is the price elasticity coefficient.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.product_elasticities: Dict[str, Dict] = {}
        self.category_elasticities: Dict[str, Dict] = {}
        self.overall_elasticity: Optional[Dict] = None

    def estimate_overall(self, df: pd.DataFrame) -> Dict:
        """Estimate overall price elasticity across all products."""
        logger.info("Estimating overall price elasticity...")
        result = self._fit_log_log(df)
        self.overall_elasticity = result
        logger.info(f"Overall elasticity: {result['elasticity']:.4f} (R²={result['r2']:.4f})")
        return result

    def estimate_by_category(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Estimate elasticity per product category."""
        logger.info("Estimating category-level elasticities...")
        for cat in df["category"].unique():
            cat_data = df[df["category"] == cat]
            if len(cat_data) < 100:
                logger.warning(f"Insufficient data for {cat} ({len(cat_data)} rows)")
                continue
            result = self._fit_log_log(cat_data)
            self.category_elasticities[cat] = result
            logger.info(f"  {cat}: ε={result['elasticity']:.4f}, R²={result['r2']:.4f}")
        return self.category_elasticities

    def estimate_by_product(
        self, df: pd.DataFrame, min_observations: int = 60
    ) -> Dict[str, Dict]:
        """Estimate elasticity per individual product."""
        logger.info("Estimating product-level elasticities...")
        products = df["product_id"].unique()
        estimated, skipped = 0, 0

        for pid in products:
            prod_data = df[df["product_id"] == pid]
            if len(prod_data) < min_observations:
                skipped += 1
                continue
            result = self._fit_log_log(prod_data)
            self.product_elasticities[pid] = result
            estimated += 1

        logger.info(f"Estimated {estimated} product elasticities, skipped {skipped}")
        return self.product_elasticities

    def get_elasticity(self, product_id: Optional[str] = None, category: Optional[str] = None) -> float:
        """Get the best available elasticity estimate for a product."""
        if product_id and product_id in self.product_elasticities:
            return self.product_elasticities[product_id]["elasticity"]
        if category and category in self.category_elasticities:
            return self.category_elasticities[category]["elasticity"]
        if self.overall_elasticity:
            return self.overall_elasticity["elasticity"]
        return -1.0  # Default assumption

    def predict_demand_at_price(
        self, current_price: float, current_demand: float,
        new_price: float, elasticity: float,
    ) -> float:
        """Predict demand at a new price given current demand and elasticity."""
        if current_price <= 0 or new_price <= 0:
            return current_demand
        price_ratio = new_price / current_price
        demand_multiplier = price_ratio ** elasticity
        return max(0, current_demand * demand_multiplier)

    def get_summary_df(self) -> pd.DataFrame:
        """Return elasticity estimates as a DataFrame."""
        rows = []
        for pid, result in self.product_elasticities.items():
            rows.append({
                "product_id": pid,
                "level": "product",
                "elasticity": result["elasticity"],
                "r2": result["r2"],
                "n_obs": result["n_obs"],
                "std_error": result.get("std_error", np.nan),
            })
        for cat, result in self.category_elasticities.items():
            rows.append({
                "product_id": cat,
                "level": "category",
                "elasticity": result["elasticity"],
                "r2": result["r2"],
                "n_obs": result["n_obs"],
                "std_error": result.get("std_error", np.nan),
            })
        return pd.DataFrame(rows)

    def _fit_log_log(self, df: pd.DataFrame) -> Dict:
        """Fit a log-log demand model: ln(Q) = α + ε·ln(P) + controls."""
        data = df[["price", "units_sold"]].dropna()
        data = data[(data["price"] > 0) & (data["units_sold"] > 0)]

        if len(data) < 10:
            return {"elasticity": np.nan, "r2": np.nan, "n_obs": len(data)}

        log_price = np.log(data["price"]).values.reshape(-1, 1)
        log_demand = np.log(data["units_sold"]).values

        # Add controls if available
        controls = []
        for col in ["is_weekend", "is_promotion", "is_holiday", "month_sin", "month_cos"]:
            if col in df.columns:
                ctrl = df.loc[data.index, col].values
                if not np.all(np.isnan(ctrl)):
                    controls.append(ctrl)

        if controls:
            X = np.column_stack([log_price] + controls)
        else:
            X = log_price

        model = Ridge(alpha=self.alpha)
        model.fit(X, log_demand)
        preds = model.predict(X)

        elasticity = model.coef_[0]
        residuals = log_demand - preds
        n = len(data)
        p = X.shape[1]
        mse = np.sum(residuals ** 2) / max(n - p - 1, 1)
        XtX_inv = np.linalg.pinv(X.T @ X)
        se = np.sqrt(mse * np.diag(XtX_inv))

        return {
            "elasticity": round(elasticity, 4),
            "intercept": round(model.intercept_, 4),
            "r2": round(r2_score(log_demand, preds), 4),
            "n_obs": n,
            "std_error": round(se[0], 4) if len(se) > 0 else np.nan,
            "coefficients": {f"control_{i}": round(c, 4) for i, c in enumerate(model.coef_[1:])},
<<<<<<< HEAD
        }
=======
        }
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
