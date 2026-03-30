"""
General helper functions used across the project.
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


def load_csv(filepath: Union[str, Path], parse_dates: Optional[List[str]] = None, **kwargs) -> pd.DataFrame:
    """Load a CSV file with optional date parsing."""
    fp = Path(filepath)
    if not fp.exists():
        raise FileNotFoundError(f"File not found: {fp}")
    return pd.read_csv(fp, parse_dates=parse_dates or [], **kwargs)


def save_csv(df: pd.DataFrame, filepath: Union[str, Path], index: bool = False) -> None:
    """Save a DataFrame to CSV, creating directories if needed."""
    fp = Path(filepath)
    fp.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(fp, index=index)


def save_json(data: Any, filepath: Union[str, Path]) -> None:
    """Save data to a JSON file."""
    fp = Path(filepath)
    fp.parent.mkdir(parents=True, exist_ok=True)
    with open(fp, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(filepath: Union[str, Path]) -> Any:
    """Load data from a JSON file."""
    with open(filepath, "r") as f:
        return json.load(f)


def calculate_margin(price: float, cost: float) -> float:
    """Calculate profit margin percentage."""
    if price == 0:
        return 0.0
    return (price - cost) / price


def calculate_price_change(current: float, previous: float) -> float:
    """Calculate percentage price change."""
    if previous == 0:
        return 0.0
    return (current - previous) / previous


def clip_price(price: float, min_price: float, max_price: float) -> float:
    """Clip price within allowed bounds."""
    return max(min_price, min(price, max_price))


def get_date_features(date: pd.Timestamp) -> Dict[str, Any]:
    """Extract date-based features from a timestamp."""
    return {
        "day_of_week": date.dayofweek,
        "day_of_month": date.day,
        "week_of_year": date.isocalendar()[1],
        "month": date.month,
        "quarter": date.quarter,
        "year": date.year,
        "is_weekend": date.dayofweek >= 5,
        "is_month_start": date.is_month_start,
        "is_month_end": date.is_month_end,
    }


def weighted_average(values: np.ndarray, weights: np.ndarray) -> float:
    """Calculate weighted average, handling edge cases."""
    if len(values) == 0 or weights.sum() == 0:
        return 0.0
    return np.average(values, weights=weights)


def format_currency(value: float, symbol: str = "$") -> str:
    """Format a number as currency."""
    return f"{symbol}{value:,.2f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a number as percentage."""
    return f"{value * 100:.{decimals}f}%"


def timestamp_now() -> str:
    """Return current timestamp as ISO string."""
<<<<<<< HEAD
    return datetime.now().isoformat()
=======
    return datetime.now().isoformat()
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
