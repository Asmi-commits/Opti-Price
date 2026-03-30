"""
API route handlers for the pricing optimization service.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import pandas as pd

from src.api.schemas import (
    PricingRequest, PricingResponse, BatchPricingRequest, BatchPricingResponse,
    DemandForecastRequest, DemandForecastResponse,
    PriceSimulationRequest, HealthResponse,
)
from src.models.elasticity_model import ElasticityModel
from src.models.pricing_optimizer import PricingOptimizer, PricingConstraints
from src.evaluation.revenue_simulation import RevenueSimulator
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pricing"])

# These would be initialized at startup
elasticity_model: Optional[ElasticityModel] = None
pricing_optimizer: Optional[PricingOptimizer] = None
revenue_simulator: Optional[RevenueSimulator] = None


def init_models(elast_model: ElasticityModel):
    """Initialize models for the API (called at startup)."""
    global elasticity_model, pricing_optimizer, revenue_simulator
    elasticity_model = elast_model
    pricing_optimizer = PricingOptimizer(elast_model, objective="profit")
    revenue_simulator = RevenueSimulator(elast_model)
    logger.info("API models initialized")


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        models_loaded={
            "elasticity_model": elasticity_model is not None,
            "pricing_optimizer": pricing_optimizer is not None,
        },
    )


@router.post("/optimize", response_model=PricingResponse)
async def optimize_price(request: PricingRequest):
    """Get optimal price for a single product."""
    if pricing_optimizer is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    rec = pricing_optimizer.optimize_product(
        product_id=request.product_id,
        current_price=request.current_price,
        current_demand=request.current_demand,
        cost=request.cost,
        category=request.category,
        competitor_price=request.competitor_price,
    )

    return PricingResponse(
        product_id=rec.product_id,
        current_price=rec.current_price,
        recommended_price=rec.recommended_price,
        price_change_pct=rec.price_change_pct,
        expected_demand=rec.expected_demand,
        expected_revenue=rec.expected_revenue,
        expected_profit=rec.expected_profit,
        revenue_uplift_pct=rec.revenue_uplift_pct,
        profit_uplift_pct=rec.profit_uplift_pct,
        confidence=rec.confidence,
        rationale=rec.rationale,
    )


@router.post("/optimize/batch", response_model=BatchPricingResponse)
async def optimize_batch(request: BatchPricingRequest):
    """Optimize prices for multiple products."""
    if pricing_optimizer is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    products_df = pd.DataFrame([p.dict() for p in request.products])
    products_df.rename(columns={"competitor_price": "avg_competitor_price"}, inplace=True)

    results = pricing_optimizer.optimize_portfolio(products_df)

    recommendations = [
        PricingResponse(**row.to_dict())
        for _, row in results.iterrows()
    ]

    summary = {
        "total_products": len(recommendations),
        "avg_price_change": round(results["price_change_pct"].mean(), 2),
        "total_revenue_uplift": round(
            results["expected_revenue"].sum() - results["current_revenue"].sum(), 2
        ),
        "total_profit_uplift": round(
            results["expected_profit"].sum() - results["current_profit"].sum(), 2
        ),
    }

    return BatchPricingResponse(recommendations=recommendations, summary=summary)


@router.post("/simulate")
async def simulate_prices(request: PriceSimulationRequest):
    """Simulate demand/revenue at different price points."""
    if revenue_simulator is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    results = revenue_simulator.simulate_price_change(
        product_id=request.product_id,
        current_price=request.current_price,
        current_demand=request.current_demand,
        cost=request.cost,
        price_changes=request.price_changes,
        category=request.category,
    )
    return results.to_dict(orient="records")


@router.get("/elasticity/{product_id}")
async def get_elasticity(product_id: str, category: Optional[str] = None):
    """Get price elasticity estimate for a product."""
    if elasticity_model is None:
        raise HTTPException(status_code=503, detail="Models not loaded")

    elasticity = elasticity_model.get_elasticity(product_id, category)
    return {
        "product_id": product_id,
        "elasticity": elasticity,
        "interpretation": "elastic" if elasticity < -1 else "inelastic" if elasticity > -1 else "unit elastic",
    }
