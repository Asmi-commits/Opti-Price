"""
Data validation: schema checks, data quality assertions, integrity tests.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataValidator:
    """Validate data quality and integrity."""

    def __init__(self):
        self.issues: List[Dict] = []

    def validate_sales(self, df: pd.DataFrame) -> bool:
        """Run all sales data validations."""
        self.issues = []
        self._check_required_columns(df, [
            "date", "product_id", "price", "units_sold", "revenue",
        ])
        self._check_no_nulls(df, ["date", "product_id", "price"])
        self._check_positive(df, "price")
        self._check_non_negative(df, "units_sold")
        self._check_date_range(df, "date", "2023-01-01", "2024-12-31")
        self._check_revenue_consistency(df)
        self._report()
        return len(self.issues) == 0

    def validate_catalog(self, df: pd.DataFrame) -> bool:
        """Validate product catalog."""
        self.issues = []
        self._check_required_columns(df, ["product_id", "base_price", "cost", "category"])
        self._check_unique(df, "product_id")
        self._check_positive(df, "base_price")
        self._check_positive(df, "cost")
        self._check_margin_positive(df)
        self._report()
        return len(self.issues) == 0

    def validate_referential_integrity(
        self, sales: pd.DataFrame, catalog: pd.DataFrame
    ) -> bool:
        """Ensure all products in sales exist in catalog."""
        self.issues = []
        sales_products = set(sales["product_id"].unique())
        catalog_products = set(catalog["product_id"].unique())
        orphans = sales_products - catalog_products
        if orphans:
            self.issues.append({
                "severity": "error",
                "check": "referential_integrity",
                "message": f"{len(orphans)} products in sales not found in catalog",
                "details": list(orphans)[:10],
            })
        self._report()
        return len(self.issues) == 0

    # ── Private validation methods ─────────────────────────────────────

    def _check_required_columns(self, df: pd.DataFrame, cols: List[str]):
        missing = [c for c in cols if c not in df.columns]
        if missing:
            self.issues.append({
                "severity": "error",
                "check": "required_columns",
                "message": f"Missing columns: {missing}",
            })

    def _check_no_nulls(self, df: pd.DataFrame, cols: List[str]):
        for col in cols:
            if col in df.columns:
                n_null = df[col].isnull().sum()
                if n_null > 0:
                    self.issues.append({
                        "severity": "warning",
                        "check": "no_nulls",
                        "message": f"{col}: {n_null:,} null values ({n_null/len(df)*100:.2f}%)",
                    })

    def _check_positive(self, df: pd.DataFrame, col: str):
        if col in df.columns:
            n_neg = (df[col] <= 0).sum()
            if n_neg > 0:
                self.issues.append({
                    "severity": "warning",
                    "check": "positive_values",
                    "message": f"{col}: {n_neg:,} non-positive values",
                })

    def _check_non_negative(self, df: pd.DataFrame, col: str):
        if col in df.columns:
            n_neg = (df[col] < 0).sum()
            if n_neg > 0:
                self.issues.append({
                    "severity": "warning",
                    "check": "non_negative",
                    "message": f"{col}: {n_neg:,} negative values",
                })

    def _check_unique(self, df: pd.DataFrame, col: str):
        if col in df.columns:
            n_dupes = df[col].duplicated().sum()
            if n_dupes > 0:
                self.issues.append({
                    "severity": "error",
                    "check": "uniqueness",
                    "message": f"{col}: {n_dupes:,} duplicate values",
                })

    def _check_date_range(self, df: pd.DataFrame, col: str, min_date: str, max_date: str):
        if col in df.columns:
            dates = pd.to_datetime(df[col])
            out_of_range = ((dates < min_date) | (dates > max_date)).sum()
            if out_of_range > 0:
                self.issues.append({
                    "severity": "warning",
                    "check": "date_range",
                    "message": f"{col}: {out_of_range:,} values outside [{min_date}, {max_date}]",
                })

    def _check_revenue_consistency(self, df: pd.DataFrame):
        if {"price", "units_sold", "revenue"}.issubset(df.columns):
            expected = (df["price"] * df["units_sold"]).round(2)
            mismatch = (abs(df["revenue"] - expected) > 0.01).sum()
            if mismatch > 0:
                self.issues.append({
                    "severity": "warning",
                    "check": "revenue_consistency",
                    "message": f"{mismatch:,} rows where revenue != price * units_sold",
                })

    def _check_margin_positive(self, df: pd.DataFrame):
        if {"base_price", "cost"}.issubset(df.columns):
            neg_margin = (df["base_price"] <= df["cost"]).sum()
            if neg_margin > 0:
                self.issues.append({
                    "severity": "warning",
                    "check": "margin_positive",
                    "message": f"{neg_margin:,} products with base_price <= cost",
                })

    def _report(self):
        errors = [i for i in self.issues if i["severity"] == "error"]
        warnings = [i for i in self.issues if i["severity"] == "warning"]
        if errors:
            for e in errors:
                logger.error(f"VALIDATION ERROR: {e['message']}")
        if warnings:
            for w in warnings:
                logger.warning(f"VALIDATION WARNING: {w['message']}")
        if not self.issues:
            logger.info("All validation checks passed")