"""AutoZyte — shop operations platform."""

import streamlit as st

st.set_page_config(page_title="AutoZyte", page_icon="🔧", layout="wide")

st.title("AutoZyte")
st.markdown(
    """
Licensed shop operations platform. Use the **sidebar**:

1. **System Status** — API health, warehouse, ingest, ShopMonkey (replaces CLI status; links to `/docs`)
2. **Shop intelligence** — history warehouse, trends, catalog
3. **Jake Advisor** — data-based briefing for the service advisor (Powered by FerdAI)

Start the stack:
"""
)
st.code("./start.sh", language="bash")
st.caption(
    f"API docs (live calls): http://127.0.0.1:8000/docs · "
    "Hub: [BadLabz/Projects](https://github.com/BadLabz/Projects)"
)
