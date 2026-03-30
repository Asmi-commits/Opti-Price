"""
Streamlit Dashboard for Dynamic Pricing Optimization.
Run with: streamlit run dashboards/streamlit/app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data_pipeline.ingestion import DataIngestion
from src.visualization.dashboard_data import DashboardDataPrep
from src.models.elasticity_model import ElasticityModel

st.set_page_config(
    page_title="Dynamic Pricing Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main { padding: 1rem 2rem; }
    .stMetric { background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #4CAF50; }
    h1 { color: #1a1a2e; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { padding: 8px 16px; border-radius: 4px 4px 0 0; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_data():
    """Load and cache data."""
    ingestion = DataIngestion()
    sales = ingestion.load_sales()
    catalog = ingestion.load_catalog()
    competitors = ingestion.load_competitors()
    return sales, catalog, competitors


@st.cache_resource
def load_elasticity_model(sales):
    """Load and cache elasticity model."""
    model = ElasticityModel()
    model.estimate_by_category(sales)
    model.estimate_by_product(sales, min_observations=60)
    return model


def main():
    st.title("💰 Dynamic Pricing Optimization Dashboard")
    st.markdown("Real-time pricing intelligence and optimization recommendations")

    # Load data
    with st.spinner("Loading data..."):
        sales, catalog, competitors = load_data()
        prep = DashboardDataPrep()

    # Sidebar filters
    st.sidebar.header("Filters")
    categories = ["All"] + sorted(sales["category"].unique().tolist())
    selected_cat = st.sidebar.selectbox("Category", categories)

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(sales["date"].min(), sales["date"].max()),
        min_value=sales["date"].min(),
        max_value=sales["date"].max(),
    )

    # Apply filters
    filtered = sales.copy()
    if selected_cat != "All":
        filtered = filtered[filtered["category"] == selected_cat]
    if len(date_range) == 2:
        filtered = filtered[
            (filtered["date"] >= pd.Timestamp(date_range[0])) &
            (filtered["date"] <= pd.Timestamp(date_range[1]))
        ]

    # KPIs
    kpis = prep.compute_kpis(filtered)

    st.markdown("---")
    cols = st.columns(4)
    cols[0].metric("Total Revenue", f"${kpis['total_revenue']:,.0f}")
    cols[1].metric("Total Profit", f"${kpis['total_profit']:,.0f}")
    cols[2].metric("Units Sold", f"{kpis['total_units']:,}")
    cols[3].metric("Avg Margin", f"{kpis['avg_margin_pct']}%")

    cols2 = st.columns(4)
    cols2[0].metric("Products", f"{kpis['num_products']}")
    cols2[1].metric("Transactions", f"{kpis['num_transactions']:,}")
    cols2[2].metric("Avg Order Value", f"${kpis['avg_order_value']:.2f}")
    cols2[3].metric("Promo Rate", f"{kpis['promo_pct']}%")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Revenue Trends", "🏷️ Pricing Analysis",
        "🔮 Price Simulator", "📊 Category Insights",
    ])

    with tab1:
        st.subheader("Revenue Over Time")
        daily = prep.daily_summary(filtered)
        st.line_chart(daily.set_index("date")[["revenue", "profit"]])

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Channel Mix")
            channel = prep.channel_mix(filtered)
            st.bar_chart(channel.set_index("channel")["revenue"])
        with col2:
            st.subheader("Promotion Impact")
            promo_analysis = prep.promotion_analysis(filtered)
            st.dataframe(promo_analysis, use_container_width=True)

    with tab2:
        st.subheader("Price Distribution by Category")
        cat_summary = prep.category_summary(filtered)
        st.dataframe(cat_summary, use_container_width=True)

        st.subheader("Top Products by Revenue")
        top_products = prep.product_performance(filtered, top_n=20)
        st.dataframe(top_products, use_container_width=True)

    with tab3:
        from dashboards.streamlit.components.price_simulator import render_price_simulator
        elast_model = load_elasticity_model(sales)
        render_price_simulator(catalog, elast_model)

    with tab4:
        from dashboards.streamlit.components.demand_chart import render_demand_charts
        render_demand_charts(filtered)


if __name__ == "__main__":
    main()
