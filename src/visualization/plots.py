"""
Plotting functions for demand, pricing, and business analysis.
Uses matplotlib/seaborn for static plots.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from pathlib import Path

# Style configuration
plt.rcParams.update({
    "figure.figsize": (12, 6),
    "figure.dpi": 120,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.size": 11,
})
PALETTE = sns.color_palette("husl", 10)


def plot_demand_vs_price(
    df: pd.DataFrame,
    product_id: Optional[str] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Scatter plot of demand vs price, optionally for a single product."""
    data = df[df["product_id"] == product_id] if product_id else df.sample(min(5000, len(df)))
    fig, ax = plt.subplots()
    ax.scatter(data["price"], data["units_sold"], alpha=0.3, s=10, c=PALETTE[0])
    ax.set_xlabel("Price")
    ax.set_ylabel("Units Sold")
    ax.set_title(f"Demand vs Price{f' ({product_id})' if product_id else ''}")
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig


def plot_revenue_time_series(
    df: pd.DataFrame,
    freq: str = "W",
    by_category: bool = False,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Revenue over time, optionally broken down by category."""
    fig, ax = plt.subplots(figsize=(14, 6))
    df["date"] = pd.to_datetime(df["date"])

    if by_category:
        for i, (cat, group) in enumerate(df.groupby("category")):
            agg = group.set_index("date")["revenue"].resample(freq).sum()
            ax.plot(agg.index, agg.values, label=cat, color=PALETTE[i % len(PALETTE)], linewidth=1.5)
        ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=9)
    else:
        agg = df.set_index("date")["revenue"].resample(freq).sum()
        ax.plot(agg.index, agg.values, color=PALETTE[0], linewidth=2)
        ax.fill_between(agg.index, agg.values, alpha=0.1, color=PALETTE[0])

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_ylabel("Revenue ($)")
    ax.set_title("Revenue Over Time")
    fig.autofmt_xdate()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig


def plot_price_distribution(
    df: pd.DataFrame,
    by_category: bool = True,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Distribution of prices, optionally by category."""
    fig, ax = plt.subplots(figsize=(12, 6))
    if by_category:
        categories = df["category"].unique()
        for i, cat in enumerate(categories):
            subset = df[df["category"] == cat]["price"]
            ax.hist(subset, bins=50, alpha=0.5, label=cat, color=PALETTE[i % len(PALETTE)])
        ax.legend(fontsize=9)
    else:
        ax.hist(df["price"], bins=100, color=PALETTE[0], alpha=0.7, edgecolor="white")
    ax.set_xlabel("Price ($)")
    ax.set_ylabel("Frequency")
    ax.set_title("Price Distribution")
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig


def plot_elasticity_by_category(
    elasticities: pd.DataFrame,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Bar chart of elasticity estimates by category."""
    cat_data = elasticities[elasticities["level"] == "category"].sort_values("elasticity")
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [PALETTE[2] if e < -1 else PALETTE[0] for e in cat_data["elasticity"]]
    ax.barh(cat_data["product_id"], cat_data["elasticity"], color=colors, edgecolor="white")
    ax.axvline(x=-1, color="gray", linestyle="--", alpha=0.5, label="Unit elastic")
    ax.set_xlabel("Price Elasticity of Demand")
    ax.set_title("Price Elasticity by Category")
    ax.legend()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig


def plot_optimization_results(
    recommendations: pd.DataFrame,
    top_n: int = 20,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Visualize pricing optimization recommendations."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Price change distribution
    axes[0].hist(recommendations["price_change_pct"], bins=30, color=PALETTE[0],
                 alpha=0.7, edgecolor="white")
    axes[0].axvline(x=0, color="red", linestyle="--", alpha=0.5)
    axes[0].set_xlabel("Recommended Price Change (%)")
    axes[0].set_ylabel("Number of Products")
    axes[0].set_title("Distribution of Price Changes")

    # Top profit uplift opportunities
    top = recommendations.nlargest(top_n, "profit_uplift_pct")
    axes[1].barh(range(len(top)), top["profit_uplift_pct"], color=PALETTE[3], edgecolor="white")
    axes[1].set_yticks(range(len(top)))
    axes[1].set_yticklabels(top["product_id"], fontsize=8)
    axes[1].set_xlabel("Expected Profit Uplift (%)")
    axes[1].set_title(f"Top {top_n} Profit Uplift Opportunities")

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig


def plot_forecast_vs_actual(
    dates: pd.Series,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    title: str = "Demand Forecast vs Actual",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot predicted vs actual demand over time."""
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(dates, y_true, label="Actual", color=PALETTE[0], alpha=0.7, linewidth=1)
    ax.plot(dates, y_pred, label="Predicted", color=PALETTE[2], alpha=0.7, linewidth=1, linestyle="--")
    ax.fill_between(dates, y_true, y_pred, alpha=0.1, color=PALETTE[4])
    ax.legend()
    ax.set_ylabel("Units Sold")
    ax.set_title(title)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    fig.autofmt_xdate()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight")
    return fig
