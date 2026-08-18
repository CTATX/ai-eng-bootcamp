"""System status — visual mirror of `python -m shop.cli status` (bootcamp /docs pattern)."""

from __future__ import annotations

import streamlit as st

from api_client import API_BASE, get_json, server_is_up

DOCS_URL = f"{API_BASE}/docs"

STATUS_ENDPOINTS: list[tuple[str, str, str]] = [
    ("GET /health", "/health", "Server alive"),
    ("GET /shop/system/status", "/shop/system/status", "Warehouse + ingest + ShopMonkey (CLI parity)"),
    ("GET /shop/status", "/shop/status", "Warehouse counts only"),
    ("GET /shop/ingest/status", "/shop/ingest/status", "Ingest watermark + last run"),
]

st.set_page_config(page_title="System Status", page_icon="🟢", layout="wide")
st.title("System status")
st.caption(
    "Bootcamp pattern: Streamlit is the **client**; FastAPI is the **server**. "
    "This page replaces repeated `python -m shop.cli status` runs."
)

with st.sidebar:
    st.header("Server")
    st.code("./start.sh", language="bash")
    st.markdown(
        f"- API base: `{API_BASE}`\n"
        f"- Interactive docs: [Open /docs]({DOCS_URL})\n"
        "- CLI equivalent: `python -m shop.cli status`"
    )
    if st.button("Refresh all", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

api_ok = server_is_up()
if api_ok:
    st.success(f"API is running at {API_BASE}")
else:
    st.error("API is not running. Start `./start.sh` in Terminal, then click **Refresh all**.")
    st.stop()

code, health = get_json("/health")
if code == 200 and isinstance(health, dict):
    h1, h2, h3 = st.columns(3)
    h1.metric("Product", health.get("product", "AutoZyte"))
    h2.metric("Version", health.get("version", "—"))
    h3.metric("Health", health.get("status", "—").upper())

st.link_button("Open FastAPI /docs (try calls in the browser)", DOCS_URL, use_container_width=True)
st.caption("Use /docs to execute GET/POST endpoints without curl or CLI — same as bootcamp Step E.")

code, system = get_json("/shop/system/status", timeout=30)
if code != 200 or not isinstance(system, dict):
    st.error(f"Could not load system status ({code}): {system}")
    st.stop()

warehouse = system.get("warehouse", {})
ingest = system.get("ingest", {})
counts = warehouse.get("counts", {})

st.subheader("Warehouse")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Vehicles", f"{counts.get('vehicles', 0):,}")
c2.metric("Orders", f"{counts.get('orders', 0):,}")
c3.metric("ShopMonkey orders", f"{ingest.get('shopmonkey_orders', 0):,}")
c4.metric("Watermark skip", ingest.get("watermark_skip", 0))

if warehouse.get("disclaimer"):
    st.info(warehouse["disclaimer"])

st.subheader("ShopMonkey connection")
key_ok = system.get("shopmonkey_key_configured")
if key_ok:
    st.success("SHOPMONKEY_API_KEY is configured in `.env`")
    if "shopmonkey_auth" in system:
        with st.expander("Live auth check (GET /auth/api_key/status)", expanded=True):
            st.json(system["shopmonkey_auth"])
    elif err := system.get("shopmonkey_auth_error"):
        st.warning(f"Key present but auth failed: {err.get('message', err)}")
else:
    st.warning(
        "No ShopMonkey key — synthetic warehouse only. "
        "Add `SHOPMONKEY_API_KEY` to `.env` when ready."
    )

st.subheader("Ingest")
i1, i2, i3 = st.columns(3)
i1.metric("Last run", ingest.get("last_run") or "—")
i2.metric("Last error", ingest.get("last_error") or "none")
i3.metric("SM orders in DB", ingest.get("shopmonkey_orders", 0))

st.subheader("Try live API calls (no terminal)")
st.caption("Each button calls the running server and shows the JSON response below.")

for label, path, hint in STATUS_ENDPOINTS:
    col_btn, col_hint = st.columns([1, 3])
    with col_btn:
        clicked = st.button(label, key=f"btn-{path}", use_container_width=True)
    with col_hint:
        st.caption(hint)
    if clicked:
        status_code, body = get_json(path, timeout=30)
        if status_code and 200 <= status_code < 300:
            st.success(f"{label} → {status_code}")
            st.json(body)
        else:
            st.error(f"{label} → {status_code or 'connection failed'}")
            st.write(body)

with st.expander("Full system status JSON (same as CLI)"):
    st.json(system)
