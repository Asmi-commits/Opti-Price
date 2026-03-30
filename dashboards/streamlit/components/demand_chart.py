"""
Demand analysis charts for Streamlit dashboard.
"""

import streamlit as st
import pandas as pd
import numpy as np


def render_demand_charts(sales: pd.DataFrame):
    """Render demand analysis visualizations."""
    st.subheader("📊 Demand Analysis by Category")

    # Category revenue comparison
    cat_rev = sales.groupby("category").agg(
        revenue=("revenue", "sum"),
        units=("units_sold", "sum"),
        avg_price=("price", "mean"),
        transactions=("units_sold", "count"),
    ).sort_values("revenue", ascending=False)

    st.bar_chart(cat_rev["revenue"])

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📅 Demand by Day of Week")
        dow_demand = sales.groupby("day_of_week")["units_sold"].mean()
        dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dow_demand = dow_demand.reindex(dow_order)
        st.bar_chart(dow_demand)

    with col2:
        st.subheader("📆 Monthly Demand Trend")
        sales["month_year"] = sales["date"].dt.to_period("M").astype(str)
        monthly = sales.groupby("month_year")["units_sold"].sum()
        st.line_chart(monthly)

    st.markdown("---")
    st.subheader("🏷️ Promotion Impact on Demand")

    promo_impact = sales.groupby(["category", "is_promotion"])["units_sold"].mean().unstack()
    promo_impact.columns = ["No Promo", "Promo"]
    promo_impact["Lift %"] = ((promo_impact["Promo"] - promo_impact["No Promo"]) /
                               promo_impact["No Promo"] * 100).round(1)
    st.dataframe(promo_impact, use_container_width=True)

    st.markdown("---")
    st.subheader("🔥 Top 20 Products by Volume")
    top_products = (
        sales.groupby("product_id")["units_sold"]
        .sum()
        .nlargest(20)
        .reset_index()
    )
    st.bar_chart(top_products.set_index("product_id")["units_sold"])
