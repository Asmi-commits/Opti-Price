"""
Interactive price simulator component for Streamlit.
"""

import streamlit as st
import pandas as pd
import numpy as np

from src.models.elasticity_model import ElasticityModel


def render_price_simulator(catalog: pd.DataFrame, elasticity_model: ElasticityModel):
    """Render the interactive price simulation tool."""
    st.subheader("🔮 Price Sensitivity Simulator")
    st.markdown("Explore how price changes affect demand, revenue, and profit.")

    col1, col2 = st.columns([1, 2])

    with col1:
        # Product selection
        product_ids = catalog["product_id"].tolist()
        selected_product = st.selectbox("Select Product", product_ids)

        product = catalog[catalog["product_id"] == selected_product].iloc[0]
        st.markdown(f"**Category:** {product['category']}")
        st.markdown(f"**Base Price:** ${product['base_price']:.2f}")
        st.markdown(f"**Cost:** ${product['cost']:.2f}")
        st.markdown(f"**Rating:** {'⭐' * int(product['rating'])} ({product['rating']})")

        current_price = st.number_input(
            "Current Price ($)", value=float(product["base_price"]),
            min_value=0.01, step=1.0,
        )
        current_demand = st.number_input(
            "Current Daily Demand (units)", value=50.0,
            min_value=0.0, step=5.0,
        )

        elasticity = elasticity_model.get_elasticity(selected_product, product["category"])
        st.metric("Price Elasticity", f"{elasticity:.2f}")
        if elasticity < -1:
            st.info("📉 **Elastic** — demand is sensitive to price changes")
        else:
            st.info("📈 **Inelastic** — demand is relatively stable")

    with col2:
        # Simulation
        price_changes = np.arange(-0.30, 0.31, 0.01)
        results = []
        for pct in price_changes:
            new_price = current_price * (1 + pct)
            if new_price < product["cost"] * 1.05:
                continue
            price_ratio = new_price / current_price
            new_demand = max(0, current_demand * (price_ratio ** elasticity))
            revenue = new_price * new_demand
            profit = (new_price - product["cost"]) * new_demand

            results.append({
                "Price Change (%)": round(pct * 100, 1),
                "New Price": round(new_price, 2),
                "Predicted Demand": round(new_demand, 1),
                "Revenue": round(revenue, 2),
                "Profit": round(profit, 2),
            })

        sim_df = pd.DataFrame(results)

        if len(sim_df) > 0:
            # Find optimal prices
            max_rev_idx = sim_df["Revenue"].idxmax()
            max_prof_idx = sim_df["Profit"].idxmax()

            mc1, mc2 = st.columns(2)
            mc1.metric(
                "Revenue-Maximizing Price",
                f"${sim_df.loc[max_rev_idx, 'New Price']:.2f}",
                f"{sim_df.loc[max_rev_idx, 'Price Change (%)']:+.1f}% from current",
            )
            mc2.metric(
                "Profit-Maximizing Price",
                f"${sim_df.loc[max_prof_idx, 'New Price']:.2f}",
                f"{sim_df.loc[max_prof_idx, 'Price Change (%)']:+.1f}% from current",
            )

            st.markdown("#### Revenue & Profit Curve")
            chart_data = sim_df.set_index("Price Change (%)")[["Revenue", "Profit"]]
            st.line_chart(chart_data)

            st.markdown("#### Simulation Table")
            st.dataframe(
                sim_df.style.highlight_max(subset=["Revenue", "Profit"], color="#90EE90"),
                use_container_width=True,
                height=300,
            )
