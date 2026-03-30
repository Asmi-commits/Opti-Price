"""
Main entry point: run the full dynamic pricing pipeline end-to-end.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_pipeline.ingestion import DataIngestion
from src.data_pipeline.cleaning import DataCleaner
from src.data_pipeline.transformation import DataTransformer
from src.data_pipeline.validation import DataValidator
from src.features.build_features import FeatureBuilder
from src.models.demand_forecast import DemandForecaster
from src.models.elasticity_model import ElasticityModel
from src.models.pricing_optimizer import PricingOptimizer, PricingConstraints
from src.models.model_utils import temporal_train_test_split, prepare_features
from src.evaluation.model_evaluation import ModelEvaluator
from src.evaluation.revenue_simulation import RevenueSimulator
from src.visualization.dashboard_data import DashboardDataPrep
from src.visualization.insights import InsightsGenerator
from src.utils.config import RESULTS_DIR
from src.utils.helpers import save_json, save_csv
from src.utils.logger import get_logger

logger = get_logger("main")


def run_pipeline(skip_training: bool = False):
    """Execute the full pricing optimization pipeline."""

    # ── 1. Data Ingestion ──────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 1: Data Ingestion")
    logger.info("=" * 60)
    ingestion = DataIngestion()
    data = ingestion.load_all()

    # ── 2. Data Cleaning ──────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 2: Data Cleaning")
    logger.info("=" * 60)
    cleaner = DataCleaner()
    data["sales"] = cleaner.clean_sales(data["sales"])
    data["catalog"] = cleaner.clean_catalog(data["catalog"])
    data["competitors"] = cleaner.clean_competitors(data["competitors"])
    data["inventory"] = cleaner.clean_inventory(data["inventory"])

    # ── 3. Validation ─────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 3: Data Validation")
    logger.info("=" * 60)
    validator = DataValidator()
    validator.validate_sales(data["sales"])
    validator.validate_catalog(data["catalog"])
    validator.validate_referential_integrity(data["sales"], data["catalog"])

    # ── 4. Transformation ─────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 4: Data Transformation")
    logger.info("=" * 60)
    transformer = DataTransformer()
    master = transformer.build_master_dataset(data)

    # ── 5. Feature Engineering ────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 5: Feature Engineering")
    logger.info("=" * 60)
    feature_builder = FeatureBuilder()
    features_df = feature_builder.build_all_features(master)

    # ── 6. Train/Test Split ───────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 6: Train/Test Split")
    logger.info("=" * 60)
    train_df, test_df = temporal_train_test_split(features_df)

    if not skip_training:
        # ── 7. Demand Forecasting ─────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 7: Demand Forecasting")
        logger.info("=" * 60)
        forecaster = DemandForecaster(model_type="gbr")

        feature_cols = [c for c in DemandForecaster.FEATURE_COLS if c in features_df.columns]
        X_train, y_train = prepare_features(train_df, feature_cols, "units_sold")
        X_test, y_test = prepare_features(test_df, feature_cols, "units_sold")

        forecaster.train(X_train, y_train)
        demand_metrics = forecaster.evaluate(X_test, y_test)

        # ── 8. Price Elasticity ───────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 8: Price Elasticity Estimation")
        logger.info("=" * 60)
        elasticity_model = ElasticityModel()
        elasticity_model.estimate_overall(features_df)
        elasticity_model.estimate_by_category(features_df)
        elasticity_model.estimate_by_product(features_df, min_observations=60)

        # ── 9. Pricing Optimization ───────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 9: Pricing Optimization")
        logger.info("=" * 60)
        optimizer = PricingOptimizer(elasticity_model, objective="profit")

        # Build portfolio from latest data
        latest = features_df.groupby("product_id").last().reset_index()
        portfolio = latest[["product_id", "category", "price", "units_sold"]].rename(
            columns={"price": "current_price", "units_sold": "current_demand"}
        )
        portfolio = portfolio.merge(
            data["catalog"][["product_id", "cost"]], on="product_id", how="left"
        )
        if "avg_competitor_price" in latest.columns:
            portfolio["avg_competitor_price"] = latest.set_index("product_id")["avg_competitor_price"].values

        recommendations = optimizer.optimize_portfolio(portfolio)

        # ── 10. Evaluation ────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("STEP 10: Evaluation & Results")
        logger.info("=" * 60)
        evaluator = ModelEvaluator()
        preds = forecaster.predict(X_test)
        evaluator.evaluate_demand_model("gbr", y_test, preds, test_df.loc[y_test.index, "category"])
        evaluator.evaluate_pricing_optimization(recommendations)
        evaluator.save_results()

        # Save recommendations
        save_csv(recommendations, RESULTS_DIR / "pricing_results.csv")

    # ── 11. Generate Insights ─────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("STEP 11: Business Insights")
    logger.info("=" * 60)
    insights_gen = InsightsGenerator()
    insights = insights_gen.generate_all(data["sales"], data["catalog"])
    save_json(insights, RESULTS_DIR / "business_insights.json")

    for insight in insights:
        logger.info(f"  [{insight['type'].upper()}] {insight['title']}: {insight['description']}")

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dynamic Pricing Optimization Pipeline")
    parser.add_argument("--skip-training", action="store_true", help="Skip model training")
    args = parser.parse_args()
    run_pipeline(skip_training=args.skip_training)
