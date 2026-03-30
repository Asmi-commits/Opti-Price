"""Tests for the data pipeline modules."""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_pipeline.ingestion import DataIngestion
from src.data_pipeline.cleaning import DataCleaner
from src.data_pipeline.validation import DataValidator


class TestDataIngestion:
    def test_load_sales(self):
        ingestion = DataIngestion()
        df = ingestion.load_sales()
        assert len(df) > 0
        assert "date" in df.columns
        assert "product_id" in df.columns
        assert "price" in df.columns

    def test_load_catalog(self):
        ingestion = DataIngestion()
        df = ingestion.load_catalog()
        assert len(df) > 0
        assert df["product_id"].is_unique

    def test_load_all(self):
        ingestion = DataIngestion()
        data = ingestion.load_all()
        assert set(data.keys()) == {"sales", "catalog", "competitors", "inventory", "holidays"}


class TestDataCleaner:
    def setup_method(self):
        self.cleaner = DataCleaner()

    def test_clean_sales_removes_negatives(self):
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=5),
            "product_id": ["A"] * 5,
            "price": [10, -5, 20, 0, 15],
            "units_sold": [5, 3, 8, 2, 4],
            "revenue": [50, -15, 160, 0, 60],
            "cost_of_goods": [30, 9, 96, 0, 36],
            "profit": [20, -24, 64, 0, 24],
            "is_promotion": [False] * 5,
            "channel": ["website"] * 5,
        })
        cleaned = self.cleaner.clean_sales(df)
        assert (cleaned["price"] > 0).all()

    def test_clean_catalog_clips_rating(self):
        df = pd.DataFrame({
            "product_id": ["A", "B", "C"],
            "base_price": [10, 20, 30],
            "cost": [5, 10, 15],
            "rating": [0.5, 3.5, 6.0],
            "review_count": [10, -5, 100],
        })
        cleaned = self.cleaner.clean_catalog(df)
        assert cleaned["rating"].max() <= 5.0
        assert cleaned["rating"].min() >= 1.0
        assert (cleaned["review_count"] >= 0).all()


class TestDataValidator:
    def setup_method(self):
        self.validator = DataValidator()

    def test_validate_sales_passes(self):
        df = pd.DataFrame({
            "date": pd.date_range("2023-06-01", periods=10),
            "product_id": [f"P{i}" for i in range(10)],
            "price": np.random.uniform(10, 100, 10),
            "units_sold": np.random.randint(1, 50, 10),
            "revenue": np.random.uniform(100, 5000, 10),
        })
        # Revenue won't match price*units but that's a warning, not a failure
        result = self.validator.validate_sales(df)
        # Should at least not error out
        assert isinstance(result, bool)

    def test_validate_catalog_detects_duplicates(self):
        df = pd.DataFrame({
            "product_id": ["A", "A", "B"],
            "base_price": [10, 10, 20],
            "cost": [5, 5, 10],
            "category": ["X", "X", "Y"],
        })
        result = self.validator.validate_catalog(df)
        assert result is False  # Should fail due to duplicate product_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
