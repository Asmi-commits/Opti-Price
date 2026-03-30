"""
KPI card components for Streamlit dashboard.
"""

import streamlit as st
from typing import Dict, Optional


def render_kpi_cards(kpis: Dict, previous_kpis: Optional[Dict] = None):
    """Render KPI metric cards with optional delta comparison."""

    def _delta(current_key: str, prev: Optional[Dict]) -> Optional[str]:
        if prev and current_key in prev:
            diff = kpis[current_key] - prev[current_key]
            pct = diff / max(abs(prev[current_key]), 1) * 100
            return f"{pct:+.1f}%"
        return None

    row1 = st.columns(4)
    row1[0].metric(
        "💰 Total Revenue",
        f"${kpis['total_revenue']:,.0f}",
        delta=_delta("total_revenue", previous_kpis),
    )
    row1[1].metric(
        "📈 Total Profit",
        f"${kpis['total_profit']:,.0f}",
        delta=_delta("total_profit", previous_kpis),
    )
    row1[2].metric(
        "📦 Units Sold",
        f"{kpis['total_units']:,}",
        delta=_delta("total_units", previous_kpis),
    )
    row1[3].metric(
        "📊 Avg Margin",
        f"{kpis['avg_margin_pct']}%",
        delta=_delta("avg_margin_pct", previous_kpis),
    )

    row2 = st.columns(4)
    row2[0].metric("🛍️ Products", f"{kpis['num_products']}")
    row2[1].metric("🧾 Transactions", f"{kpis['num_transactions']:,}")
    row2[2].metric("💵 Avg Order Value", f"${kpis['avg_order_value']:.2f}")
    row2[3].metric("🏷️ Promo Rate", f"{kpis['promo_pct']}%")
