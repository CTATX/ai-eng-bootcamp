"""ShopMonkey integration — our UI calling their official API. Not a reskin."""

from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

from api_client import API_BASE, server_is_up


@st.cache_data(ttl=30)
def load_shopmonkey(path: str, params: dict | None = None):
    response = requests.get(f"{API_BASE}{path}", params=params, timeout=20)
    response.raise_for_status()
    return response.json()


st.title("ShopMonkey integration")
st.caption(
    "Our app talks to ShopMonkey REST v3. This is not a ShopMonkey reskin, "
    "iframe, or white-label."
)

if not server_is_up():
    st.error("Your API is not running. Start it with `./start.sh`, then refresh.")
    st.stop()

try:
    catalog = load_shopmonkey("/shopmonkey/catalog")
except requests.RequestException as exc:
    st.error(f"Could not load the ShopMonkey catalog: {exc}")
    st.stop()

st.info(catalog["summary"])

with st.sidebar:
    st.header("Shop snapshot")
    limit = st.selectbox("Rows per list", [10, 25, 50], index=1)
    if st.button("Refresh data", icon=":material/refresh:", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Live calls need `SHOPMONKEY_API_KEY` in `.env`.")

status_slot = st.container()
data_slot = st.container()

with status_slot:
    try:
        status = load_shopmonkey("/shopmonkey/status")
    except requests.HTTPError as exc:
        detail = exc.response.json().get("detail", exc.response.text) if exc.response is not None else str(exc)
        st.error(f"ShopMonkey status: {detail}")
        status = {"configured": False, "connected": False, "message": str(detail)}
    except requests.RequestException as exc:
        st.error(f"Could not check ShopMonkey: {exc}")
        st.stop()

    with st.container(horizontal=True):
        st.metric(
            "Official API",
            "Allowed",
            border=True,
            help="REST v3 integration is allowed. Reskin is not.",
        )
        st.metric(
            "Reskin ShopMonkey",
            "Not allowed",
            border=True,
        )
        st.metric(
            "API key",
            "Configured" if status.get("configured") else "Missing",
            border=True,
        )
        st.metric(
            "ShopMonkey",
            "Connected" if status.get("connected") else "Not connected",
            border=True,
        )
    st.caption(status.get("message", ""))

allowed_tab, blocked_tab, live_tab = st.tabs(
    ["Allowed APIs", "Not allowed", "Live shop data"]
)

with allowed_tab:
    with st.container(border=True):
        st.subheader("What the API lets us do")
        st.dataframe(
            pd.DataFrame(catalog["allowed_resources"]),
            column_config={
                "name": st.column_config.TextColumn("Resource", pinned=True),
                "path": st.column_config.TextColumn("Path"),
                "use": st.column_config.TextColumn("Use"),
            },
            hide_index=True,
        )
        st.caption(
            f"Base URL: `{catalog['base_url']}` · "
            f"[Docs]({catalog['docs_url']})"
        )

with blocked_tab:
    with st.container(border=True):
        st.subheader("What we will not do")
        st.dataframe(
            pd.DataFrame(catalog["not_allowed"]),
            column_config={
                "action": st.column_config.TextColumn("Blocked", pinned=True),
                "why": st.column_config.TextColumn("Why"),
            },
            hide_index=True,
        )
        st.caption(
            f"[Terms]({catalog['terms_url']}) · "
            f"[Acceptable use]({catalog['acceptable_use_url']})"
        )

with live_tab:
    if not status.get("connected"):
        st.warning(
            "Add `SHOPMONKEY_API_KEY` to `.env`, restart the API, then refresh. "
            "Admin path: Settings → Integration → API Keys."
        )
    else:
        try:
            snapshot = load_shopmonkey("/shopmonkey/snapshot", {"limit": limit})
        except requests.HTTPError as exc:
            detail = (
                exc.response.json().get("detail", exc.response.text)
                if exc.response is not None
                else str(exc)
            )
            st.error(f"Could not load shop data: {detail}")
        except requests.RequestException as exc:
            st.error(f"Could not load shop data: {exc}")
        else:
            with st.container(horizontal=True):
                st.metric("Orders loaded", f"{len(snapshot['orders']):,}", border=True)
                st.metric(
                    "Customers loaded",
                    f"{len(snapshot['customers']):,}",
                    border=True,
                )
                st.metric(
                    "Appointments loaded",
                    f"{len(snapshot['appointments']):,}",
                    border=True,
                )
                st.metric("Users loaded", f"{snapshot['user_count']:,}", border=True)

            order_col, customer_col = st.columns(2)
            with order_col, st.container(border=True):
                st.subheader("Orders")
                if snapshot["orders"]:
                    st.dataframe(pd.DataFrame(snapshot["orders"]), hide_index=True)
                else:
                    st.info("No orders returned.")
            with customer_col, st.container(border=True):
                st.subheader("Customers")
                if snapshot["customers"]:
                    st.dataframe(pd.DataFrame(snapshot["customers"]), hide_index=True)
                else:
                    st.info("No customers returned.")

            with st.container(border=True):
                st.subheader("Appointments")
                if snapshot["appointments"]:
                    st.dataframe(pd.DataFrame(snapshot["appointments"]), hide_index=True)
                else:
                    st.info("No appointments returned.")
