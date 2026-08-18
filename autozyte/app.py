"""AutoZyte — shop operations platform."""

import streamlit as st

st.set_page_config(page_title="AutoZyte", page_icon="🔧", layout="wide")

st.title("AutoZyte")
st.markdown(
    """
Licensed shop operations platform. Use the **sidebar**:

1. **Shop intelligence** — history warehouse, trends, catalog (synthetic Porsche until ingest)
2. **Jake Advisor** — data-based briefing for the service advisor (Powered by FerdAI)

Start the API:
"""
)
st.code("./start.sh", language="bash")
st.caption("Hub: [GTInternational/Projects](https://github.com/GTInternational/Projects)")
