"""Home — pick an app from the sidebar."""

import streamlit as st

st.set_page_config(page_title="AI Eng Bootcamp", page_icon="🏠", layout="centered")

st.title("AI Eng Bootcamp")
st.markdown(
    """
Welcome. Use the **sidebar on the left** to switch apps:

1. **Cost Estimator** — model cost math (`POST /estimate`)
2. **Bootcamp Q&A** — ask questions (`POST /ask`)

Shop production code lives in **[AutoZyte](https://github.com/GTInternational/autozyte)** (GTInternational).

Start the API:
"""
)
st.code("./start.sh", language="bash")

st.info("Use the sidebar for **Cost Estimator** or **Bootcamp Q&A**.")
