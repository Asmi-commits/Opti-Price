"""
Pydantic schemas for the pricing API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class PricingRequest(BaseModel):
    """Request body for price optimization."""
    product_id: str = Field(..., description="Product SKU identifier")
    current_price: float = Field(..., gt=0, description="Current selling price")
    current_demand: float = Field(..., ge=0, description="Current daily demand (units)")
    cost: float = Field(..., gt=0, description="Cost of goods")
    category: Optional[str] = Field(None, description="Product category")
    competitor_price: Optional[float] = Field(None, gt=0, description="Average competitor price")


class PricingResponse(BaseModel):
    """Response body with pricing recommendation."""
    product_id: str
    current_price: float
    recommended_price: float
    price_change_pct: float
    expected_demand: float
    expected_revenue: float
    expected_profit: float
    revenue_uplift_pct: float
    profit_uplift_pct: float
    confidence: str
    rationale: str


class BatchPricingRequest(BaseModel):
    """Batch pricing optimization request."""
    products: List[PricingRequest]
    objective: str = Field("profit", description="Optimization objective: 'profit' or 'revenue'")


class BatchPricingResponse(BaseModel):
    """Batch pricing response."""
    recommendations: List[PricingResponse]
    summary: dict


class DemandForecastRequest(BaseModel):
    """Request for demand forecast."""
    product_id: str
    price: float = Field(..., gt=0)
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    is_promotion: bool = False
    promotion_discount_pct: float = 0.0


class DemandForecastResponse(BaseModel):
    """Demand forecast response."""
    product_id: str
    date: str
    predicted_demand: float
    confidence_interval: dict


class PriceSimulationRequest(BaseModel):
    """Request for price sensitivity simulation."""
    product_id: str
    current_price: float = Field(..., gt=0)
    current_demand: float = Field(..., ge=0)
    cost: float = Field(..., gt=0)
    price_changes: List[float] = Field(
        default=[-0.20, -0.15, -0.10, -0.05, 0, 0.05, 0.10, 0.15, 0.20],
        description="List of percentage price changes to simulate"
    )
    category: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    models_loaded: dict
