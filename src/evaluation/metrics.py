"""
Evaluation metrics for demand forecasting and pricing models.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute comprehensive regression metrics."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    residuals = y_true - y_pred

    n = len(y_true)
    mae = np.mean(np.abs(residuals))
    mse = np.mean(residuals ** 2)
    rmse = np.sqrt(mse)

    # MAPE (avoid division by zero)
    nonzero = y_true != 0
    mape = np.mean(np.abs(residuals[nonzero] / y_true[nonzero])) * 100 if nonzero.any() else np.inf

    # Symmetric MAPE
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    smape = np.mean(np.abs(residuals) / np.maximum(denom, 1e-8)) * 100

    # R²
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - ss_res / max(ss_tot, 1e-8)

    # Adjusted R² (assuming no extra features info; placeholder)
    adj_r2 = r2  # Would need p (num features) to calculate properly

    return {
        "n_samples": n,
        "mae": round(mae, 4),
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "mape": round(mape, 2),
        "smape": round(smape, 2),
        "r2": round(r2, 4),
        "median_ae": round(np.median(np.abs(residuals)), 4),
        "max_error": round(np.max(np.abs(residuals)), 4),
        "mean_residual": round(np.mean(residuals), 4),
        "std_residual": round(np.std(residuals), 4),
    }


def pricing_metrics(
    recommendations: pd.DataFrame,
) -> Dict[str, float]:
    """Evaluate pricing optimization results."""
    return {
        "n_products": len(recommendations),
        "avg_price_change_pct": round(recommendations["price_change_pct"].mean(), 2),
        "median_price_change_pct": round(recommendations["price_change_pct"].median(), 2),
        "total_expected_revenue": round(recommendations["expected_revenue"].sum(), 2),
        "total_current_revenue": round(recommendations["current_revenue"].sum(), 2),
        "total_revenue_uplift": round(
            recommendations["expected_revenue"].sum() - recommendations["current_revenue"].sum(), 2
        ),
        "total_expected_profit": round(recommendations["expected_profit"].sum(), 2),
        "total_current_profit": round(recommendations["current_profit"].sum(), 2),
        "total_profit_uplift": round(
            recommendations["expected_profit"].sum() - recommendations["current_profit"].sum(), 2
        ),
        "pct_price_increase": round((recommendations["price_change_pct"] > 1).mean() * 100, 1),
        "pct_price_decrease": round((recommendations["price_change_pct"] < -1).mean() * 100, 1),
        "pct_price_hold": round(
            (recommendations["price_change_pct"].between(-1, 1)).mean() * 100, 1
        ),
        "avg_confidence_score": round(
            recommendations["confidence"].map({"high": 3, "medium": 2, "low": 1}).mean(), 2
        ),
    }


def demand_forecast_by_segment(
    y_true: pd.Series,
    y_pred: np.ndarray,
    segments: pd.Series,
) -> pd.DataFrame:
    """Compute metrics broken down by segment (e.g., category)."""
    results = []
    for seg in segments.unique():
        mask = segments == seg
        if mask.sum() < 5:
            continue
        metrics = regression_metrics(y_true[mask], y_pred[mask])
        metrics["segment"] = seg
        results.append(metrics)
<<<<<<< HEAD
    return pd.DataFrame(results).set_index("segment").sort_values("mae")
=======
    return pd.DataFrame(results).set_index("segment").sort_values("mae")
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
