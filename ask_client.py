"""Streamlit client for POST /ask — Step E. Server must be running on port 8000."""

import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"
API_URL = f"{API_BASE}/ask"


def server_is_up() -> bool:
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


st.set_page_config(page_title="Bootcamp Q&A", page_icon="💬", layout="centered")
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
