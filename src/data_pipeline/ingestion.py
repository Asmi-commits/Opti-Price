"""
Data ingestion: load raw data from various sources into DataFrames.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Optional

from src.utils.config import (
    SALES_FILE, CATALOG_FILE, COMPETITOR_FILE,
    INVENTORY_FILE, HOLIDAYS_FILE,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataIngestion:
    """Handles loading of all raw data sources."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.sales_path = SALES_FILE
        self.catalog_path = CATALOG_FILE
        self.competitor_path = COMPETITOR_FILE
        self.inventory_path = INVENTORY_FILE
        self.holidays_path = HOLIDAYS_FILE

    def load_sales(self) -> pd.DataFrame:
        """Load sales transaction data."""
        logger.info(f"Loading sales data from {self.sales_path}")
        df = pd.read_csv(self.sales_path, parse_dates=["date"])
        logger.info(f"Loaded {len(df):,} sales records ({df['date'].min()} to {df['date'].max()})")
        return df

    def load_catalog(self) -> pd.DataFrame:
        """Load product catalog."""
        logger.info(f"Loading product catalog from {self.catalog_path}")
        df = pd.read_csv(self.catalog_path, parse_dates=["launch_date"])
        logger.info(f"Loaded {len(df):,} products across {df['category'].nunique()} categories")
        return df

    def load_competitors(self) -> pd.DataFrame:
        """Load competitor pricing data."""
        logger.info(f"Loading competitor prices from {self.competitor_path}")
        df = pd.read_csv(self.competitor_path, parse_dates=["date"])
        logger.info(f"Loaded {len(df):,} competitor price records")
        return df

    def load_inventory(self) -> pd.DataFrame:
        """Load inventory/stock level data."""
        logger.info(f"Loading inventory data from {self.inventory_path}")
        df = pd.read_csv(self.inventory_path, parse_dates=["date", "last_restock_date"])
        logger.info(f"Loaded {len(df):,} inventory records")
        return df

    def load_holidays(self) -> pd.DataFrame:
        """Load holidays calendar."""
        logger.info(f"Loading holidays from {self.holidays_path}")
        df = pd.read_csv(self.holidays_path, parse_dates=["date"])
        logger.info(f"Loaded {len(df):,} holiday entries")
        return df

    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Load all data sources into a dictionary."""
        return {
            "sales": self.load_sales(),
            "catalog": self.load_catalog(),
            "competitors": self.load_competitors(),
            "inventory": self.load_inventory(),
            "holidays": self.load_holidays(),
        }
