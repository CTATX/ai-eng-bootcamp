"""Streamlit UI for AI workload cost estimation — calls POST /estimate."""

from __future__ import annotations

import requests
import streamlit as st

from api_client import API_BASE, server_is_up

st.set_page_config(page_title="AI Eng Bootcamp", page_icon="📊", layout="centered")

st.title("AI Cost Estimator")
st.caption("Client UI → your FastAPI `/estimate` endpoint → deterministic cost math.")

if server_is_up():
    st.success("Connected to your API")
else:
    st.warning("Your API is not running. Start it in a separate terminal, then refresh.")

with st.sidebar:
    st.header("Assumptions")
    st.markdown(
        "- Token prices from a 5-model catalog\n"
        "- Output size comes from result shape\n"
        "- Retries scale primary + checker steps\n"
        "- Monthly = cost/task × tasks/day × 30"
    )
    with st.expander("Server command (Terminal 1)"):
        st.code("uvicorn server.main:app --reload", language="bash")

result_shapes: list[str] = [
    "Short answer (≈150 tokens)",
    "Paragraph (≈400 tokens)",
    "Report section (≈900 tokens)",
]

col_left, col_right = st.columns(2)

with col_left:
    workload_text = st.text_area(
        "Describe the workload",
        placeholder="Example: Summarize 3-page service invoices and flag warranty risks.",
        height=120,
    )
    input_tokens = st.number_input(
        "Estimated input tokens per task",
        min_value=500,
        max_value=500_000,
        value=4_000,
        step=500,
        help="Rough rule: ~750 tokens per page of text.",
    )

with col_right:
    result_shape = st.selectbox("Expected result size", result_shapes)
    primary_steps = st.slider("Primary model steps per task", 1, 5, 1)
    checker_steps = st.slider("Checker/review steps per task", 0, 3, 1)
    tasks_per_day = st.number_input("Completed tasks per day", min_value=1, max_value=10_000, value=50)

estimate_clicked = st.button("Estimate cost", type="primary", use_container_width=True)

if estimate_clicked:
    if not server_is_up():
        st.error("Start the API server first, then try again.")
    else:
        try:
            response = requests.post(
                f"{API_BASE}/estimate",
                json={
                    "input_tokens": int(input_tokens),
                    "result_shape": result_shape,
                    "primary_steps": int(primary_steps),
                    "checker_steps": int(checker_steps),
                    "tasks_per_day": int(tasks_per_day),
                    "workload_note": workload_text.strip() or None,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            recommendation = data.get("recommendation")
            likely_rows = data.get("likely_comparison", [])
            scenario_ranges = data.get("scenario_ranges", [])

            st.subheader("Recommendation")
            if recommendation is None:
                st.error(
                    "No model in the catalog fits this input size. "
                    "Reduce input tokens or pick a larger-context model."
                )
            else:
                st.success(
                    f"**{recommendation['name']}** ({recommendation['provider']}) — "
                    f"${recommendation['cost_per_task_usd']:.5f} per task · "
                    f"${recommendation['monthly_usd']:,.2f}/month at {tasks_per_day} tasks/day"
                )

            if workload_text.strip():
                st.info(f"Workload note: {workload_text.strip()}")

            st.subheader("Likely-scenario comparison")
            if likely_rows:
                st.dataframe(
                    [
                        {
                            "Model": row["name"],
                            "Provider": row["provider"],
                            "Cost / task (USD)": round(row["cost_per_task_usd"], 6),
                            "Monthly (USD)": round(row["monthly_usd"], 2),
                            "Output tokens": row["output_tokens"],
                            "Attempted calls": round(row["attempted_calls"], 2),
                        }
                        for row in likely_rows
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.warning("No eligible models to compare.")

            with st.expander("Low / likely / high ranges for top pick"):
                if scenario_ranges:
                    st.dataframe(
                        [
                            {
                                "Scenario": row["scenario"],
                                "Cost / task (USD)": round(row["cost_per_task_usd"], 6),
                                "Monthly (USD)": round(row["monthly_usd"], 2),
                            }
                            for row in scenario_ranges
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )
        except requests.ConnectionError:
            st.error("Lost connection to the API. Check that the server is still running.")
        except requests.HTTPError:
            detail = response.json().get("detail", response.text)
            st.error(f"API error ({response.status_code}): {detail}")
else:
    st.info("Enter workload details, then click **Estimate cost**.")
