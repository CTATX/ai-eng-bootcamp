"""API Health — visual heartbeat for the FastAPI server."""

from __future__ import annotations

import requests
import streamlit as st

from api_client import API_BASE, server_is_up

st.title("API Health")
st.caption("Client-side check against your FastAPI server.")

col_status, col_refresh = st.columns([3, 1])
with col_refresh:
    if st.button("Refresh", use_container_width=True):
        st.rerun()

with col_status:
    if server_is_up():
        st.success(f"API is up — `{API_BASE}`")
    else:
        st.error(f"API is down — `{API_BASE}`")
        st.info("Start the server: `./start.sh` in a terminal, then refresh this page.")

st.subheader("Endpoints")
st.markdown(
    f"""
| Check | URL |
|-------|-----|
| Health (JSON) | [{API_BASE}/health]({API_BASE}/health) |
| Swagger docs | [{API_BASE}/docs]({API_BASE}/docs) |
| API menu | [{API_BASE}/]({API_BASE}/) |
"""
)

if server_is_up():
    st.subheader("Live response")
    try:
        health = requests.get(f"{API_BASE}/health", timeout=2)
        st.json(health.json())
    except requests.RequestException as exc:
        st.warning(f"Could not fetch /health: {exc}")

    try:
        root = requests.get(f"{API_BASE}/", timeout=2)
        with st.expander("GET / — service menu"):
            st.json(root.json())
    except requests.RequestException:
        pass

with st.sidebar:
    st.header("Week 1")
    st.markdown(
        "This page is the **client**. It calls `GET /health` — same check as:\n\n"
        f"```bash\ncurl {API_BASE}/health\n```"
    )
    st.markdown("Next: **Bootcamp Q&A** → test `POST /ask` with your OpenAI key.")
