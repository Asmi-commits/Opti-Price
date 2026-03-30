"""
Model evaluation: comprehensive evaluation pipeline for all models.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import json

from src.evaluation.metrics import regression_metrics, pricing_metrics, demand_forecast_by_segment
from src.utils.config import RESULTS_DIR
from src.utils.helpers import save_json
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelEvaluator:
    """Evaluate and compare models."""

    def __init__(self):
        self.results: Dict = {}

    def evaluate_demand_model(
        self,
        model_name: str,
        y_true: pd.Series,
        y_pred: np.ndarray,
        categories: Optional[pd.Series] = None,
    ) -> Dict:
        """Full evaluation of a demand forecasting model."""
        logger.info(f"Evaluating demand model: {model_name}")

        # Overall metrics
        overall = regression_metrics(y_true, y_pred)
        result = {"overall": overall}

        # By category
        if categories is not None:
            by_cat = demand_forecast_by_segment(y_true, y_pred, categories)
            result["by_category"] = by_cat.to_dict()

        # By demand level
        demand_bins = pd.cut(y_true, bins=[0, 10, 50, 100, float("inf")],
                             labels=["low", "medium", "high", "very_high"])
        by_demand = demand_forecast_by_segment(y_true, y_pred, demand_bins)
        result["by_demand_level"] = by_demand.to_dict()

        # Error distribution
        errors = y_true.values - y_pred
        result["error_distribution"] = {
            "mean": round(float(np.mean(errors)), 2),
            "std": round(float(np.std(errors)), 2),
            "p5": round(float(np.percentile(errors, 5)), 2),
            "p25": round(float(np.percentile(errors, 25)), 2),
            "p50": round(float(np.percentile(errors, 50)), 2),
            "p75": round(float(np.percentile(errors, 75)), 2),
            "p95": round(float(np.percentile(errors, 95)), 2),
        }

        self.results[model_name] = result
        logger.info(f"  Overall: MAE={overall['mae']}, RMSE={overall['rmse']}, R²={overall['r2']}")
        return result

    def evaluate_pricing_optimization(
        self,
        recommendations: pd.DataFrame,
    ) -> Dict:
        """Evaluate pricing optimization results."""
        logger.info("Evaluating pricing optimization...")
        metrics = pricing_metrics(recommendations)
        self.results["pricing_optimization"] = metrics
        return metrics

    def compare_models(self) -> pd.DataFrame:
        """Compare all evaluated models side by side."""
        rows = []
        for name, result in self.results.items():
            if "overall" in result:
                row = {"model": name}
                row.update(result["overall"])
                rows.append(row)
        if rows:
            return pd.DataFrame(rows).set_index("model").sort_values("rmse")
        return pd.DataFrame()

    def save_results(self, filepath: Optional[str] = None) -> None:
        """Save evaluation results to JSON."""
        fp = filepath or str(RESULTS_DIR / "model_metrics.json")
        # Convert any numpy types
        clean = json.loads(json.dumps(self.results, default=str))
        save_json(clean, fp)
<<<<<<< HEAD
        logger.info(f"Results saved to {fp}")
=======
        logger.info(f"Results saved to {fp}")
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
