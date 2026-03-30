#!/usr/bin/env python3
"""
Generate a large, realistic dynamic pricing dataset simulating 2 years of
e-commerce sales across multiple product categories, with competitor pricing,
inventory levels, promotions, seasonality, and demand elasticity baked in.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os, json, hashlib

np.random.seed(42)
OUT = "/home/claude/dynamic-pricing-optimization/data"

# ── 1. Product Catalog (200 products across 8 categories) ──────────────
categories = {
    "Electronics":     {"n": 35, "base_range": (49.99, 1999.99), "elasticity": -1.8, "margin": 0.18},
    "Clothing":        {"n": 30, "base_range": (9.99, 299.99),   "elasticity": -2.2, "margin": 0.45},
    "Home & Kitchen":  {"n": 25, "base_range": (14.99, 599.99),  "elasticity": -1.5, "margin": 0.35},
    "Sports & Outdoors":{"n": 20,"base_range": (19.99, 499.99),  "elasticity": -1.6, "margin": 0.30},
    "Beauty":          {"n": 25, "base_range": (4.99, 149.99),   "elasticity": -2.5, "margin": 0.55},
    "Books":           {"n": 20, "base_range": (5.99, 49.99),    "elasticity": -1.2, "margin": 0.40},
    "Toys & Games":    {"n": 25, "base_range": (9.99, 199.99),   "elasticity": -2.0, "margin": 0.42},
    "Grocery":         {"n": 20, "base_range": (1.99, 79.99),    "elasticity": -0.8, "margin": 0.25},
}

products = []
pid = 1000
for cat, info in categories.items():
    for i in range(info["n"]):
        pid += 1
        base_price = round(np.random.uniform(*info["base_range"]), 2)
        cost = round(base_price * (1 - info["margin"]) * np.random.uniform(0.9, 1.1), 2)
        brand_tier = np.random.choice(["budget", "mid-range", "premium"], p=[0.3, 0.45, 0.25])
        weight_kg = round(np.random.uniform(0.1, 25.0), 2) if cat != "Books" else round(np.random.uniform(0.2, 1.5), 2)
        products.append({
            "product_id": f"SKU-{pid}",
            "product_name": f"{cat.split('&')[0].strip()} Product {i+1:03d}",
            "category": cat,
            "subcategory": f"{cat}_sub_{np.random.randint(1,6)}",
            "brand_tier": brand_tier,
            "base_price": base_price,
            "cost": cost,
            "weight_kg": weight_kg,
            "rating": round(np.clip(np.random.normal(4.0, 0.6), 1.0, 5.0), 1),
            "review_count": int(np.random.lognormal(4.5, 1.2)),
            "launch_date": (datetime(2021, 1, 1) + timedelta(days=np.random.randint(0, 730))).strftime("%Y-%m-%d"),
            "is_perishable": cat == "Grocery",
            "elasticity_estimate": round(info["elasticity"] * np.random.uniform(0.7, 1.3), 2),
        })

catalog_df = pd.DataFrame(products)
catalog_df.to_csv(f"{OUT}/raw/product_catalog.csv", index=False)
print(f"Product catalog: {len(catalog_df)} products")

# ── 2. Holidays Calendar ───────────────────────────────────────────────
holidays = []
for year in [2023, 2024]:
    holiday_list = [
        (f"{year}-01-01", "New Year's Day", "high"),
        (f"{year}-01-26", "Republic Day", "medium"),
        (f"{year}-02-14", "Valentine's Day", "high"),
        (f"{year}-03-08", "International Women's Day", "medium"),
        (f"{year}-03-25", "Holi", "high"),
        (f"{year}-04-14", "Baisakhi", "medium"),
        (f"{year}-05-12", "Mother's Day", "high"),
        (f"{year}-06-16", "Father's Day", "medium"),
        (f"{year}-07-04", "Summer Sale", "high"),
        (f"{year}-08-15", "Independence Day", "high"),
        (f"{year}-09-01", "Back to School", "medium"),
        (f"{year}-10-02", "Gandhi Jayanti", "medium"),
        (f"{year}-10-15", "Navratri Start", "high"),
        (f"{year}-10-24", "Dussehra", "high"),
        (f"{year}-11-01", "Diwali Week Start", "high"),
        (f"{year}-11-12", "Diwali", "high"),
        (f"{year}-11-24", "Black Friday", "high"),
        (f"{year}-11-27", "Cyber Monday", "high"),
        (f"{year}-12-25", "Christmas", "high"),
        (f"{year}-12-31", "New Year's Eve", "high"),
    ]
    for d, name, impact in holiday_list:
        holidays.append({"date": d, "holiday_name": name, "impact_level": impact,
                         "affects_categories": "all" if impact == "high" else np.random.choice(list(categories.keys()))})

holidays_df = pd.DataFrame(holidays)
holidays_df.to_csv(f"{OUT}/external/holidays_calendar.csv", index=False)
print(f"Holidays calendar: {len(holidays_df)} entries")

# ── 3. Daily Sales Data (2 years × 200 products → ~146k rows) ─────────
date_range = pd.date_range("2023-01-01", "2024-12-31", freq="D")
holiday_dates = set(holidays_df["date"].values)
high_holiday_dates = set(holidays_df[holidays_df["impact_level"] == "high"]["date"].values)

sales_rows = []
inv_rows = []
comp_rows = []

for prod in products:
    pid = prod["product_id"]
    base = prod["base_price"]
    cost = prod["cost"]
    elast = prod["elasticity_estimate"]
    cat = prod["category"]

    # Seasonal pattern per category
    if cat in ["Clothing", "Sports & Outdoors"]:
        seasonal_peak_month = np.random.choice([6, 7, 11, 12])
    elif cat == "Electronics":
        seasonal_peak_month = np.random.choice([10, 11, 12])
    elif cat == "Toys & Games":
        seasonal_peak_month = 12
    elif cat == "Grocery":
        seasonal_peak_month = None  # less seasonal
    else:
        seasonal_peak_month = np.random.choice(range(1, 13))

    # Base daily demand
    base_demand = np.random.uniform(5, 80) if cat != "Grocery" else np.random.uniform(20, 200)

    # Inventory simulation
    stock = int(np.random.uniform(200, 2000))
    reorder_point = int(stock * 0.2)

    for date in date_range:
        date_str = date.strftime("%Y-%m-%d")
        dow = date.dayofweek
        month = date.month

        # ── Price dynamics ──
        # Weekly cycle: slight weekend premium
        weekend_factor = 1.03 if dow >= 5 else 1.0
        # Monthly price variation (simulate dynamic pricing strategy)
        monthly_noise = 1 + 0.05 * np.sin(2 * np.pi * month / 12)
        # Random promotion (10% chance)
        promo = np.random.random() < 0.10
        promo_discount = np.random.uniform(0.05, 0.35) if promo else 0.0
        # Competitor pressure
        comp_price_ratio = np.random.normal(1.0, 0.08)
        comp_adj = 1.0 - 0.02 * (comp_price_ratio - 1.0)

        price = base * weekend_factor * monthly_noise * comp_adj * (1 - promo_discount)
        # Don't sell below cost
        price = max(price, cost * 1.05)
        price = round(price, 2)

        # ── Demand model ──
        price_ratio = price / base
        price_effect = np.exp(elast * (price_ratio - 1))
        # Seasonality
        if seasonal_peak_month:
            season_effect = 1 + 0.5 * np.exp(-0.5 * ((month - seasonal_peak_month) % 12)**2 / 4)
        else:
            season_effect = 1 + 0.1 * np.sin(2 * np.pi * month / 12)
        # Day of week effect
        dow_effect = 1.15 if dow in [4, 5] else (0.85 if dow == 0 else 1.0)
        # Holiday boost
        if date_str in high_holiday_dates:
            holiday_effect = np.random.uniform(1.5, 3.0)
        elif date_str in holiday_dates:
            holiday_effect = np.random.uniform(1.1, 1.5)
        else:
            holiday_effect = 1.0
        # Trend (slight growth over time)
        days_since_start = (date - date_range[0]).days
        trend = 1 + 0.0002 * days_since_start
        # Stock-out effect
        stock_effect = 1.0 if stock > reorder_point else max(0.3, stock / reorder_point)

        demand = base_demand * price_effect * season_effect * dow_effect * holiday_effect * trend * stock_effect
        demand = max(0, demand + np.random.normal(0, demand * 0.15))
        units_sold = int(round(demand))

        # Update stock
        stock = max(0, stock - units_sold)
        # Restock simulation
        if stock <= reorder_point and np.random.random() < 0.4:
            restock = int(np.random.uniform(100, 1000))
            stock += restock

        revenue = round(units_sold * price, 2)
        cogs = round(units_sold * cost, 2)

        # Channel split
        channel = np.random.choice(
            ["website", "mobile_app", "marketplace", "in_store"],
            p=[0.35, 0.30, 0.25, 0.10]
        )

        sales_rows.append({
            "date": date_str,
            "product_id": pid,
            "category": cat,
            "price": price,
            "units_sold": units_sold,
            "revenue": revenue,
            "cost_of_goods": cogs,
            "profit": round(revenue - cogs, 2),
            "is_promotion": promo,
            "promotion_discount_pct": round(promo_discount * 100, 1) if promo else 0.0,
            "channel": channel,
            "day_of_week": date.strftime("%A"),
            "month": month,
            "year": date.year,
        })

        # Inventory (sample ~every 3rd day per product to keep size manageable)
        if np.random.random() < 0.33:
            inv_rows.append({
                "date": date_str,
                "product_id": pid,
                "stock_level": stock,
                "reorder_point": reorder_point,
                "days_of_supply": round(stock / max(1, demand), 1),
                "warehouse": np.random.choice(["WH-North", "WH-South", "WH-East", "WH-West"]),
                "last_restock_date": (date - timedelta(days=np.random.randint(1, 30))).strftime("%Y-%m-%d"),
            })

        # Competitor prices (sample ~every 5th day)
        if np.random.random() < 0.20:
            for comp_name in ["CompetitorA", "CompetitorB", "CompetitorC"]:
                comp_price = round(base * comp_price_ratio * np.random.uniform(0.9, 1.15), 2)
                comp_rows.append({
                    "date": date_str,
                    "product_id": pid,
                    "competitor": comp_name,
                    "competitor_price": comp_price,
                    "price_difference": round(price - comp_price, 2),
                    "price_difference_pct": round((price - comp_price) / comp_price * 100, 1),
                    "in_stock": np.random.random() > 0.1,
                    "has_promotion": np.random.random() < 0.15,
                })

    if len(sales_rows) % 50000 == 0:
        print(f"  Generated {len(sales_rows):,} sales rows...")

print(f"Generating DataFrames...")
sales_df = pd.DataFrame(sales_rows)
inv_df = pd.DataFrame(inv_rows)
comp_df = pd.DataFrame(comp_rows)

# Save raw data
sales_df.to_csv(f"{OUT}/raw/sales_data.csv", index=False)
inv_df.to_csv(f"{OUT}/raw/inventory_data.csv", index=False)
comp_df.to_csv(f"{OUT}/raw/competitor_prices.csv", index=False)

print(f"\n=== Dataset Summary ===")
print(f"Sales data:       {len(sales_df):>10,} rows  ({os.path.getsize(f'{OUT}/raw/sales_data.csv') / 1e6:.1f} MB)")
print(f"Inventory data:   {len(inv_df):>10,} rows  ({os.path.getsize(f'{OUT}/raw/inventory_data.csv') / 1e6:.1f} MB)")
print(f"Competitor prices: {len(comp_df):>10,} rows  ({os.path.getsize(f'{OUT}/raw/competitor_prices.csv') / 1e6:.1f} MB)")
print(f"Product catalog:  {len(catalog_df):>10,} rows")
print(f"Date range: {sales_df['date'].min()} to {sales_df['date'].max()}")
print(f"Products: {sales_df['product_id'].nunique()}")
print(f"Categories: {sales_df['category'].nunique()}")
print(f"Total revenue: ${sales_df['revenue'].sum():,.2f}")
print(f"Total units sold: {sales_df['units_sold'].sum():,}")

# ── 4. Processed Data ──────────────────────────────────────────────────
print("\nGenerating processed data...")

# Cleaned data (same as raw but with explicit dtypes)
cleaned = sales_df.copy()
cleaned["date"] = pd.to_datetime(cleaned["date"])
cleaned = cleaned.sort_values(["product_id", "date"]).reset_index(drop=True)
cleaned.to_csv(f"{OUT}/processed/cleaned_data.csv", index=False)

# Feature engineered
feat = cleaned.copy()
feat["price_to_base_ratio"] = feat.apply(
    lambda r: round(r["price"] / catalog_df[catalog_df["product_id"] == r["product_id"]]["base_price"].values[0], 4)
    if r["product_id"] in catalog_df["product_id"].values else 1.0, axis=1
)
feat["rolling_7d_sales"] = feat.groupby("product_id")["units_sold"].transform(lambda x: x.rolling(7, min_periods=1).mean().round(1))
feat["rolling_30d_sales"] = feat.groupby("product_id")["units_sold"].transform(lambda x: x.rolling(30, min_periods=1).mean().round(1))
feat["price_change_pct"] = feat.groupby("product_id")["price"].transform(lambda x: x.pct_change().fillna(0).round(4))
feat["is_weekend"] = feat["date"].dt.dayofweek >= 5
feat["quarter"] = feat["date"].dt.quarter
feat["week_of_year"] = feat["date"].dt.isocalendar().week.astype(int)
feat.to_csv(f"{OUT}/processed/feature_engineered.csv", index=False)

# Train/test split marker
feat["split"] = "train"
feat.loc[feat["date"] >= "2024-10-01", "split"] = "test"
feat[["date", "product_id", "split"]].to_csv(f"{OUT}/processed/train_test_split.csv", index=False)

print(f"Feature engineered: {len(feat):,} rows")
print(f"Train/test: {(feat['split']=='train').sum():,} / {(feat['split']=='test').sum():,}")
print("\nAll data files generated successfully!")