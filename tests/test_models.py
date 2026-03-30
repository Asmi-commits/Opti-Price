"""Tests for model modules."""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.models.elasticity_model import ElasticityModel
from src.models.pricing_optimizer import PricingOptimizer, PricingConstraints
from src.evaluation.metrics import regression_metrics


class TestElasticityModel:
    def setup_method(self):
        self.model = ElasticityModel(alpha=1.0)

    def test_predict_demand_at_price(self):
        # Price goes up, demand should go down for negative elasticity
        demand = self.model.predict_demand_at_price(
            current_price=100, current_demand=50,
            new_price=110, elasticity=-1.5,
        )
        assert demand < 50  # Higher price → lower demand

    def test_predict_demand_price_decrease(self):
        demand = self.model.predict_demand_at_price(
            current_price=100, current_demand=50,
            new_price=90, elasticity=-1.5,
        )
        assert demand > 50  # Lower price → higher demand

    def test_unit_elastic(self):
        # At unit elasticity, 10% price increase → ~10% demand decrease
        demand = self.model.predict_demand_at_price(
            current_price=100, current_demand=100,
            new_price=110, elasticity=-1.0,
        )
        assert 88 < demand < 92  # Approximately 90


class TestPricingOptimizer:
    def setup_method(self):
        self.elast_model = ElasticityModel()
        # Set a known elasticity
        self.elast_model.category_elasticities["TestCat"] = {
            "elasticity": -1.5, "r2": 0.5, "n_obs": 100,
        }
        self.optimizer = PricingOptimizer(
            self.elast_model, objective="profit",
            constraints=PricingConstraints(max_price_change_pct=0.20),
        )

    def test_optimize_product(self):
        rec = self.optimizer.optimize_product(
            product_id="TEST-001",
            current_price=100,
            current_demand=50,
            cost=60,
            category="TestCat",
        )
        assert rec.recommended_price > 0
        assert rec.expected_demand >= 0
        assert abs(rec.price_change_pct) <= 20.1  # Within constraints
        assert rec.confidence in ["high", "medium", "low"]

    def test_optimizer_respects_min_margin(self):
        rec = self.optimizer.optimize_product(
            product_id="TEST-002",
            current_price=65,
            current_demand=100,
            cost=60,
            category="TestCat",
        )
        # Should not recommend price below cost + margin
        assert rec.recommended_price >= 60 * 1.05


class TestRegressionMetrics:
    def test_perfect_predictions(self):
        y_true = np.array([10, 20, 30, 40, 50])
        y_pred = np.array([10, 20, 30, 40, 50])
        metrics = regression_metrics(y_true, y_pred)
        assert metrics["mae"] == 0
        assert metrics["rmse"] == 0
        assert metrics["r2"] == 1.0

    def test_imperfect_predictions(self):
        y_true = np.array([10, 20, 30, 40, 50])
        y_pred = np.array([12, 18, 33, 37, 52])
        metrics = regression_metrics(y_true, y_pred)
        assert metrics["mae"] > 0
        assert 0 < metrics["r2"] < 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
