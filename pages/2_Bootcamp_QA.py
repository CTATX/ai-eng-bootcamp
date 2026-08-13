"""Bootcamp Q&A — calls your FastAPI POST /ask endpoint."""

import requests
import streamlit as st

from api_client import API_BASE, server_is_up

API_URL = f"{API_BASE}/ask"


st.title("Bootcamp Q&A")
st.caption("Ask a question — answers come from your FastAPI service.")

if server_is_up():
    st.success("Connected to your API")
else:
    st.warning("Your API is not running. Start it in a separate terminal, then refresh this page.")

with st.sidebar:
    st.header("Setup")
    st.markdown(
        "This page is the **client**. Your FastAPI app is the **server**.\n\n"
        "Keep both running at the same time."
    )
    with st.expander("Server command (Terminal 1)"):
        st.code("uvicorn server.main:app --reload", language="bash")

question = st.text_area("Your question", placeholder="What is RAG?", height=100)

if st.button("Ask", type="primary", use_container_width=True):
    if not question.strip():
        st.warning("Enter a question first.")
    elif not server_is_up():
        st.error("Start the API server first, then try again.")
    else:
        try:
            response = requests.post(
                API_URL,
                json={"question": question.strip()},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            st.subheader("Answer")
            st.write(data["answer"])
            st.caption(f"Confidence: {data['confidence']}")
        except requests.ConnectionError:
            st.error("Lost connection to the API. Check that the server is still running.")
        except requests.HTTPError:
            detail = response.json().get("detail", response.text)
            st.error(f"API error ({response.status_code}): {detail}")
