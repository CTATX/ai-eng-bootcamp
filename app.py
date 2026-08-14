"""Home — pick an app from the sidebar."""

import streamlit as st

st.set_page_config(
    page_title="AI Eng Bootcamp",
    page_icon=":material/home:",
    layout="centered",
)

st.title("AI Eng Bootcamp")
st.markdown(
    """
Welcome. Use the **sidebar on the left** to switch apps:

1. **Cost Estimator** — model cost math (`POST /estimate`)
2. **Bootcamp Q&A** — ask questions (`POST /ask`)
3. **AI FinOps** — actual spend, outcomes, attribution, and budget controls
4. **ShopMonkey** — official shop API integration (not a reskin)

Both need the API server running in another terminal:
"""
)
st.code("./start.sh", language="bash")

st.info(
    "Use the sidebar for **Cost Estimator**, **Bootcamp Q&A**, **AI FinOps**, or **ShopMonkey**."
)
