"""Tests for feature engineering modules."""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.time_features import TimeFeatureBuilder
from src.features.pricing_features import PricingFeatureBuilder
from src.features.inventory_features import InventoryFeatureBuilder


class TestTimeFeatures:
    def setup_method(self):
        self.builder = TimeFeatureBuilder()
        self.df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=100, freq="D"),
            "product_id": ["P1"] * 100,
            "price": np.random.uniform(10, 50, 100),
        })

    def test_calendar_features(self):
        result = self.builder.build(self.df)
        assert "day_of_week_num" in result.columns
        assert "month" in result.columns
        assert "is_weekend" in result.columns
        assert result["day_of_week_num"].between(0, 6).all()
        assert result["month"].between(1, 12).all()

    def test_cyclical_encoding(self):
        result = self.builder.build(self.df)
        assert "dow_sin" in result.columns
        assert "month_cos" in result.columns
        assert result["dow_sin"].between(-1, 1).all()

    def test_trend_features(self):
        result = self.builder.build(self.df)
        assert "days_since_start" in result.columns
        assert result["days_since_start"].iloc[0] == 0
        assert result["days_since_start"].iloc[-1] == 99


class TestPricingFeatures:
    def setup_method(self):
        self.builder = PricingFeatureBuilder()

    def test_price_ratios(self):
        df = pd.DataFrame({
            "product_id": ["P1"] * 10,
            "price": [100] * 10,
            "base_price": [120] * 10,
            "cost": [60] * 10,
        })
        result = self.builder._price_ratios(df)
        assert "price_to_base_ratio" in result.columns
        assert "discount_depth" in result.columns
        assert "margin_pct" in result.columns
        assert np.isclose(result["price_to_base_ratio"].iloc[0], 100/120, atol=0.01)


class TestInventoryFeatures:
    def setup_method(self):
        self.builder = InventoryFeatureBuilder()

    def test_stock_status(self):
        df = pd.DataFrame({
            "product_id": ["P1"] * 5,
            "stock_level": [0, 10, 100, 500, 1000],
            "days_of_supply": [0, 3, 10, 30, 60],
        })
        result = self.builder._stock_status(df)
        assert "low_stock_flag" in result.columns
        assert "out_of_stock_flag" in result.columns
        assert result["out_of_stock_flag"].iloc[0] == 1
        assert result["low_stock_flag"].iloc[1] == 1  # 3 days < 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
