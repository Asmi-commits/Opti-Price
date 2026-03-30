"""
Project-wide constants.
"""

CATEGORIES = [
    "Electronics",
    "Clothing",
    "Home & Kitchen",
    "Sports & Outdoors",
    "Beauty",
    "Books",
    "Toys & Games",
    "Grocery",
]

CHANNELS = ["website", "mobile_app", "marketplace", "in_store"]

BRAND_TIERS = ["budget", "mid-range", "premium"]

WAREHOUSES = ["WH-North", "WH-South", "WH-East", "WH-West"]

COMPETITORS = ["CompetitorA", "CompetitorB", "CompetitorC"]

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Column name mappings
SALES_COLS = [
    "date", "product_id", "category", "price", "units_sold",
    "revenue", "cost_of_goods", "profit", "is_promotion",
    "promotion_discount_pct", "channel", "day_of_week", "month", "year",
]

CATALOG_COLS = [
    "product_id", "product_name", "category", "subcategory", "brand_tier",
    "base_price", "cost", "weight_kg", "rating", "review_count",
    "launch_date", "is_perishable", "elasticity_estimate",
]

# Metric names
METRIC_MAE = "mean_absolute_error"
METRIC_RMSE = "root_mean_squared_error"
METRIC_MAPE = "mean_absolute_percentage_error"
<<<<<<< HEAD
METRIC_R2 = "r_squared"
=======
METRIC_R2 = "r_squared"
>>>>>>> 4219dc752222c7785caaafee868265c5ea202b15
