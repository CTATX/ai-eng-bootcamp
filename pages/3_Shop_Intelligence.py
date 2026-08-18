"""Shop intelligence — synthetic Porsche warehouse screens. Not a ShopMonkey reskin."""

from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

from api_client import API_BASE, server_is_up


@st.cache_data(ttl=30)
def load_shop(path: str):
    response = requests.get(f"{API_BASE}{path}", timeout=20)
    response.raise_for_status()
    return response.json()


st.title("Shop intelligence")
st.caption(
    "Synthetic Porsche prototype (1980–2025). No ShopMonkey key. "
    "Not live Pelican or WorldPac inventory. Not a ShopMonkey reskin."
)

if not server_is_up():
    st.error("Your API is not running. Start it with `./start.sh`, then refresh.")
    st.stop()

try:
    status = load_shop("/shop/status")
    tickets = load_shop("/shop/trends/tickets")
    reasons = load_shop("/shop/trends/reasons")
    models = load_shop("/shop/trends/models")
    parts = load_shop("/shop/parts")
    artifacts = load_shop("/shop/artifacts")
    gotcha_payload = load_shop("/shop/gotchas")
except requests.RequestException as exc:
    st.error(f"Could not load shop warehouse: {exc}")
    st.stop()

st.warning(status["disclaimer"])

counts = status["counts"]
col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Vehicles", f"{counts['vehicles']:,}")
col_b.metric("Orders", f"{counts['orders']:,}")
col_c.metric("Catalog SKUs", f"{counts['parts_catalog']:,}")
col_d.metric("Comeback orders", f"{gotcha_payload['comeback_orders']:,}")

st.caption(
    f"FACT · make {', '.join(status['makes'])} · "
    f"model years {status['vehicle_year_min']}–{status['vehicle_year_max']} · "
    f"source `{status['source']}` · "
    f"labor hours missing on {status['orders_missing_labor_hours']} orders "
    f"({status['missing_labor_share']:.0%} UNKNOWN)"
)

trend_tab, parts_tab, packet_tab = st.tabs(
    ["Trends", "Product list", "Job packet holes"]
)

with trend_tab:
    left, right = st.columns(2)
    with left:
        st.subheader("Average ticket by shop year")
        ticket_frame = pd.DataFrame(tickets)
        st.line_chart(ticket_frame, x="year", y="avg_ticket_usd")
        st.caption("INFERRED mean of synthetic invoiced totals. Min/max are observed in that year.")
        st.dataframe(
            ticket_frame.rename(
                columns={
                    "year": "Year",
                    "order_count": "Orders",
                    "avg_ticket_usd": "Typical $",
                    "min_ticket_usd": "Best observed $",
                    "max_ticket_usd": "Worst observed $",
                }
            ),
            hide_index=True,
        )
    with right:
        st.subheader("Why it came in")
        reason_frame = pd.DataFrame(reasons)
        st.bar_chart(reason_frame, x="reason", y="order_count")
        st.caption("FACT counts of service reasons in the warehouse.")

    st.subheader("Model mix")
    model_frame = pd.DataFrame(models)
    st.bar_chart(model_frame, x="model", y="order_count")

    st.subheader("Gotchas (defined, not diagnosed)")
    if gotcha_payload["events"]:
        st.dataframe(pd.DataFrame(gotcha_payload["events"]), hide_index=True)
        st.caption(
            "FACT event counts. Comeback = second visit within 30 days. "
            "Not a failure-mode conclusion."
        )
    else:
        st.info("No gotcha rows in this seed.")

with parts_tab:
    st.subheader("Product list")
    st.caption(
        "Named sources a shop would actually check. SKUs and prices are synthetic. "
        "We did not scrape Pelican Parts, WorldPac, or anyone else."
    )
    vendor_filter = st.multiselect(
        "Vendor",
        sorted({row["vendor"] for row in parts}),
        default=None,
    )
    catalog_frame = pd.DataFrame(parts)
    if vendor_filter:
        catalog_frame = catalog_frame[catalog_frame["vendor"].isin(vendor_filter)]
    catalog_frame = catalog_frame.copy()
    catalog_frame["in_stock"] = catalog_frame["in_stock"].map(
        lambda value: "On hand" if value else "Order"
    )
    st.dataframe(
        catalog_frame.rename(
            columns={
                "sku": "SKU",
                "name": "Part",
                "vendor": "Source",
                "vendor_kind": "Kind",
                "list_usd": "List $",
                "lead_days": "Lead days",
                "in_stock": "Availability",
                "source": "Data",
            }
        ),
        hide_index=True,
    )

with packet_tab:
    st.subheader("What should ride with each job")
    st.caption(
        "Designs, schematics, take-apart, build steps, images, and video are required "
        "later. This prototype only has a shop-authored checklist stub. Everything else "
        "is UNKNOWN — not filled in."
    )
    artifact_frame = pd.DataFrame(artifacts)
    artifact_frame["available"] = artifact_frame["available"].map(
        lambda value: "Present" if value else "UNKNOWN"
    )
    st.dataframe(
        artifact_frame.rename(
            columns={
                "job_family": "Job family",
                "artifact_type": "Artifact",
                "title": "Title",
                "available": "Status",
                "note": "Note",
                "source": "Data",
            }
        ),
        hide_index=True,
    )
