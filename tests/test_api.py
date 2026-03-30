"""Tests for the API endpoints."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.api.schemas import (
    PricingRequest, PricingResponse, BatchPricingRequest,
    DemandForecastRequest, PriceSimulationRequest,
)


class TestSchemas:
    def test_pricing_request_valid(self):
        req = PricingRequest(
            product_id="SKU-1001",
            current_price=99.99,
            current_demand=50,
            cost=45.00,
            category="Electronics",
        )
        assert req.product_id == "SKU-1001"
        assert req.current_price == 99.99

    def test_pricing_request_rejects_negative_price(self):
        with pytest.raises(Exception):
            PricingRequest(
                product_id="SKU-1001",
                current_price=-10,
                current_demand=50,
                cost=45.00,
            )

    def test_batch_request(self):
        products = [
            PricingRequest(product_id=f"SKU-{i}", current_price=50+i*10,
                           current_demand=30, cost=25+i*5)
            for i in range(3)
        ]
        batch = BatchPricingRequest(products=products, objective="profit")
        assert len(batch.products) == 3
        assert batch.objective == "profit"

    def test_simulation_request_defaults(self):
        req = PriceSimulationRequest(
            product_id="SKU-1001",
            current_price=100,
            current_demand=50,
            cost=60,
        )
        assert len(req.price_changes) == 9  # Default grid
        assert 0 in req.price_changes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
