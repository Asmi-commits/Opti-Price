"""
FastAPI application for the Dynamic Pricing Optimization service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routes import router, init_models
from src.models.elasticity_model import ElasticityModel
from src.data_pipeline.ingestion import DataIngestion
from src.utils.config import API_HOST, API_PORT, API_VERSION
from src.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup."""
    logger.info("Loading models...")
    try:
        ingestion = DataIngestion()
        sales = ingestion.load_sales()
        elast = ElasticityModel()
        elast.estimate_by_category(sales)
        elast.estimate_by_product(sales, min_observations=60)
        init_models(elast)
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Dynamic Pricing Optimization API",
    description="ML-powered pricing recommendations for e-commerce products",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "Dynamic Pricing Optimization",
        "version": "1.0.0",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
