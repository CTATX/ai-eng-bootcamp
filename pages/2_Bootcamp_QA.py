"""Bootcamp Q&A — calls your FastAPI POST /ask endpoint."""

import requests
import streamlit as st

from api_client import API_BASE, server_is_up

API_URL = f"{API_BASE}/ask"


st.title("Bootcamp Q&A")
st.caption("Ask a question, then review the outcome. Every call is attributed and measured.")

if server_is_up():
    st.success("Connected to your API")
else:
    st.warning("Your API is not running. Start it in a separate terminal, then refresh this page.")

with st.sidebar:
    st.header("Usage attribution")
    user_id = st.text_input("User", value="local-user")
    business_owner_id = st.text_input("Business owner", value="CT")
    use_case = st.text_input("Use case", value="bootcamp-qa")
    environment = st.selectbox("Environment", ["local", "development", "production"])
    st.divider()
    st.header("Setup")
    st.markdown(
        "This page is the **client**. Your FastAPI app is the **server**.\n\n"
        "Keep both running at the same time."
    )
    with st.expander("Server command (Terminal 1)"):
        st.code("uvicorn server.main:app --reload", language="bash")

with st.form("ask_form"):
    question = st.text_area("Your question", placeholder="What is RAG?", height=100)
    ask_clicked = st.form_submit_button("Ask", type="primary", width="stretch")

if ask_clicked:
    if not question.strip():
        st.warning("Enter a question first.")
    elif not server_is_up():
        st.error("Start the API server first, then try again.")
    else:
        try:
            response = requests.post(
                API_URL,
                json={
                    "question": question.strip(),
                    "user_id": user_id,
                    "business_owner_id": business_owner_id,
                    "use_case": use_case,
                    "environment": environment,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            st.session_state["latest_answer"] = data["answer"]
            st.session_state["latest_confidence"] = data["confidence"]
            st.session_state["latest_usage"] = data.get("usage")
            st.session_state.pop("outcome_reviewed", None)
        except requests.ConnectionError:
            st.error("Lost connection to the API. Check that the server is still running.")
        except requests.HTTPError:
            detail = response.json().get("detail", response.text)
            st.error(f"API error ({response.status_code}): {detail}")

if answer := st.session_state.get("latest_answer"):
    st.subheader("Answer")
    st.write(answer)
    st.caption(f"Confidence: {st.session_state['latest_confidence']}")

    usage = st.session_state.get("latest_usage")
    if usage:
        with st.container(border=True):
            st.markdown("**Usage receipt**")
            st.caption(
                f"{usage['model_id']} · "
                f"{usage['input_tokens']:,} input · "
                f"{usage['output_tokens']:,} output · "
                f"${usage['estimated_cost_usd']:.6f} estimated"
            )

        if st.session_state.get("outcome_reviewed"):
            st.success(f"Outcome marked {st.session_state['outcome_reviewed']}.")
        else:
            st.markdown("**Was this output useful enough to accept?**")
            accept_col, reject_col = st.columns(2)
            outcome_status = None
            if accept_col.button("Accept outcome", type="primary", width="stretch"):
                outcome_status = "accepted"
            if reject_col.button("Reject outcome", width="stretch"):
                outcome_status = "rejected"

            if outcome_status:
                review_response = requests.post(
                    f"{API_BASE}/finops/usage/{usage['request_id']}/outcome",
                    json={"outcome_status": outcome_status},
                    timeout=10,
                )
                if review_response.ok:
                    st.session_state["outcome_reviewed"] = outcome_status
                    st.rerun()
                else:
                    st.error("Could not save the outcome review.")
