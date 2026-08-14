"""Home — pick an app from the sidebar."""

import streamlit as st

st.set_page_config(page_title="AI Eng Bootcamp", page_icon="🏠", layout="centered")

st.title("AI Eng Bootcamp")
st.markdown(
    """
Welcome. Use the **sidebar on the left** to switch apps:

1. **Cost Estimator** — model cost math (`POST /estimate`)
2. **Bootcamp Q&A** — ask questions (`POST /ask`)
3. **Shop intelligence** — synthetic Porsche warehouse (no ShopMonkey key)

Both need the API server running in another terminal:
"""
)
st.code("uvicorn server.main:app --reload", language="bash")

st.info("Use the sidebar for **Cost Estimator**, **Bootcamp Q&A**, or **Shop intelligence**.")
