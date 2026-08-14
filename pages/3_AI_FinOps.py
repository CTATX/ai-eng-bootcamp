"""AI FinOps overview — actual usage, efficiency, outcomes, and budget controls."""

from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

from api_client import API_BASE, server_is_up


@st.cache_data(ttl=10)
def load_finops(path: str, params: dict | None = None):
    response = requests.get(f"{API_BASE}{path}", params=params, timeout=15)
    response.raise_for_status()
    return response.json()


st.title("AI FinOps")
st.caption(
    "Outcome-linked AI spend and operations. Cost is estimated from provider usage; "
    "spend alone is not value."
)

if not server_is_up():
    st.error("Your API is not running. Start it with `./start.sh`, then refresh.")
    st.stop()

with st.sidebar:
    st.header("Dashboard controls")
    window_days = st.segmented_control(
        "Time window",
        options=[7, 30],
        default=30,
        format_func=lambda value: f"{value} days",
    )
    dimension_labels = {
        "Business owner": "business_owner_id",
        "User": "user_id",
        "Use case": "use_case",
        "Model": "model_id",
    }
    dimension_label = st.selectbox("Attribution view", list(dimension_labels))
    if st.button("Refresh data", width="stretch"):
        st.cache_data.clear()
        st.rerun()

try:
    kpis = load_finops("/finops/kpis", {"days": window_days})
    daily = load_finops("/finops/spend/daily", {"days": window_days})
    attribution = load_finops(
        "/finops/attribution",
        {"days": window_days, "dimension": dimension_labels[dimension_label]},
    )
except requests.RequestException as exc:
    st.error(f"Could not load FinOps data: {exc}")
    st.stop()

budget_status = kpis["budget_status"]
if budget_status == "critical":
    st.error("Daily API budget is at or above 100%.")
elif budget_status == "warning":
    st.warning("Daily API budget has crossed the warning threshold.")
elif budget_status == "informational":
    st.info("Daily API budget has crossed 50%.")

with st.container(horizontal=True):
    st.metric(
        f"{window_days}-day spend",
        f"${kpis['total_spend_usd']:.4f}",
        border=True,
        help=kpis["cost_confidence"],
    )
    st.metric(
        "Average daily spend",
        f"${kpis['average_daily_spend_usd']:.4f}",
        border=True,
        help="Includes zero-spend calendar days.",
    )
    st.metric(
        "Cost / accepted outcome",
        (
            f"${kpis['cost_per_accepted_outcome_usd']:.4f}"
            if kpis["cost_per_accepted_outcome_usd"] is not None
            else "Not available"
        ),
        border=True,
    )
    st.metric(
        "Provider cache ratio",
        (
            f"{kpis['provider_cache_ratio']:.1%}"
            if kpis["provider_cache_ratio"] is not None
            else "No usage"
        ),
        border=True,
        help=kpis["cache_metric_label"],
    )

with st.container(horizontal=True):
    st.metric(
        "Requests",
        f"{kpis['request_count']:,}",
        border=True,
    )
    st.metric(
        "Successful task rate",
        (
            f"{kpis['successful_task_rate']:.1%}"
            if kpis["successful_task_rate"] is not None
            else "No usage"
        ),
        border=True,
    )
    st.metric(
        "Acceptance rate",
        (
            f"{kpis['acceptance_rate']:.1%}"
            if kpis["acceptance_rate"] is not None
            else "Needs reviews"
        ),
        border=True,
    )
    st.metric(
        "Daily budget used",
        (
            f"{kpis['daily_budget_utilization']:.1%}"
            if kpis["daily_budget_utilization"] is not None
            else "No budget"
        ),
        border=True,
        help=f"Daily budget: ${kpis['daily_budget_usd']:.2f}",
    )

trend_col, control_col = st.columns([2, 1])
with trend_col:
    with st.container(border=True):
        st.subheader("Daily API spend")
        daily_frame = pd.DataFrame(daily)
        st.line_chart(
            daily_frame,
            x="date",
            y="estimated_spend_usd",
            x_label="Date",
            y_label="Estimated spend (USD)",
        )

with control_col:
    with st.container(border=True):
        st.subheader("Budget control")
        st.metric(
            "Today",
            f"${kpis['today_spend_usd']:.4f}",
            help=f"Daily cap: ${kpis['daily_budget_usd']:.2f}",
        )
        st.metric(
            "Projected month end",
            f"${kpis['projected_month_end_spend_usd']:.2f}",
            help="Directional projection based on elapsed calendar days.",
        )
        st.write(
            "Hard stop: "
            + ("**enabled**" if kpis["hard_stop_enabled"] else "**off (recommended for learning)**")
        )

with st.container(border=True):
    st.subheader(f"Spend by {dimension_label.lower()}")
    if attribution:
        attribution_frame = pd.DataFrame(attribution)
        st.dataframe(
            attribution_frame,
            column_config={
                "dimension": st.column_config.TextColumn(dimension_label, pinned=True),
                "estimated_spend_usd": st.column_config.NumberColumn(
                    "Estimated spend", format="$%.6f"
                ),
                "request_count": st.column_config.NumberColumn("Requests", format="%d"),
                "accepted_outcomes": st.column_config.NumberColumn(
                    "Accepted outcomes", format="%d"
                ),
                "spend_share": st.column_config.ProgressColumn(
                    "Spend share", min_value=0, max_value=1, format="percent"
                ),
                "cost_per_accepted_outcome_usd": st.column_config.NumberColumn(
                    "Cost / accepted outcome", format="$%.6f"
                ),
            },
            hide_index=True,
        )
    else:
        st.info("No attributed usage in this window. Ask a Q&A question to create an event.")

with st.expander("Metric confidence and value controls"):
    st.markdown(
        f"""
- **Cost:** {kpis['cost_confidence']}
- **Cache:** {kpis['cache_metric_label']}
- **Normalized cache ratio:** {kpis['normalized_cache_note']}
- **Business value:** {kpis['value_status']}

ROI is intentionally withheld until people cost, infrastructure, and Finance-validated
value are captured. See `docs/ai-finops-kpi-contract.md`.
"""
    )
